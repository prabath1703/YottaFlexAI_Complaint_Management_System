from datetime import datetime, timedelta
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import SLAClock, Complaint, StatusEvent


SLA_HOURS = {
    "P1": 4,
    "P2": 12,
    "P3": 24,
    "P4": 72,
}


def create_sla_clock(db: Session, complaint: Complaint):
    existing = db.query(SLAClock).filter(
        SLAClock.complaint_id == complaint.complaint_id
    ).first()

    if existing:
        return existing

    now = datetime.utcnow()
    hours = SLA_HOURS.get(complaint.priority)

    if hours is None:
        raise HTTPException(status_code=400, detail="Invalid priority")

    clock = SLAClock(
        sla_id=f"SLA-{complaint.complaint_id}",
        complaint_id=complaint.complaint_id,
        priority=complaint.priority,
        start_time=now,
        sla_hours=hours,
        sla_deadline=now + timedelta(hours=hours),
        paused_duration_minutes=0,
        elapsed_duration_minutes=0,
        sla_status="OPEN",
    )

    db.add(clock)
    db.commit()
    db.refresh(clock)

    return clock


def get_clock(db: Session, complaint_id: str):
    clock = db.query(SLAClock).filter(
        SLAClock.complaint_id == complaint_id
    ).first()

    if not clock:
        raise HTTPException(status_code=404, detail="SLA clock not found")

    return clock


def record_sla_event(db, complaint_id, event_type, performed_by):
    event = StatusEvent(
        event_id=f"EVT-{secrets.token_hex(8).upper()}",
        complaint_id=complaint_id,
        event_type=event_type,
        from_status=None,
        to_status=None,
        event_time=datetime.utcnow(),
        performed_by=performed_by,
    )
    db.add(event)


def pause_sla(
    db: Session,
    complaint_id: str,
    performed_by: str = "SYSTEM",
):
    clock = get_clock(db, complaint_id)

    if clock.sla_status == "PAUSED":
        raise HTTPException(status_code=400, detail="SLA is already paused")

    if clock.sla_status in ("BREACHED", "COMPLETED"):
        raise HTTPException(
            status_code=400,
            detail="Cannot pause a breached or completed SLA",
        )

    now = datetime.utcnow()

    clock.paused_at = now
    clock.sla_status = "PAUSED"

    record_sla_event(db, complaint_id, "SLA_PAUSED", performed_by)

    db.commit()
    db.refresh(clock)

    return clock


def resume_sla(
    db: Session,
    complaint_id: str,
    performed_by: str = "SYSTEM",
):
    clock = get_clock(db, complaint_id)

    if clock.sla_status != "PAUSED" or not clock.paused_at:
        raise HTTPException(status_code=400, detail="SLA is not paused")

    now = datetime.utcnow()
    pause_minutes = int((now - clock.paused_at).total_seconds() / 60)

    clock.paused_duration_minutes = (
        (clock.paused_duration_minutes or 0) + pause_minutes
    )

    # Extend the deadline by the exact pause duration.
    clock.sla_deadline += timedelta(minutes=pause_minutes)

    clock.paused_at = None
    clock.sla_status = "OPEN"

    record_sla_event(db, complaint_id, "SLA_RESUMED", performed_by)

    db.commit()
    db.refresh(clock)

    return clock


def evaluate_sla(db: Session, clock: SLAClock):
    now = datetime.utcnow()

    # Never evaluate a resolved or closed complaint as an active SLA.
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == clock.complaint_id
    ).first()

    if complaint and complaint.status in ("RESOLVED", "CLOSED"):
        return clock

    if clock.sla_status in ("COMPLETED", "BREACHED"):
        return clock

    if clock.sla_status == "PAUSED":
        elapsed_end = clock.paused_at
    else:
        elapsed_end = now

    elapsed = max(
        0,
        int((elapsed_end - clock.start_time).total_seconds() / 60)
        - (clock.paused_duration_minutes or 0),
    )

    clock.elapsed_duration_minutes = elapsed

    if now >= clock.sla_deadline:
        clock.sla_status = "BREACHED"

        if clock.breached_at is None:
            clock.breached_at = now

            record_sla_event(
                db,
                clock.complaint_id,
                "SLA_BREACHED",
                "SYSTEM",
            )

    else:
        clock.sla_status = "OPEN"

    return clock


def complete_sla(db: Session, complaint_id: str):
    clock = get_clock(db, complaint_id)

    if clock.sla_status == "PAUSED":
        raise HTTPException(
            status_code=400,
            detail="Resume SLA before completing it",
        )

    clock.sla_status = "COMPLETED"

    record_sla_event(
        db,
        complaint_id,
        "SLA_COMPLETED",
        "SYSTEM",
    )

    db.commit()
    db.refresh(clock)

    return clock