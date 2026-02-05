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

class UserProfileResponse(BaseModel):
    user_id: int
    user_email: str
    user_name: str
    birth_date: date | None
    bio: str | None
    user_role: str
    social_link: str | None
    created_at: datetime

class UserProfileUpdateRequest(BaseModel):
    user_name: str | None = None
    email : str | None = None
    birth_date: date | None = None
    bio: str | None = None
    social_link: str | None = None

class PasswordChangeRequest(BaseModel):
    old_password: str 
    new_password: str
    confirm_new_password : str

class PasswordChangeResponse(BaseModel):
    message: str
