from sqlalchemy.orm import Session
from models.user_model import User
from schemas.user_schema import UserProfileUpdateRequest, PasswordChangeRequest
from core.security import hash_password, verify_password

def get_user_profile(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    return user

def update_user_profile(db: Session, user_id: int, data: UserProfileUpdateRequest):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
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
    return user


def change_user_password(
    db: Session,
    user_id: int,
    data: PasswordChangeRequest
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None

    # 🔐 Verify old password
    if not verify_password(data.old_password, user.password_hash):
        return False

    if data.new_password != data.confirm_new_password:
        return False
    
    # 🔐 Hash new password
    new_hashed_password = hash_password(data.new_password)

    # 🔐 Update password
    user.password_hash = new_hashed_password
    db.commit()
    db.refresh(user)

    return True