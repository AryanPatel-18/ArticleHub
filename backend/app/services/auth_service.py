from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user_model import User
from sqlalchemy import or_
from core.security import hash_password
from schemas.auth_schema import RegistrationRequest, LoginRequest, LoginResponse, RegistrationResponse
from core.security import verify_password, create_access_token

def register_user(db: Session, user : RegistrationRequest):
    existing_user = db.query(User).filter(
        or_(User.user_email == user.user_email,
            User.user_name == user.user_name)
    ).first()

    # Data Validation
    if existing_user:
        if existing_user.user_email == user.user_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        if existing_user.user_name == user.user_name:
            raise HTTPException(status_code=400, detail="Username already exists")

    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="The password is too long")
    
    if user.password != user.confirm_password :
        raise HTTPException(status_code=400, detail="The passwords do not match")
    
    
    # Encrypting the password
    hashed_password = hash_password(user.password)

    # Creating the user
    new_user = User(
        user_name=user.user_name,
        user_email=user.user_email,
        password_hash=hashed_password,
        birth_date=user.birth_date,
        about_author=user.about_author,
        social_link=user.social_link
    )

    # updating the database
    db.add(new_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error while saving user")
    db.refresh(new_user)
    return RegistrationResponse(user_id=new_user.user_id, message="The user was created")


def login_user(db: Session, payload : LoginRequest):
    user = db.query(User).filter(User.user_email == payload.user_email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.user_id),
        "role": user.user_role
    })

    return LoginResponse(
        user_id = user.user_id,
        access_token = token,
        token_type = "Bearer"
    )
