from sqlalchemy.orm import Session
from app.models.article_model import Article, ArticleTag, Tag, ArticleStat
from app.models.vector_model import ArticleVector
from app.models.user_model import User
from app.models.interaction_model import UserInteraction
import math
from app.schemas.article_schema import ArticleReadResponse, ArticleCreateRequest, SavedArticleResponse, PaginatedSavedArticlesResponse,UserArticleResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse, ArticleUpdateRequest
from sqlalchemy import func, desc, asc
from fastapi import HTTPException, status
from datetime import datetime
from app.core.logger import get_logger

logger = get_logger(__name__)


"""
This service contains the core business logic for managing articles, including creating, reading, updating, and deleting articles, as well as fetching articles by tag or author and getting user-specific article statistics. The service interacts with the database to perform these operations and is used by the article router to handle API requests related to articles.
"""

# This is for fetching articles based on the id
def get_article_by_id(db: Session, get_id: int) -> ArticleReadResponse | None:
    logger.info(f"article_fetch_start article_id={get_id}")

    try:
        article = (
            db.query(Article)
            .filter(Article.article_id == get_id)
            .filter(Article.is_published)
            .first()
        )

        if article is None:
            logger.warning(f"article_not_found article_id={get_id}")
            return None

        author = (
            db.query(User.user_name)
            .filter(User.user_id == article.author_id)
            .first()
        )

        if author is None:
            logger.warning(
                f"article_author_missing article_id={get_id} author_id={article.author_id}"
            )
            return None

        tag_rows = (
            db.query(Tag.tag_name)
            .join(ArticleTag, Tag.tag_id == ArticleTag.tag_id)
            .filter(ArticleTag.article_id == article.article_id)
            .all()
        )

        tags = [row.tag_name for row in tag_rows]

        logger.info(f"article_loaded article_id={get_id}")

        return ArticleReadResponse(
            article_id=article.article_id,
            title=article.title,
            content=article.content,
            author_username=author.user_name,
            created_at=article.created_at,
            tags=tags
        )

    except Exception:
        logger.exception(f"article_fetch_failed article_id={get_id}")
        raise

"""This is for creating an article. It takes in the article creation request which contains the title, content, and tags. It returns the created article with the article id and author id. The tags are normalized to lowercase and stripped of whitespace. If a tag does not exist, it is created. The article is also added to the ArticleStat table for tracking views, likes, and saves. The article vectors are also created in the background, but that logic is handled in the background whereas the output of the function is sent first therefore the user does not have to wait for the vectorization. Thus there is a delay between the creation of the article and the vectors being used for the recommendation system and search feature for the other users"""
def create_article(
    db: Session,
    author_id: int,
    data: ArticleCreateRequest
):
    logger.info(f"article_create_start author_id={author_id}")

    try:
        article = Article(
            title=data.title,
            content=data.content,
            author_id=author_id
        )
        db.add(article)
        db.flush()

        # Normalize + deduplicate tags
        normalized_tags = {
            tag.strip().lower()
            for tag in data.tag_names
            if tag and tag.strip()
        }

        if not normalized_tags:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one valid tag is required"
            )

        tag_objects = []

        for tag_name in normalized_tags:
            tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()

            if not tag:
                tag = Tag(tag_name=tag_name)
                db.add(tag)
                db.flush()

            tag_objects.append(tag)

        for tag in tag_objects:
            db.add(
                ArticleTag(
                    article_id=article.article_id,
                    tag_id=tag.tag_id
                )
            )

        db.add(ArticleStat(article_id=article.article_id))

        db.commit()
        db.refresh(article)

        logger.info(f"article_created article_id={article.article_id}")
        return article

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("article_create_failed")
        raise


