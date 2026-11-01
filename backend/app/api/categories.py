
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import Category

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    return (
        db.query(Category)
        .order_by(Category.category_id)
        .all()
    )


@router.get("/{category_id}")
def get_category(category_id: str, db: Session = Depends(get_db)):
    category = (
        db.query(Category)
        .filter(Category.category_id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category
