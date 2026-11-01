from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Customer

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("/")
def get_customers(
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Customer)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (Customer.customer_id.ilike(term))
            | (Customer.name.ilike(term))
            | (Customer.email.ilike(term))
        )

    return (
        query.order_by(Customer.customer_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()

    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer