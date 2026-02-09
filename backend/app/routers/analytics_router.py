from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.dependencies import get_current_user_id
from app.services.analytics_service import (
    generate_user_article_interaction_graph
)

# Analytics router for endpoints related to user interaction analytics and insights
router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# Endpoint to get a graph of the user's interactions with articles (likes, saves, views) with respect to the time of interaction. This can help users visualize their engagement over time.
@router.get("/my-articles/interactions-graph", summary="Get a graph of your interactions with articles")
def get_my_article_interaction_graph(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    image_buffer = generate_user_article_interaction_graph(
        db=db,
        user_id=user_id
    )

    return StreamingResponse(
        image_buffer,
        media_type="image/png"
    )
