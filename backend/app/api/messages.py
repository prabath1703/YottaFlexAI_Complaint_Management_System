
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import Complaint, ComplaintMessage
from app.schemas.message import MessageCreate, MessageResponse


router = APIRouter(prefix="/api/messages", tags=["Messages"])


ALLOWED_SENDERS = {
    "CUSTOMER",
    "AGENT",
    "SYSTEM",
    "APPROVER",
    "OPERATIONS",
}

ALLOWED_CHANNELS = {
    "WEB",
    "EMAIL",
    "PHONE",
    "CHAT",
    "INTERNAL",
}


def get_complaint_or_404(complaint_id: str, db: Session):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return complaint


@router.get(
    "/complaint/{complaint_id}",
    response_model=list[MessageResponse],
)
def get_messages(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    get_complaint_or_404(complaint_id, db)

    return (
        db.query(ComplaintMessage)
        .filter(ComplaintMessage.complaint_id == complaint_id)
        .order_by(ComplaintMessage.message_time.asc())
        .all()
    )


@router.post(
    "/complaint/{complaint_id}",
    response_model=MessageResponse,
    status_code=201,
)
def add_message(
    complaint_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
):
    get_complaint_or_404(complaint_id, db)

    sender_type = payload.sender_type.strip().upper()
    channel = payload.channel.strip().upper()
    message_text = payload.message_text.strip()

    if sender_type not in ALLOWED_SENDERS:
        raise HTTPException(
            status_code=400,
            detail="Invalid sender type.",
        )

    if channel not in ALLOWED_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail="Invalid communication channel.",
        )

    if not message_text:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    message = ComplaintMessage(
        message_id=f"MSG-{uuid4().hex[:12].upper()}",
        complaint_id=complaint_id,
        sender_type=sender_type,
        message_time=datetime.utcnow(),
        message_text=message_text,
        channel=channel,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message
