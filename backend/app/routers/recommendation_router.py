from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.recommendation_service import get_top_articles_for_user
from schemas.article_schema import PaginatedArticleRecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/", response_model=PaginatedArticleRecommendationResponse)
def recommend_articles(
    user_id: int,
    session_id: str,
    page: int = 1,
    db: Session = Depends(get_db)
):
    return get_top_articles_for_user(db, user_id, session_id, page)
