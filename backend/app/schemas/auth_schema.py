from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class RegistrationRequest(BaseModel):
    user_email : EmailStr
    user_name : str
    password : str = Field(..., min_length=8, max_length=64) # ... For mandatory
    confirm_password : str = Field(..., min_length=8, max_length=64) 
    birth_date  : date
    about_author : Optional[str] = Field(None, max_length=500) # None for not necessary
    social_link : Optional[str] = None

class RegistrationResponse(BaseModel):
    user_id : int
    message : str

class LoginRequest(BaseModel):
    user_email : EmailStr
    password : str

class LoginResponse(BaseModel):
    user_id : int
    access_token : str
    token_type : str = "Bearer" # Bearer is the default value    

class TokenValidationResponse(BaseModel):
    valid : bool
    user_id : int | None = None

    