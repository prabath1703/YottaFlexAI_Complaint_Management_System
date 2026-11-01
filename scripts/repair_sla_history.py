
import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from app.db.database import SessionLocal
from app.models import Complaint, SLAClock, StatusEvent


DB_FILE = Path("data/complaint_management.db")


def main():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    # Create a unique backup without overwriting earlier backups.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = DB_FILE.with_name(
        f"complaint_management_before_sla_repair_{timestamp}.db"
    )
    shutil.copy2(DB_FILE, backup_file)
    print(f"Backup created: {backup_file}")

    db = SessionLocal()

    completed = 0
    breached = 0
    skipped = 0

    try:
        clocks = db.query(SLAClock).all()

        for clock in clocks:
            complaint = (
                db.query(Complaint)
                .filter(
                    Complaint.complaint_id == clock.complaint_id
                )
                .first()
            )

            if not complaint:
                skipped += 1
                continue

            # Only repair complaints that are already resolved or closed.
            if complaint.status not in ("RESOLVED", "CLOSED"):
                continue

            # Find the first historical resolution event.
            resolution_event = (
                db.query(StatusEvent)
                .filter(
                    StatusEvent.complaint_id == complaint.complaint_id,
                    StatusEvent.to_status == "RESOLVED",
                )
                .order_by(StatusEvent.event_time.asc())
                .first()
            )

            # Fall back to CLOSED if no RESOLVED event exists.
            if not resolution_event:
                resolution_event = (
                    db.query(StatusEvent)
                    .filter(
                        StatusEvent.complaint_id == complaint.complaint_id,
                        StatusEvent.to_status == "CLOSED",
                    )
                    .order_by(StatusEvent.event_time.asc())
                    .first()
                )

            if not resolution_event:
                skipped += 1
                continue

            resolution_time = resolution_event.event_time

            if (
                not resolution_time
                or not clock.start_time
                or not clock.sla_deadline
                or resolution_time < clock.start_time
            ):
                skipped += 1
                continue

            # Calculate actual elapsed time, excluding paused duration.
            elapsed = max(
                0,
                int(
                    (resolution_time - clock.start_time).total_seconds()
                    / 60
                ) - (clock.paused_duration_minutes or 0),
            )

            clock.elapsed_duration_minutes = elapsed

            breach_events = (
                db.query(StatusEvent)
                .filter(
                    StatusEvent.complaint_id == complaint.complaint_id,
                    StatusEvent.event_type == "SLA_BREACHED",
                )
                .order_by(StatusEvent.event_time.asc())
                .all()
            )

            if resolution_time <= clock.sla_deadline:
                # Resolved within the SLA deadline.
                clock.sla_status = "COMPLETED"
                clock.breached_at = None
                completed += 1

                # A complaint completed within SLA must not retain
                # an SLA breach event.
                for event in breach_events:
                    db.delete(event)

            else:
                # Resolved after the SLA deadline.
                clock.sla_status = "BREACHED"

                # Preserve the original breach event timestamp.
                # If no event exists, use the SLA deadline.
                if breach_events:
                    clock.breached_at = breach_events[0].event_time

                    # Remove duplicate breach events.
                    for event in breach_events[1:]:
                        db.delete(event)
                else:
                    clock.breached_at = clock.sla_deadline

                    db.add(
                        StatusEvent(
                            event_id=f"EVT-{uuid4().hex[:16].upper()}",
                            complaint_id=complaint.complaint_id,
                            event_type="SLA_BREACHED",
                            from_status=None,
                            to_status=None,
                            event_time=clock.sla_deadline,
                            performed_by="SYSTEM",
                        )
                    )

                breached += 1

        db.commit()

        print("\n--- SLA REPAIR SUMMARY ---")
        print("Total SLA clocks:", len(clocks))
        print("Completed within SLA:", completed)
        print("Genuinely breached:", breached)
        print("Skipped:", skipped)
        print("Backup:", backup_file)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
