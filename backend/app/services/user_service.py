from sqlalchemy.orm import Session
from app.models.user_model import User
from app.schemas.user_schema import UserProfileUpdateRequest, PasswordChangeRequest
from app.core.security import hash_password, verify_password
from app.core.logger import get_logger
logger = get_logger(__name__)


# Get the user profile information based on the user ID, would return 404 if the user does not exist
def get_user_profile(db: Session, user_id: int):
    logger.info(f"user_profile_fetch user_id={user_id}")
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            logger.warning(f"user_profile_not_found user_id={user_id}")

        return user

    except Exception:
        logger.exception(f"user_profile_fetch_failed user_id={user_id}")
        raise

# For updating the user information, this is a common function that is used between multiple routers. As to reduce the redundant code and also increase the efficiency of the code by just having one function that can be used to update the user information instead of having multiple functions that would do the same thing
def update_user_profile(db: Session, user_id: int, data: UserProfileUpdateRequest):
    logger.info(f"user_profile_update_start user_id={user_id}")

    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"user_profile_update_missing user_id={user_id}")
            return None

        if data.user_name is not None:
            user.user_name = data.user_name

        if data.birth_date is not None:
            user.birth_date = data.birth_date

        if data.bio is not None:
            user.bio = data.bio

        if data.social_link is not None:
            user.social_link = data.social_link

        if data.email is not None:
            user.user_email = data.email

        db.commit()
        db.refresh(user)

        logger.info(f"user_profile_updated user_id={user_id}")

        return user

    except Exception:
        db.rollback()
        logger.exception(f"user_profile_update_failed user_id={user_id}")
        raise


# For changing the user password, this function would verify the old password and if it is valid it would return true else it would return false. It would also return 404 if the user does not exist.
def change_user_password(
    db: Session,
    user_id: int,
    data: PasswordChangeRequest
):
    logger.info(f"password_change_attempt user_id={user_id}")

    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"password_change_user_missing user_id={user_id}")
            return None

        if not verify_password(data.old_password, user.password_hash):
            logger.warning(f"password_change_invalid_old user_id={user_id}")
            return False

        if data.new_password != data.confirm_new_password:
            logger.warning(f"password_change_mismatch user_id={user_id}")
            return False

        new_hashed_password = hash_password(data.new_password)
        user.password_hash = new_hashed_password

        db.commit()
        db.refresh(user)

        logger.info(f"password_changed user_id={user_id}")

        return True

    except Exception:
        db.rollback()
        logger.exception(f"password_change_failed user_id={user_id}")
        raise
