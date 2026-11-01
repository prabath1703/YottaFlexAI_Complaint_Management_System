
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import (
    Complaint,
    Resolution,
    StatusEvent,
    ComplaintMessage,
    SLAClock,
)
from app.schemas.resolution import ResolutionCreate


router = APIRouter(prefix="/api/resolutions", tags=["Resolutions"])


class ApprovalDecision(BaseModel):
    performed_by: str = Field(min_length=1)


class RejectionDecision(BaseModel):
    performed_by: str = Field(min_length=1)
    reason: str = Field(min_length=3)


def get_complaint_and_latest_resolution(db: Session, complaint_id: str):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    resolution = (
        db.query(Resolution)
        .filter(Resolution.complaint_id == complaint_id)
        .order_by(Resolution.resolved_at.desc())
        .first()
    )

    if not resolution:
        raise HTTPException(
            status_code=404,
            detail="No resolution found for this complaint",
        )

    return complaint, resolution


def check_pending_resolution(db: Session, resolution: Resolution):
    decision = (
        db.query(StatusEvent)
        .filter(
            StatusEvent.complaint_id == resolution.complaint_id,
            StatusEvent.event_type.in_([
                "RESOLUTION_APPROVED",
                "RESOLUTION_REJECTED",
            ]),
            StatusEvent.event_time >= resolution.resolved_at,
        )
        .order_by(StatusEvent.event_time.desc())
        .first()
    )

    if decision:
        raise HTTPException(
            status_code=400,
            detail="This resolution has already received a decision.",
        )


def finalize_sla_on_resolution(
    db: Session,
    complaint_id: str,
    completed_at: datetime,
    performed_by: str,
):
    """
    Finalize the SLA when a resolution is approved.

    COMPLETED means the complaint was resolved within its allowed SLA time.
    BREACHED means the allowed SLA time was exceeded.
    Existing terminal SLA states are preserved.
    """

    clock = (
        db.query(SLAClock)
        .filter(SLAClock.complaint_id == complaint_id)
        .first()
    )

    # No SLA clock exists for this complaint.
    if not clock:
        return None

    # Never overwrite an existing terminal SLA result.
    if clock.sla_status in ("COMPLETED", "BREACHED"):
        return clock.sla_status

    previous_paused_minutes = clock.paused_duration_minutes or 0

    # If the SLA is currently paused, include the current pause duration.
    if clock.paused_at:
        current_pause_minutes = max(
            0,
            int((completed_at - clock.paused_at).total_seconds() / 60),
        )

        total_paused_minutes = (
            previous_paused_minutes + current_pause_minutes
        )

        elapsed_end = clock.paused_at
    else:
        total_paused_minutes = previous_paused_minutes
        elapsed_end = completed_at

    elapsed_minutes = max(
        0,
        int((elapsed_end - clock.start_time).total_seconds() / 60)
        - previous_paused_minutes,
    )

    clock.paused_duration_minutes = total_paused_minutes
    clock.elapsed_duration_minutes = elapsed_minutes
    clock.paused_at = None

    allowed_minutes = clock.sla_hours * 60

    if elapsed_minutes <= allowed_minutes:
        clock.sla_status = "COMPLETED"
        event_type = "SLA_COMPLETED"
    else:
        clock.sla_status = "BREACHED"
        event_type = "SLA_BREACHED"

        if clock.breached_at is None:
            clock.breached_at = completed_at

    # Avoid creating duplicate SLA terminal events.
    existing_event = (
        db.query(StatusEvent)
        .filter(
            StatusEvent.complaint_id == complaint_id,
            StatusEvent.event_type == event_type,
        )
        .first()
    )

    if not existing_event:
        db.add(
            StatusEvent(
                event_id=f"EVT-{uuid4().hex[:16].upper()}",
                complaint_id=complaint_id,
                event_type=event_type,
                from_status=None,
                to_status=None,
                event_time=completed_at,
                performed_by=performed_by,
            )
        )

    return clock.sla_status


