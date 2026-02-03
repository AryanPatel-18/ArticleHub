from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.trending_service import get_trending_tags, get_trending_authors
from schemas.trending_schema import TrendingTagSchema, TrendingAuthorSchema
from typing import List

router = APIRouter(prefix="/trending", tags=["Trending"])

@router.get("/tags", response_model=List[TrendingTagSchema])
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


@router.get("/authors", response_model=list[TrendingAuthorSchema])
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