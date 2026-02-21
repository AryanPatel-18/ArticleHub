from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.article_schema import ArticleReadResponse
from app.services.article_service import get_article_by_id, create_article, get_saved_articles_for_user, get_articles_by_user, get_user_article_stats, delete_article, get_articles_by_tag, get_articles_by_author, update_article
from app.schemas.article_schema import ArticleResponse, ArticleCreateRequest, PaginatedSavedArticlesResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse, PaginatedArticlesByTagSchema, ArticleByTagSchema, PaginatedArticlesByAuthorSchema,ArticleByAuthorSchema, ArticleUpdateRequest, ArticleUpdateResponse
from app.services.vector_background_service import create_article_vector_background
import os


# Article router for endpoints related to article management (CRUD operations, fetching by tag/author)

router = APIRouter(prefix="/articles", tags=["Articles"])

# Endpoint to get an article by its ID. This is a basic read operation that allows users to view the details of a specific article. The article id in this case is passed through the url. This would return the article if it exists or it would simply return 404 error if the article does not exist
@router.get("/{article_id}", response_model=ArticleReadResponse, summary="Get an article by its ID")
def read_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article Does Not Exist")

    return article

# Endpoint to create a new article. This allows only authenticated users to create articles. The article details are passed in the request body in json format. The vector generation is done in the background to avoid blocking the user from browsing the rest of the webpage. This endpoint would return the article details if the article is created successfully or it would return 401 error if the user is not authenticated.

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


# Gets the user the paginated list of the articles that it has created. return 401 if the user if not authenticated. Also you can pass the page size as well as the page length in the url parameters
@router.get("/user/me",response_model=PaginatedUserArticlesResponse, summary="Get a paginated list of your articles with sorting options")
def get_my_articles(
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_articles_by_user(db, user_id, page, page_size,sort)


# Return the stats of the user articles such as total articles, total likes, total saves, total views. This would return 401 if the user is not authenticated.
@router.get("/stats/me",response_model=UserArticleStatsResponse, summary="Get statistics about your articles (total, interactions, etc.)")
def get_my_article_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_user_article_stats(db, user_id)


# For deleting the article. User can only delete the articles that he or she has created. return 401 if the user is not authenticated or not authorized to delete the article. Also returns 404 if the article does not exist.
@router.delete("/{article_id}", summary="Delete an article you authored")
def delete_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return delete_article(db, article_id, user_id)

# Endpoint to fetch the articles based on the tag. return 401 if the user is not authenticated. Or would return 404 if the tag does not exist
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
        tag_name=tag_name,  
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

# Endpoint to fetch the articles based on the author. return 401 if the user is not authenticated. Or would return 404 if the author does not exist

@router.get("/get/by-author", response_model=PaginatedArticlesByAuthorSchema, summary="Get a paginated list of articles by author")
def fetch_articles_by_author(
    author_id: int = Query(..., description="User ID (author)"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    page_size = 5

    author_name, author_bio, articles, total_articles, total_pages = get_articles_by_author(
        db=db,
        author_id=author_id,
        page=page,
        page_size=page_size
    )

    if author_name is None:
        raise HTTPException(status_code=404, detail="Author not found")

    return PaginatedArticlesByAuthorSchema(
        author_id=author_id,
        author_name=author_name,
        author_bio=author_bio,
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
# Endpoint to get a paginated list of user's saved articles. This would return 401 if the user is not authenticated. The pagination parameters that is the page number and page size can be passed in as the url parameters.
@router.get("/get/saved", response_model=PaginatedSavedArticlesResponse, summary="Get a paginated list of your saved articles")
def fetch_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return get_saved_articles_for_user(db, user_id,page, page_size)


# Endpoint to update an article. User can only update the articles that he or she has created. return 401 if the user is not authenticated or not authorized to update the article. Also returns 404 if the article does not exist. The vector generation is done in the background to avoid blocking the user from browsing the rest of the webpage.

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
