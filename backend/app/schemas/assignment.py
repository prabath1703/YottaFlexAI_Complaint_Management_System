from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssignmentRequest(BaseModel):
    assigned_by: str = "SYSTEM"
    team: Optional[str] = None
    agent_id: Optional[str] = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: str
    complaint_id: str
    team: str
    agent_id: str
    assigned_at: Optional[str] = None
    unassigned_at: Optional[str] = None
    assignment_reason: Optional[str] = None