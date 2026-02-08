from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.dependencies import get_db
from core.dependencies import get_current_user_id
from services.analytics_service import (
    generate_user_article_interaction_graph
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/my-articles/interactions-graph")
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
