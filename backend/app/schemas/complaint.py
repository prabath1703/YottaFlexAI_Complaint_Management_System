from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    customer_id: str
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    channel: str
    description: str = Field(min_length=5)
    category_id: str
    category: str
    severity: str
    sentiment: Optional[str] = None
    repeat_complaint_flag: bool = False
    related_complaint_id: Optional[str] = None
    safety_issue_flag: bool = False
    priority: str
    status: str = "OPEN"


class ComplaintStatusUpdate(BaseModel):
    status: str
    performed_by: str = "system"


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    channel: Optional[str] = None
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    sentiment: Optional[str] = None
    repeat_complaint_flag: Optional[bool] = None
    related_complaint_id: Optional[str] = None
    safety_issue_flag: Optional[bool] = None
    priority: Optional[str] = None
    status: Optional[str] = None