from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Assignment, Complaint
from app.schemas.assignment import AssignmentRequest
from app.services.assignment_service import assign_complaint

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


@router.get("/")
def get_assignments(db: Session = Depends(get_db)):
    return (
        db.query(Assignment)
        .order_by(Assignment.assigned_at.desc())
        .limit(500)
        .all()
    )


@router.get("/{complaint_id}")
def get_complaint_assignments(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return (
        db.query(Assignment)
        .filter(Assignment.complaint_id == complaint_id)
        .order_by(Assignment.assigned_at.asc())
        .all()
    )


@router.post("/{complaint_id}/assign")
def assign_or_reassign(
    complaint_id: str,
    payload: AssignmentRequest,
    db: Session = Depends(get_db),
):
    return assign_complaint(
        db=db,
        complaint_id=complaint_id,
        assigned_by=payload.assigned_by,
        requested_team=payload.team,
        requested_agent=payload.agent_id,
    )