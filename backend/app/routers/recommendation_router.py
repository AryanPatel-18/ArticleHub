from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.recommendation_service import get_top_articles_for_user
from schemas.article_schema import ArticleRecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/{user_id}", response_model=list[ArticleRecommendationResponse])
def recommend_articles(user_id: int, db: Session = Depends(get_db)):
    return get_top_articles_for_user(db, user_id)
