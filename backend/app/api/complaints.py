import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import (
    Complaint,
    Customer,
    Order,
    Product,
    Category,
    StatusEvent,
)
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
)

from app.services.assignment_service import assign_complaint
from app.services.sla_service import create_sla_clock

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


def generate_complaint_id(db: Session) -> str:
    year = datetime.now().year

    for _ in range(100):
        number = secrets.randbelow(900000) + 100000
        complaint_id = f"CMP-{year}-{number}"

        exists = db.query(Complaint).filter(
            Complaint.complaint_id == complaint_id
        ).first()

        if not exists:
            return complaint_id

    raise HTTPException(
        status_code=500,
        detail="Could not generate a unique complaint ID",
    )


@router.get("/", response_model=list[ComplaintResponse])
def get_complaints(
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(term))
            | (Complaint.description.ilike(term))
            | (Complaint.customer_id.ilike(term))
        )

    if status:
        query = query.filter(Complaint.status == status)

    if priority:
        query = query.filter(Complaint.priority == priority)

    if category:
        query = query.filter(Complaint.category == category)

    return (
        query.order_by(Complaint.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


@router.post("/", response_model=ComplaintResponse, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
):
    if not db.query(Customer).filter(
        Customer.customer_id == payload.customer_id
    ).first():
        raise HTTPException(status_code=400, detail="Customer not found")

    if payload.order_id and not db.query(Order).filter(
        Order.order_id == payload.order_id
    ).first():
        raise HTTPException(status_code=400, detail="Order not found")

    if payload.product_id and not db.query(Product).filter(
        Product.product_id == payload.product_id
    ).first():
        raise HTTPException(status_code=400, detail="Product not found")

    if not db.query(Category).filter(
        Category.category_id == payload.category_id
    ).first():
        raise HTTPException(status_code=400, detail="Category not found")

    complaint_id = generate_complaint_id(db)
    now = datetime.utcnow()

    complaint = Complaint(
        complaint_id=complaint_id,
        customer_id=payload.customer_id,
        source_customer_id=payload.customer_id,
        order_id=payload.order_id,
        product_id=payload.product_id,
        channel=payload.channel,
        created_at=now,
        description=payload.description,
        category_id=payload.category_id,
        category=payload.category,
        severity=payload.severity,
        sentiment=payload.sentiment,
        repeat_complaint_flag=payload.repeat_complaint_flag,
        related_complaint_id=payload.related_complaint_id,
        safety_issue_flag=payload.safety_issue_flag,
        priority=payload.priority,
        status=payload.status,
    )

    event = StatusEvent(
        event_id=f"EVT-{secrets.token_hex(8).upper()}",
        complaint_id=complaint_id,
        event_type="COMPLAINT_CREATED",
        from_status=None,
        to_status=payload.status,
        event_time=now,
        performed_by="system",
    )

    db.add(complaint)
    db.add(event)
    db.commit()
    db.refresh(complaint)

    # Automatically assign the complaint.
    assign_complaint(
        db=db,
        complaint_id=complaint_id,
        assigned_by="SYSTEM",
    )

    # Automatically start the SLA clock.
    create_sla_clock(
        db=db,
        complaint=complaint,
    )

    db.refresh(complaint)

    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: str,
    payload: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = complaint.status.upper()
    new_status = payload.status.strip().upper()

    if old_status == new_status:
        return complaint

    # Prevent changes to permanently closed complaints.
    if old_status == "CLOSED":
        raise HTTPException(
            status_code=400,
            detail="Closed complaints cannot be modified."
        )

    # A complaint must be resolved before it can be closed.
    if new_status == "CLOSED" and old_status != "RESOLVED":
        raise HTTPException(
            status_code=400,
            detail="A complaint must be RESOLVED before it can be CLOSED."
        )

    # A complaint must be in progress before resolution.
    if new_status == "RESOLVED" and old_status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS complaints can be marked RESOLVED."
        )

    complaint.status = new_status

    event = StatusEvent(
        event_id=f"EVT-{secrets.token_hex(8).upper()}",
        complaint_id=complaint_id,
        event_type="STATUS_CHANGED",
        from_status=old_status,
        to_status=new_status,
        event_time=datetime.utcnow(),
        performed_by=payload.performed_by,
    )

    db.add(event)
    db.commit()
    db.refresh(complaint)

    return complaint


@router.get("/{complaint_id}/history")
def get_complaint_history(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    events = (
        db.query(StatusEvent)
        .filter(StatusEvent.complaint_id == complaint_id)
        .order_by(StatusEvent.event_time.asc())
        .all()
    )

    return events