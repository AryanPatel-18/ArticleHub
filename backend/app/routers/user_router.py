from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user_schema import UserProfileResponse,UserProfileUpdateRequest,PasswordChangeRequest, PasswordChangeResponse
from app.core.dependencies import get_db, get_current_user_id
from app.services.user_service import get_user_profile,update_user_profile,change_user_password
from sqlalchemy.orm import Session


router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):


    user = get_user_profile(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        user_id=user.user_id,
        user_email=user.user_email,
        user_name=user.user_name,
        birth_date=user.birth_date,
        bio=user.bio,
        user_role=user.user_role,
        social_link=user.social_link,
        created_at=user.created_at
    )


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    user = update_user_profile(db, user_id, data)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        user_id=user.user_id,
        user_email=user.user_email,
        user_name=user.user_name,
        birth_date=user.birth_date,
        bio=user.bio,
        user_role=user.user_role,
        social_link=user.social_link,
        created_at=user.created_at
    )

@router.put("/me/password", response_model=PasswordChangeResponse)
def change_my_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    result = change_user_password(db, user_id, data)

    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    if result is False:
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    return PasswordChangeResponse(
        message="Password updated successfully"
    )