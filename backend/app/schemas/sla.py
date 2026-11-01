from pydantic import BaseModel


class SLActionRequest(BaseModel):
    performed_by: str = "SYSTEM"