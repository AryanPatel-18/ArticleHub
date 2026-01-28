from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from models.user_model import User
from schemas.auth_schema import (
    RegistrationRequest,
    RegistrationResponse,
    LoginRequest,
    LoginResponse
)
from core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def register_user(db: Session, user: RegistrationRequest):
    # Check for existing email or username
    existing_user = db.query(User).filter(
        or_(
            User.user_email == user.user_email,
            User.user_name == user.user_name
        )
    ).first()

    if existing_user:
        if existing_user.user_email == user.user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        if existing_user.user_name == user.user_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

    # bcrypt hard limit (security requirement)
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long"
        )

    # Hash password
    hashed_password = hash_password(user.password)

    # Create user instance
    new_user = User(
        user_name=user.user_name,
        user_email=user.user_email,
        password_hash=hashed_password,
        birth_date=user.birth_date,
        bio=user.bio,
        social_link=user.social_link,
        user_role="user"
    )

    db.add(new_user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating user"
        )

    db.refresh(new_user)

    return RegistrationResponse(
        user_id=new_user.user_id,
        message="User registered successfully"
    )


def login_user(db: Session, payload: LoginRequest):
    user = db.query(User).filter(
        User.user_email == payload.user_email
    ).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token({
        "sub": str(user.user_id),
        "role": user.user_role
    })

    return LoginResponse(
        user_id=user.user_id,
        access_token=access_token,
        token_type="Bearer"
    )
