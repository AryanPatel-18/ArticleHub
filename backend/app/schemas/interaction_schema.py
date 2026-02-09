from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

# This schema defines the data schemas for user interactions with articles, including creating interactions (views, likes, saves), responses for interaction creation, checking interaction status, and toggling interactions. These schemas ensure that the data sent to and received from the API regarding user interactions is structured and validated properly.


class UserInteractionCreateRequest(BaseModel):
    article_id: int
    interaction_type: str = Field(..., pattern="^(view|like|save)$")


class UserInteractionResponse(BaseModel):
    interaction_id: int
    user_id: int
    article_id: int
    interaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class InteractionStatusResponse(BaseModel):
    liked: bool
    saved: bool
    
class InteractionToggleRequest(BaseModel):
    article_id: int
    interaction_type: Literal["like", "save"]    


class InteractionToggleResponse(BaseModel):
    interaction_type: str
    active: bool
    new_count: int | None = None
