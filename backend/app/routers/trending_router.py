from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.trending_service import get_trending_tags, get_trending_authors
from app.schemas.trending_schema import TrendingTagSchema, TrendingAuthorSchema
from typing import List

# This router handles the endpoints related to trending tags and authors based on recent article interactions

router = APIRouter(prefix="/trending", tags=["Trending"])

# Endpoint to get a list of trending tags based on recent article interactions. The tags are ranked based on the number of interactions
@router.get("/tags", response_model=List[TrendingTagSchema], summary="Get a list of trending tags based on recent article interactions")
def fetch_trending_tags(db: Session = Depends(get_db)):
    tags = get_trending_tags(db, days=7, limit=10)

    return [
        TrendingTagSchema(
            tag_id=row.tag_id,
            tag_name=row.tag_name,
            count=row.count
        )
        for row in tags
    ]

# Endpoint to get a list of trending authors based on recent article interactions. The authors are ranked based on the number of interactions with their articles
@router.get("/authors", response_model=list[TrendingAuthorSchema], summary="Get a list of trending authors based on recent article interactions")
def fetch_trending_authors(db: Session = Depends(get_db)):
    authors = get_trending_authors(db, days=7, limit=10)

    return [
        TrendingAuthorSchema(
            user_id=row.user_id,
            user_name=row.user_name,
            count=row.count
        )
        for row in authors
    ]