# get the articles that were saved by the user
def get_saved_articles_for_user(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 5
):    
    # 1. Count total saved articles
    total_results = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == user_id)
        .filter(UserInteraction.interaction_type == "save")
        .count()
    )

    total_pages = math.ceil(total_results / page_size) if total_results > 0 else 0

    if total_results == 0:
        return PaginatedSavedArticlesResponse(
            page=page,
            page_size=page_size,
            total_results=0,
            total_pages=0,
            articles=[]
        )

    # 2. Get paginated saved article IDs (IMPORTANT: use scalars)
    article_ids = [
        row[0] for row in (
            db.query(UserInteraction.article_id)
            .filter(UserInteraction.user_id == user_id)
            .filter(UserInteraction.interaction_type == "save")
            .order_by(UserInteraction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
    ]

    if not article_ids:
        return PaginatedSavedArticlesResponse(
            page=page,
            page_size=page_size,
            total_results=total_results,
            total_pages=total_pages,
            articles=[]
        )

    # 3. Load articles with author name + like count
    rows = (
        db.query(
            Article,
            User.user_name,
            ArticleStat.like_count
        )
        .join(User, Article.author_id == User.user_id)
        .join(ArticleStat, Article.article_id == ArticleStat.article_id)
        .filter(Article.article_id.in_(article_ids))
        .filter(Article.is_published)
        .all()
    )

    # Map article_id -> (Article, username, likes)
    article_map = {
        article.article_id: (article, username, likes)
        for article, username, likes in rows
    }

    # 4. Build response preserving save order
    result = []
    for aid in article_ids:
        if aid not in article_map:
            continue  # article deleted but save still exists

        article, username, likes = article_map[aid]

        result.append(
            SavedArticleResponse(
                article_id=article.article_id,
                likes=likes,
                title=article.title,
                content=article.content,
                author_username=username,
                created_at=article.created_at
            )
        )
    logger.info(
        f"saved_articles_loaded user_id={user_id} "
        f"results={len(result)} page={page}"
    )
    return PaginatedSavedArticlesResponse(
        page=page,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        articles=result
    )

# Get the articles that were created by the user
def get_articles_by_user(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 5,
    sort: str = "newest"
):
    valid_sorts = {"newest", "oldest", "most_liked"}

    if sort not in valid_sorts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid sort value"
        )

    total_results = (
        db.query(Article)
        .filter(Article.author_id == user_id)
        .count()
    )

    total_pages = math.ceil(total_results / page_size) if total_results > 0 else 0

    if total_results == 0:
        return PaginatedUserArticlesResponse(
            page=page,
            page_size=page_size,
            total_results=0,
            total_pages=0,
            articles=[]
        )

    query = (
        db.query(Article, User.user_name)
        .join(User, Article.author_id == User.user_id)
        .filter(Article.author_id == user_id)
    )

    if sort == "oldest":
        query = query.order_by(asc(Article.created_at))

    elif sort == "most_liked":
        query = (
            query.join(ArticleStat, Article.article_id == ArticleStat.article_id)
                 .order_by(desc(ArticleStat.like_count))
        )

    else:  # newest
        query = query.order_by(desc(Article.created_at))

    rows = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    articles = [
        UserArticleResponse(
            article_id=article.article_id,
            title=article.title,
            content=article.content,
            author_username=username,
            created_at=article.created_at
        )
        for article, username in rows
    ]

    logger.info(
        f"user_articles_loaded user_id={user_id} "
        f"page={page} sort={sort} results={len(articles)}"
    )

    return PaginatedUserArticlesResponse(
        page=page,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        articles=articles
    )


# Get the stats ( likes, saves and views) of all the articles that were created by the user
def get_user_article_stats(db: Session, user_id: int) -> UserArticleStatsResponse:
    # total articles
    total_articles = (
        db.query(func.count(Article.article_id))
        .filter(Article.author_id == user_id)
        .scalar()
    )

    # published articles
    published_articles = (
        db.query(func.count(Article.article_id))
        .filter(Article.author_id == user_id)
        .filter(Article.is_published)
        .scalar()
    )

    # aggregate stats (join with articles to scope to this user)
    stats = (
        db.query(
            func.coalesce(func.sum(ArticleStat.view_count), 0),
            func.coalesce(func.sum(ArticleStat.like_count), 0),
            func.coalesce(func.sum(ArticleStat.save_count), 0),
        )
        .join(Article, Article.article_id == ArticleStat.article_id)
        .filter(Article.author_id == user_id)
        .first()
    )

    total_views, total_likes, total_saves = stats
    logger.info(f"user_article_stats_loaded user_id={user_id}")

    return UserArticleStatsResponse(
        total_articles=total_articles,
        published_articles=published_articles,
        total_views=total_views,
        total_likes=total_likes,
        total_saves=total_saves
    )

# Delete the article that were created by the user. In this case only the articles that were created by the user would be deleted and if the user has not created the said article then it would return the 401 unauthorized error
def delete_article(db: Session, article_id: int, user_id: int):
    article = (
        db.query(Article)
        .filter(Article.article_id == article_id)
        .filter(Article.author_id == user_id)
        .first()
    )
    
    found_article = (
        db.query(Article)
        .filter(Article.article_id == article_id)
        .first()
    )
    
    if not found_article:
        raise HTTPException(status_code=404, detail="Article Not Found")

    if not article:
        raise HTTPException(status_code=403, detail="You cannot delete this article")

    logger.info(f"article_delete_start article_id={article_id} user_id={user_id}")
    # delete dependent rows first
    db.query(ArticleStat).filter(ArticleStat.article_id == article_id).delete()
    db.query(ArticleVector).filter(ArticleVector.article_id == article_id).delete()
    db.query(ArticleTag).filter(ArticleTag.article_id == article_id).delete()
    db.query(UserInteraction).filter(UserInteraction.article_id == article_id).delete()

    db.delete(article)
    db.commit()
    logger.info(f"article_deleted article_id={article_id}")

    return {"message": "Article deleted successfully"}

# Get all the articles based on the tag name 
def get_articles_by_tag(
    db: Session,
    tag_id: int,
    page: int = 1,
    page_size: int = 5
):
    if page < 1:
        page = 1

    offset = (page - 1) * page_size

    # Fetch tag name
    tag = db.query(Tag).filter(Tag.tag_id == tag_id).first()
    if not tag:
        return None, None, 0, 0  # handled in router

    base_query = (
        db.query(Article)
        .join(ArticleTag, Article.article_id == ArticleTag.article_id)
        .filter(ArticleTag.tag_id == tag_id)
        .filter(Article.is_published)
        .order_by(Article.created_at.desc())
    )

    total_articles = base_query.count()
    total_pages = (total_articles + page_size - 1) // page_size

    articles = (
        base_query
        .offset(offset)
        .limit(page_size)
        .all()
    )
    logger.info(
        f"articles_by_tag_loaded tag_id={tag_id} "
        f"results={len(articles)} page={page}"
    )

    return tag.tag_name, articles, total_articles, total_pages

# Get all the articles based on the author id
def get_articles_by_author(
    db: Session,
    author_id: int,
    page: int = 1,
    page_size: int = 5
):
    if page < 1:
        page = 1

    offset = (page - 1) * page_size

    # 🔹 Fetch author name from users table
    author = db.query(User).filter(User.user_id == author_id).first()
    if not author:
        return None, None, 0, 0

    base_query = (
        db.query(Article)
        .filter(Article.author_id == author_id)
        .filter(Article.is_published)
        .order_by(Article.created_at.desc())
    )

    total_articles = base_query.count()
    total_pages = (total_articles + page_size - 1) // page_size

    articles = (
        base_query
        .offset(offset)
        .limit(page_size)
        .all()
    )
    logger.info(
        f"articles_by_author_loaded author_id={author_id} "
        f"results={len(articles)} page={page}"
    )

    return author.user_name, articles, total_articles, total_pages


# This function is almost the same as the created article function just in this case the information is updated , but the vectorization portion of this function remains the same as the create vector function. Also there is another verification of the user id that check if the article was created by the user id that requested to edit the said article.
def update_article(
    db: Session,
    article_id: int,
    user_id: int,
    data: ArticleUpdateRequest
):
    logger.info(
        f"article_update_start article_id={article_id} user_id={user_id}"
    )

    try:
        article = db.query(Article).filter(
            Article.article_id == article_id
        ).first()

        if not article:
            return None

        if article.author_id != user_id:
            raise PermissionError("Not your article")

        # -----------------------------
        # TAG VALIDATION + NORMALIZATION
        # -----------------------------
        cleaned_tags = {
            tag.strip().lower()
            for tag in data.tag_names
            if tag and tag.strip()
        }

        if not cleaned_tags:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tag list cannot be empty"
            )

        article.title = data.title
        article.content = data.content
        article.updated_at = datetime.utcnow()

        db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id
        ).delete()

        logger.info(f"article_vector_invalidated article_id={article_id}")

        tag_objects = []

        for tag_name in cleaned_tags:
            tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()

            if not tag:
                tag = Tag(tag_name=tag_name)
                db.add(tag)
                db.flush()

            tag_objects.append(tag)

        for tag in tag_objects:
            db.add(
                ArticleTag(
                    article_id=article.article_id,
                    tag_id=tag.tag_id
                )
            )

        db.query(ArticleVector).filter(
            ArticleVector.article_id == article.article_id
        ).delete()

        db.commit()
        logger.info(f"article_updated article_id={article_id}")
        db.refresh(article)

        return article, [t.tag_name for t in tag_objects]

    except PermissionError:
        db.rollback()
        logger.warning(
            f"article_update_permission_denied article_id={article_id} user_id={user_id}"
        )
        raise

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("article_update_failed")
        raise