from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    sender_type: str
    message_text: str
    channel: str = "WEB"


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    complaint_id: str
    sender_type: str
    message_time: datetime
    message_text: str
    channel: str