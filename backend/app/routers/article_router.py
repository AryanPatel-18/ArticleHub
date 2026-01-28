from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db
from schemas.article_schema import ArticleReadResponse
from services.article_service import get_article_by_id

router = APIRouter(prefix="/articles", tags=["Articles"])

@router.get("/{article_id}", response_model=ArticleReadResponse)
def read_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Random Random")

    return article

