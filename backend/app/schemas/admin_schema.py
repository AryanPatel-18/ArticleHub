from pydantic import BaseModel, Field
from datetime import datetime


class AdminActionResponse(BaseModel):
    id: int
    admin_user_id: int | None

    action_type: str
    target_type: str
    target_id: int

    target_snapshot: str | None
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminDeleteRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
