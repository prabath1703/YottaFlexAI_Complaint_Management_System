from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import SLAClock, Complaint
from app.schemas.sla import SLActionRequest
from app.services.sla_service import (
    get_clock,
    pause_sla,
    resume_sla,
    evaluate_sla,
    complete_sla,
)

router = APIRouter(prefix="/api/sla", tags=["SLA Monitoring"])


def serialize_sla_clock(clock):
    """Convert an SQLAlchemy SLAClock into a JSON-safe dictionary."""
    return {
        "sla_id": clock.sla_id,
        "complaint_id": clock.complaint_id,
        "priority": clock.priority,
        "start_time": clock.start_time,
        "sla_hours": clock.sla_hours,
        "sla_deadline": clock.sla_deadline,
        "paused_duration_minutes": clock.paused_duration_minutes,
        "elapsed_duration_minutes": clock.elapsed_duration_minutes,
        "sla_status": clock.sla_status,
        "paused_at": clock.paused_at,
        "breached_at": clock.breached_at,
    }


@router.get("/")
def get_all_sla_clocks(db: Session = Depends(get_db)):
    clocks = db.query(SLAClock).all()

    result = []

    for clock in clocks:
        evaluate_sla(db, clock)
        result.append(serialize_sla_clock(clock))

    db.commit()

    return result


@router.get("/{complaint_id}")
def get_sla(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    clock = get_clock(db, complaint_id)

    evaluate_sla(db, clock)
    db.commit()
    db.refresh(clock)

    return serialize_sla_clock(clock)


@router.post("/{complaint_id}/pause")
def pause_complaint_sla(
    complaint_id: str,
    payload: SLActionRequest,
    db: Session = Depends(get_db),
):
    clock = pause_sla(db, complaint_id, payload.performed_by)
    return serialize_sla_clock(clock)


@router.post("/{complaint_id}/resume")
def resume_complaint_sla(
    complaint_id: str,
    payload: SLActionRequest,
    db: Session = Depends(get_db),
):
    clock = resume_sla(db, complaint_id, payload.performed_by)
    return serialize_sla_clock(clock)


@router.post("/{complaint_id}/complete")
def complete_complaint_sla(
    complaint_id: str,
    payload: SLActionRequest,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.status not in ("RESOLVED", "CLOSED"):
        raise HTTPException(
            status_code=400,
            detail="Resolve or close the complaint before completing its SLA",
        )

    clock = complete_sla(db, complaint_id)
    return serialize_sla_clock(clock)
