from app.db.database import SessionLocal
from app.models import Complaint, SLAClock, StatusEvent, Resolution

db = SessionLocal()

try:
    print("\n--- SAMPLE CLOSED COMPLAINTS ---")

    rows = (
        db.query(Complaint, SLAClock)
        .join(SLAClock, Complaint.complaint_id == SLAClock.complaint_id)
        .filter(Complaint.status == "CLOSED")
        .limit(5)
        .all()
    )

    for complaint, clock in rows:
        print({
            "complaint_id": complaint.complaint_id,
            "created_at": complaint.created_at,
            "status": complaint.status,
            "sla_start": clock.start_time,
            "sla_deadline": clock.sla_deadline,
            "sla_status": clock.sla_status,
        })

        events = (
            db.query(StatusEvent)
            .filter(StatusEvent.complaint_id == complaint.complaint_id)
            .order_by(StatusEvent.event_time.asc())
            .all()
        )

        print("Events:", [
            (e.event_type, e.event_time, e.from_status, e.to_status)
            for e in events
        ])

        resolutions = (
            db.query(Resolution)
            .filter(Resolution.complaint_id == complaint.complaint_id)
            .all()
        )

        print("Resolutions:", [
            (r.resolution_id, r.resolved_at)
            for r in resolutions
        ])

        print("-" * 50)

    print("\n--- RESOLUTION RECORD COUNT ---")
    print(db.query(Resolution).count())

    print("\n--- STATUS EVENT COUNT ---")
    print(db.query(StatusEvent).count())

finally:
    db.close()