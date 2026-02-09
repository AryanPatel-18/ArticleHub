from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user_id
from app.services.recommendation_service import get_top_articles_for_user
from app.schemas.article_schema import PaginatedArticleRecommendationResponse

# This router handles the endpoint related to personalized article recommendations for users based on their interactions and preferences.

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Endpoint to get personalized article recommendations for the authenticated user. The recommendations are based on the user's interactions with articles (likes, saves, views).
@router.get("/", response_model=PaginatedArticleRecommendationResponse, summary="Get personalized article recommendations based on your interactions")
def recommend_articles(
    page: int = 1,
    page_size: int = 5,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_top_articles_for_user(db, user_id, page, page_size)
