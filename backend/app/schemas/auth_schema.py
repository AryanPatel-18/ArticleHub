from pydantic import BaseModel, EmailStr, Field,model_validator,field_validator
from typing import Optional
from datetime import date

# This schema defines the data schemas for user authentication and registration, including the request and response models for user registration, login, and token validation. It ensures that the data sent to and received from the authentication endpoints is structured and validated properly.


class RegistrationRequest(BaseModel):
    user_email: EmailStr
    user_name: str
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)
    birth_date: date
    bio: Optional[str] = Field(None, max_length=500)
    social_link: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self):
        # Password match validation
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        # Empty username validation
        if not self.user_name.strip():
            raise ValueError("Username cannot be empty")

        # Future birth date validation
        if self.birth_date > date.today():
            raise ValueError("Birth date cannot be in the future")

        # Social link length validation
        if self.social_link and len(self.social_link) > 255:
            raise ValueError("Social link too long")

        return self


class RegistrationResponse(BaseModel):
    user_id : int
    message : str

class LoginRequest(BaseModel):
    user_email : EmailStr
    password : str
    
    @field_validator("user_email")
    @classmethod
    def normalize_email(cls, v):
        return v.lower()

class LoginResponse(BaseModel):
    user_id : int
    access_token : str
    token_type : str = "Bearer" # Bearer is the default value    

class TokenValidationResponse(BaseModel):
    valid : bool
    user_id : int | None = None

