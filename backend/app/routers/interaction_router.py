from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.interaction_schema import UserInteractionCreateRequest, UserInteractionResponse, InteractionStatusResponse, InteractionToggleResponse , InteractionToggleRequest
from app.services.interaction_service import create_interaction, get_interaction_status, toggle_interaction


router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.post("/", response_model=UserInteractionResponse, summary="Record a user interaction with an article (like, save, view)")
def add_interaction(
    user_id: int,
    data: UserInteractionCreateRequest,
    db: Session = Depends(get_db)
):
    return create_interaction(db, user_id, data)

@router.get("/status", response_model=InteractionStatusResponse, summary="Get the interaction status (liked, saved) for a specific article")
def interaction_status(user_id: int,article_id: int,db: Session = Depends(get_db)):
    return get_interaction_status(db, user_id, article_id)


@router.post("/toggle", response_model=InteractionToggleResponse, summary="Toggle an interaction (like, save) for a specific article")
def toggle_interaction_route(
    data: InteractionToggleRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return toggle_interaction(db, user_id, data)
