from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user_id
from schemas.article_schema import ArticleReadResponse
from services.article_service import get_article_by_id, create_article, get_saved_articles_for_user, get_articles_by_user, get_user_article_stats, delete_article
from schemas.article_schema import ArticleResponse, ArticleCreateRequest, PaginatedSavedArticlesResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse
from core.security import decode_access_token

router = APIRouter(prefix="/articles", tags=["Articles"])

@router.get("/{article_id}", response_model=ArticleReadResponse)
def read_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Random Random")

    return article

@router.post("/", response_model=ArticleResponse)
def create_article_endpoint(
    payload: ArticleCreateRequest,
    db: Session = Depends(get_db)
):
    user_id = decode_access_token(payload.token)['sub']
    return create_article(db, user_id, payload)


@router.get("/saved/list", response_model=PaginatedSavedArticlesResponse)
def get_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_saved_articles_for_user(db, user_id, page, page_size)


@router.get("/user/me",response_model=PaginatedUserArticlesResponse)
def get_my_articles(
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_articles_by_user(db, user_id, page, page_size,sort)



@router.get("/stats/me",response_model=UserArticleStatsResponse)
def get_my_article_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_article_stats(db, user_id)

@router.delete("/delete/{article_id}")
def delete_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return delete_article(db, article_id, user_id)