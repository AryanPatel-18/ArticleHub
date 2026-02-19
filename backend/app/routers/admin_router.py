from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
    require_admin
)

from app.schemas.admin_schema import (
    AdminActionResponse,
    AdminDeleteRequest
)

from app.services.admin_service import (
    admin_delete_article,
    admin_delete_tag,
    admin_delete_user
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)


@router.delete("/articles/{article_id}", response_model=AdminActionResponse)
def delete_article_admin(
    article_id: int,
    payload: AdminDeleteRequest,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)
):
    return admin_delete_article(
        db=db,
        article_id=article_id,
        admin_user_id=admin.user_id,
        reason=payload.reason
    )


@router.delete("/tags/{tag_id}", response_model=AdminActionResponse)
def delete_tag_admin(
    tag_id: int,
    payload: AdminDeleteRequest,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)
):
    return admin_delete_tag(
        db=db,
        tag_id=tag_id,
        admin_user_id=admin.user_id,
        reason=payload.reason
    )


@router.delete("/users/{target_user_id}", response_model=AdminActionResponse)
def delete_user_admin(
    target_user_id: int,
    payload: AdminDeleteRequest,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)
):
    return admin_delete_user(
        db=db,
        target_user_id=target_user_id,
        admin_user_id=admin.user_id,
        reason=payload.reason
    )


@router.get("/me")
def get_current_user_info(
    user = Depends(get_current_user)
):
    return {
        "user_id": user.user_id,
        "role": user.user_role
    }
