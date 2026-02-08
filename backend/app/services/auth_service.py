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
from services.user_vector_service import create_default_user_vector
from core.logger import get_logger
logger = get_logger(__name__)

def register_user(db: Session, user: RegistrationRequest):
    logger.info(f"user_registration_start email={user.user_email}")

    existing_user = db.query(User).filter(
        or_(
            User.user_email == user.user_email,
            User.user_name == user.user_name
        )
    ).first()

    if existing_user:
        logger.warning("user_registration_conflict")
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

    if len(user.password.encode("utf-8")) > 72:
        logger.warning("user_registration_password_too_long")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long"
        )

    hashed_password = hash_password(user.password)

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
        logger.info(f"user_created user_id={new_user.user_id}")

    except Exception:
        db.rollback()
        logger.exception("user_creation_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating user"
        )

    db.refresh(new_user)

    create_default_user_vector(db, new_user.user_id)
    logger.info(f"user_vector_initialized user_id={new_user.user_id}")

    return RegistrationResponse(
        user_id=new_user.user_id,
        message="User registered successfully"
    )



def login_user(db: Session, payload: LoginRequest):
    logger.info(f"login_attempt email={payload.user_email}")

    try:
        user = db.query(User).filter(
            User.user_email == payload.user_email
        ).first()

        if not user or not verify_password(payload.password, user.password_hash):
            logger.warning(f"login_failed email={payload.user_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        access_token = create_access_token({
            "sub": str(user.user_id),
            "role": user.user_role
        })

        logger.info(f"login_success user_id={user.user_id}")

        return LoginResponse(
            user_id=user.user_id,
            access_token=access_token,
            token_type="Bearer"
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("login_error")
        raise

