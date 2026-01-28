from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class UserBase(BaseModel):
    user_id: int
    user_email: EmailStr
    user_name: str
    birth_date: Optional[date]
    bio: Optional[str]
    social_link: Optional[str]
    user_role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    user_id: int
    user_name: str
    bio: Optional[str]
    social_link: Optional[str]

    class Config:
        from_attributes = True


class UserPreferredTagRequest(BaseModel):
    tag_ids: list[int]
