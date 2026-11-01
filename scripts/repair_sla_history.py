import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from app.db.database import SessionLocal
from app.models import Complaint, SLAClock, StatusEvent


DB_FILE = Path("data/complaint_management.db")
BACKUP_FILE = Path("data/complaint_management_before_sla_repair.db")


def main():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    # Preserve the original database before changing anything.
    shutil.copy2(DB_FILE, BACKUP_FILE)
    print(f"Backup created: {BACKUP_FILE}")

    db = SessionLocal()

    completed = 0
    breached = 0
    skipped = 0

    try:
        clocks = db.query(SLAClock).all()

        for clock in clocks:
            complaint = db.query(Complaint).filter(
                Complaint.complaint_id == clock.complaint_id
            ).first()

            if not complaint:
                skipped += 1
                continue

            if complaint.status not in ("RESOLVED", "CLOSED"):
                continue

            # Use the actual lifecycle event, not today's date.
            resolution_event = (
                db.query(StatusEvent)
                .filter(
                    StatusEvent.complaint_id == complaint.complaint_id,
                    StatusEvent.to_status == "RESOLVED",
                )
                .order_by(StatusEvent.event_time.asc())
                .first()
            )

            # If no RESOLVED event exists, use the CLOSED event.
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

            if not resolution_time or resolution_time < clock.start_time:
                skipped += 1
                continue

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
                # Complaint met its SLA.
                clock.sla_status = "COMPLETED"
                clock.breached_at = None
                completed += 1

                # Remove false breach events generated after resolution.
                for event in breach_events:
                    if event.event_time > resolution_time:
                        db.delete(event)

            else:
                # Complaint genuinely exceeded its SLA.
                clock.sla_status = "BREACHED"
                clock.breached_at = resolution_time
                breached += 1

                if breach_events:
                    # Correct the timestamp of the existing breach event.
                    breach_events[0].event_time = resolution_time

                    # Remove duplicate breach events.
                    for event in breach_events[1:]:
                        db.delete(event)
                else:
                    db.add(
                        StatusEvent(
                            event_id=f"EVT-{uuid4().hex[:16].upper()}",
                            complaint_id=complaint.complaint_id,
                            event_type="SLA_BREACHED",
                            from_status=None,
                            to_status=None,
                            event_time=resolution_time,
                            performed_by="SYSTEM",
                        )
                    )

        db.commit()

        print("\n--- SLA REPAIR SUMMARY ---")
        print("Total SLA clocks:", len(clocks))
        print("Completed within SLA:", completed)
        print("Genuinely breached:", breached)
        print("Skipped:", skipped)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()