@router.get("/complaint/{complaint_id}")
def get_resolution(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return (
        db.query(Resolution)
        .filter(Resolution.complaint_id == complaint_id)
        .order_by(Resolution.resolved_at.desc())
        .all()
    )


@router.post("/complaint/{complaint_id}")
def create_resolution(
    complaint_id: str,
    payload: ResolutionCreate,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS complaints can receive a resolution proposal.",
        )

    resolution_type = payload.resolution_type.strip()
    resolution_description = payload.resolution_description.strip()
    resolved_by = payload.resolved_by.strip()

    if not resolution_type or not resolution_description or not resolved_by:
        raise HTTPException(
            status_code=400,
            detail="Resolution type, description and resolved_by are required.",
        )

    resolution = Resolution(
        resolution_id=f"RES-{uuid4().hex[:12].upper()}",
        complaint_id=complaint_id,
        resolution_type=resolution_type,
        resolution_description=resolution_description,
        resolved_at=datetime.utcnow(),
        resolved_by=resolved_by,
        refund_amount=payload.refund_amount,
    )

    event = StatusEvent(
        event_id=f"EVT-{uuid4().hex[:16].upper()}",
        complaint_id=complaint_id,
        event_type="RESOLUTION_PROPOSED",
        from_status=complaint.status,
        to_status=complaint.status,
        event_time=datetime.utcnow(),
        performed_by=resolved_by,
    )

    try:
        db.add(resolution)
        db.add(event)
        db.commit()
        db.refresh(resolution)
        return resolution

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save resolution proposal.",
        )


@router.post("/complaint/{complaint_id}/approve")
def approve_resolution(
    complaint_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
):
    complaint, resolution = get_complaint_and_latest_resolution(
        db, complaint_id
    )

    if complaint.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS complaints can have resolutions approved.",
        )

    check_pending_resolution(db, resolution)

    performed_by = payload.performed_by.strip()

    if not performed_by:
        raise HTTPException(
            status_code=400,
            detail="Approver name is required.",
        )

    old_status = complaint.status
    now = datetime.utcnow()

    complaint.status = "RESOLVED"

    event = StatusEvent(
        event_id=f"EVT-{uuid4().hex[:16].upper()}",
        complaint_id=complaint_id,
        event_type="RESOLUTION_APPROVED",
        from_status=old_status,
        to_status="RESOLVED",
        event_time=now,
        performed_by=performed_by,
    )

    try:
        db.add(event)

        # Automatically finalize the SLA when the resolution is approved.
        sla_status = finalize_sla_on_resolution(
            db=db,
            complaint_id=complaint_id,
            completed_at=now,
            performed_by=performed_by,
        )

        db.commit()
        db.refresh(complaint)

        return {
            "message": "Resolution approved successfully",
            "complaint_id": complaint_id,
            "resolution_id": resolution.resolution_id,
            "status": complaint.status,
            "approved_by": performed_by,
            "sla_status": sla_status,
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to approve resolution.",
        )


@router.post("/complaint/{complaint_id}/reject")
def reject_resolution(
    complaint_id: str,
    payload: RejectionDecision,
    db: Session = Depends(get_db),
):
    complaint, resolution = get_complaint_and_latest_resolution(
        db, complaint_id
    )

    if complaint.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS complaints can have resolutions rejected.",
        )

    check_pending_resolution(db, resolution)

    performed_by = payload.performed_by.strip()
    reason = payload.reason.strip()

    if not performed_by or len(reason) < 3:
        raise HTTPException(
            status_code=400,
            detail="Approver name and a rejection reason of at least 3 characters are required.",
        )

    now = datetime.utcnow()

    event = StatusEvent(
        event_id=f"EVT-{uuid4().hex[:16].upper()}",
        complaint_id=complaint_id,
        event_type="RESOLUTION_REJECTED",
        from_status=complaint.status,
        to_status=complaint.status,
        event_time=now,
        performed_by=performed_by,
    )

    rejection_message = ComplaintMessage(
        message_id=f"MSG-{uuid4().hex[:12].upper()}",
        complaint_id=complaint_id,
        sender_type="APPROVER",
        message_time=now,
        message_text=f"Resolution rejected. Reason: {reason}",
        channel="INTERNAL",
    )

    try:
        db.add(event)
        db.add(rejection_message)
        db.commit()

        return {
            "message": "Resolution rejected",
            "complaint_id": complaint_id,
            "resolution_id": resolution.resolution_id,
            "status": complaint.status,
            "rejected_by": performed_by,
            "reason": reason,
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to reject resolution.",
        )
