from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.interaction_schema import UserInteractionCreateRequest, UserInteractionResponse, InteractionStatusResponse, InteractionToggleResponse , InteractionToggleRequest
from app.services.interaction_service import create_interaction, get_interaction_status, toggle_interaction

# This router handles all the endpoints related to user interactions with articles, such as liking, saving, and viewing articles.
router = APIRouter(prefix="/interactions", tags=["Interactions"])


# Endpoint to record a user interaction with an article. This can be used for likes, saves, and views.
@router.post("/", response_model=UserInteractionResponse, summary="Record a user interaction with an article (like, save, view)")
def add_interaction(
    user_id: int,
    data: UserInteractionCreateRequest,
    db: Session = Depends(get_db)
):
    return create_interaction(db, user_id, data)

# Endpoint to get the interaction status (liked, saved) for a specific article. This can be used to show the current interaction status of an article for the user.
@router.get("/status", response_model=InteractionStatusResponse, summary="Get the interaction status (liked, saved) for a specific article")
def interaction_status(user_id: int,article_id: int,db: Session = Depends(get_db)):
    return get_interaction_status(db, user_id, article_id)

# Endpoint to toggle an interaction (like, save) for a specific article. If the interaction already exists, it will be removed. If it does not exist, it will be created. This allows users to easily like or save an article with a single endpoint. This also marks the user as dirty therefore there is no need to update the user every time the user has clicked an article, they would be updated once they exit from the page
@router.post("/toggle", response_model=InteractionToggleResponse, summary="Toggle an interaction (like, save) for a specific article")
def toggle_interaction_route(
    data: InteractionToggleRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return toggle_interaction(db, user_id, data)
