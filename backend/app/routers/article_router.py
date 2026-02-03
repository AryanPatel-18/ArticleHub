from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user_id
from schemas.article_schema import ArticleReadResponse
from services.article_service import get_article_by_id, create_article, get_saved_articles_for_user, get_articles_by_user, get_user_article_stats, delete_article, get_articles_by_tag, get_articles_by_author
from schemas.article_schema import ArticleResponse, ArticleCreateRequest, PaginatedSavedArticlesResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse, PaginatedArticlesByTagSchema, ArticleByTagSchema, PaginatedArticlesByAuthorSchema,ArticleByAuthorSchema
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

@router.get("/get/by-tag", response_model=PaginatedArticlesByTagSchema)
def fetch_articles_by_tag(
    tag_id: int = Query(..., description="Tag ID"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    page_size = 5

    articles, total_articles, total_pages = get_articles_by_tag(
        db=db,
        tag_id=tag_id,
        page=page,
        page_size=page_size
    )

    return PaginatedArticlesByTagSchema(
        tag_id=tag_id,
        page=page,
        page_size=page_size,
        total_articles=total_articles,
        total_pages=total_pages,
        articles=[
            ArticleByTagSchema(
                article_id=a.article_id,
                author_id=a.author_id,
                title=a.title,
                content=a.content,
                created_at=a.created_at
            )
            for a in articles
        ]
    )


@router.get("/get/by-author", response_model=PaginatedArticlesByAuthorSchema)
def fetch_articles_by_author(
    author_id: int = Query(..., description="User ID (author)"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    page_size = 5

    articles, total_articles, total_pages = get_articles_by_author(
        db=db,
        author_id=author_id,
        page=page,
        page_size=page_size
    )

    return PaginatedArticlesByAuthorSchema(
        author_id=author_id,
        page=page,
        page_size=page_size,
        total_articles=total_articles,
        total_pages=total_pages,
        articles=[
            ArticleByAuthorSchema(
                article_id=a.article_id,
                author_id=a.author_id,
                title=a.title,
                content=a.content,
                created_at=a.created_at
            )
            for a in articles
        ]
    )

@router.get("/get/saved", response_model=PaginatedSavedArticlesResponse)
def fetch_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return get_saved_articles_for_user(db, user_id,page, page_size)