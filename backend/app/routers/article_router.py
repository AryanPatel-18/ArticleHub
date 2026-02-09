from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.article_schema import ArticleReadResponse
from app.services.article_service import get_article_by_id, create_article, get_saved_articles_for_user, get_articles_by_user, get_user_article_stats, delete_article, get_articles_by_tag, get_articles_by_author, update_article
from app.schemas.article_schema import ArticleResponse, ArticleCreateRequest, PaginatedSavedArticlesResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse, PaginatedArticlesByTagSchema, ArticleByTagSchema, PaginatedArticlesByAuthorSchema,ArticleByAuthorSchema, ArticleUpdateRequest, ArticleUpdateResponse
from app.services.vector_background_service import create_article_vector_background
import os
router = APIRouter(prefix="/articles", tags=["Articles"])

@router.get("/{article_id}", response_model=ArticleReadResponse, summary="Get an article by its ID")
def read_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article Does Not Exist")

    return article

@router.post("/", response_model=ArticleResponse, status_code=201, summary="Create a new article")
def create_article_endpoint(
    payload: ArticleCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    article = create_article(db, user_id, payload)

    # Skip heavy background jobs during tests
    if os.getenv("TESTING") != "1":
        background_tasks.add_task(
            create_article_vector_background,
            article.article_id
        )

    return article


@router.get("/saved/list", response_model=PaginatedSavedArticlesResponse, summary="Get a paginated list of your saved articles")
def get_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_saved_articles_for_user(db, user_id, page, page_size)


@router.get("/user/me",response_model=PaginatedUserArticlesResponse, summary="Get a paginated list of your articles with sorting options")
def get_my_articles(
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_articles_by_user(db, user_id, page, page_size,sort)



@router.get("/stats/me",response_model=UserArticleStatsResponse, summary="Get statistics about your articles (total, interactions, etc.)")
def get_my_article_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_article_stats(db, user_id)

@router.delete("/{article_id}", summary="Delete an article you authored")
def delete_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return delete_article(db, article_id, user_id)

@router.get("/get/by-tag", response_model=PaginatedArticlesByTagSchema, summary="Get a paginated list of articles by tag")
def fetch_articles_by_tag(
    tag_id: int = Query(..., description="Tag ID"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    page_size = 5

    tag_name, articles, total_articles, total_pages = get_articles_by_tag(
        db=db,
        tag_id=tag_id,
        page=page,
        page_size=page_size
    )

    if tag_name is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    return PaginatedArticlesByTagSchema(
        tag_id=tag_id,
        tag_name=tag_name,   # ✅ now included
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

@router.get("/get/by-author", response_model=PaginatedArticlesByAuthorSchema, summary="Get a paginated list of articles by author")
def fetch_articles_by_author(
    author_id: int = Query(..., description="User ID (author)"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    page_size = 5

    author_name, articles, total_articles, total_pages = get_articles_by_author(
        db=db,
        author_id=author_id,
        page=page,
        page_size=page_size
    )

    if author_name is None:
        raise HTTPException(status_code=404, detail="Author not found")

    return PaginatedArticlesByAuthorSchema(
        author_id=author_id,
        author_name=author_name,  # ✅ now included
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

@router.get("/get/saved", response_model=PaginatedSavedArticlesResponse, summary="Get a paginated list of your saved articles")
def fetch_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return get_saved_articles_for_user(db, user_id,page, page_size)

@router.put("/{article_id}", response_model=ArticleUpdateResponse, summary="Update an article you authored")
def edit_article(
    article_id: int,
    data: ArticleUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    try:
        result = update_article(
            db=db,
            article_id=article_id,
            user_id=user_id,
            data=data
        )
    except PermissionError:
        raise HTTPException(
            status_code=401,
            detail="Not authorized to edit this article"
        )

    if result is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article, tag_names = result

    background_tasks.add_task(
        create_article_vector_background,
        article.article_id
    )

    return ArticleUpdateResponse(
        article_id=article.article_id,
        title=article.title,
        content=article.content,
        author_id=article.author_id,
        updated_at=article.updated_at,
        tag_names=tag_names
    )
