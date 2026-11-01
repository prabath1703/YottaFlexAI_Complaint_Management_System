from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ResolutionCreate(BaseModel):
    resolution_type: str
    resolution_description: str
    resolved_by: str
    refund_amount: Optional[float] = 0


class ResolutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resolution_id: str
    complaint_id: str
    resolution_type: str
    resolution_description: str
    resolved_at: datetime
    resolved_by: str
    refund_amount: Optional[float] = None