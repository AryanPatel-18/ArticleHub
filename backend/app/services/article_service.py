from sqlalchemy.orm import Session
from models.article_model import Article, ArticleTag, Tag, ArticleStat
from models.vector_model import ArticleVector
from models.user_model import User
from models.interaction_model import UserInteraction
import math
from schemas.article_schema import ArticleReadResponse, ArticleCreateRequest, SavedArticleResponse, PaginatedSavedArticlesResponse,UserArticleResponse, PaginatedUserArticlesResponse, UserArticleStatsResponse, ArticleUpdateRequest
from services.article_vector_service import create_article_vector
from sqlalchemy import func, desc, asc
from fastapi import HTTPException
from datetime import datetime

def get_article_by_id(db: Session, get_id: int) -> ArticleReadResponse | None:
    article = (
        db.query(Article)
        .filter(Article.article_id == get_id)
        .filter(Article.is_published)
        .first()
    )

    if article is None:
        return None

    author = (
        db.query(User.user_name)
        .filter(User.user_id == article.author_id)
        .first()
    )

    if author is None:
        return None

    tag_rows = (
        db.query(Tag.tag_name)
        .join(ArticleTag, Tag.tag_id == ArticleTag.tag_id)
        .filter(ArticleTag.article_id == article.article_id)
        .all()
    )

    tags = [row.tag_name for row in tag_rows]

    return ArticleReadResponse(
        article_id=article.article_id,
        title=article.title,
        content=article.content,
        author_username=author.user_name,
        created_at=article.created_at,
        tags=tags
    )

def create_article(
    db: Session,
    author_id: int,
    data: ArticleCreateRequest
):
    try:
        # 1. Create article
        article = Article(
            title=data.title,
            content=data.content,
            author_id=author_id
        )
        db.add(article)
        db.flush()  # get article.article_id

        tag_objects = []

        # 2. Handle tags (create if missing)
        for tag_name in data.tag_names:
            tag_name = tag_name.strip().lower()

            tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()
            if not tag:
                tag = Tag(tag_name=tag_name)
                db.add(tag)
                db.flush()  # get tag.tag_id

            tag_objects.append(tag)

        # 3. Create article-tag links
        for tag in tag_objects:
            link = ArticleTag(
                article_id=article.article_id,
                tag_id=tag.tag_id
            )
            db.add(link)

        # 4. Create stats row
        stats = ArticleStat(article_id=article.article_id)
        db.add(stats)

        # 5. Create vectors (same transaction)
        create_article_vector(db, article.article_id)

        # ✅ SINGLE COMMIT
        db.commit()
        db.refresh(article)

        return article

    except Exception as e:
        db.rollback()
        raise e

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

    return PaginatedSavedArticlesResponse(
        page=page,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        articles=result
    )
    
def get_articles_by_user(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 5,
    sort: str = "newest"   # ✅ added
):
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

    # ✅ only new logic: sorting
    if sort == "oldest":
        query = query.order_by(asc(Article.created_at))
    elif sort == "most_liked":
        query = (
            query.join(ArticleStat, Article.article_id == ArticleStat.article_id)
                 .order_by(desc(ArticleStat.like_count))
        )
    else:  # newest (default)
        query = query.order_by(desc(Article.created_at))

    rows = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    articles = []
    for article, username in rows:
        articles.append(
            UserArticleResponse(
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                author_username=username,
                created_at=article.created_at
            )
        )

    return PaginatedUserArticlesResponse(
        page=page,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        articles=articles
    )

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

    return UserArticleStatsResponse(
        total_articles=total_articles,
        published_articles=published_articles,
        total_views=total_views,
        total_likes=total_likes,
        total_saves=total_saves
    )

def delete_article(db: Session, article_id: int, user_id: int):
    article = (
        db.query(Article)
        .filter(Article.article_id == article_id)
        .filter(Article.author_id == user_id)
        .first()
    )

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # delete dependent rows first
    db.query(ArticleStat).filter(ArticleStat.article_id == article_id).delete()
    db.query(ArticleVector).filter(ArticleVector.article_id == article_id).delete()
    db.query(ArticleTag).filter(ArticleTag.article_id == article_id).delete()
    db.query(UserInteraction).filter(UserInteraction.article_id == article_id).delete()

    db.delete(article)
    db.commit()

    return {"message": "Article deleted successfully"}

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

    return tag.tag_name, articles, total_articles, total_pages

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

    return author.user_name, articles, total_articles, total_pages

def update_article(
    db: Session,
    article_id: int,
    user_id: int,
    data: ArticleUpdateRequest
):
    try:
        # 1. Fetch article
        article = db.query(Article).filter(Article.article_id == article_id).first()
        if not article:
            return None

        # 2. AUTHORIZATION CHECK
        if article.author_id != user_id:
            raise PermissionError("Not your article")

        # 3. Update fields
        article.title = data.title
        article.content = data.content
        article.updated_at = datetime.utcnow()

        # 4. Remove old tags
        db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id
        ).delete()

        tag_objects = []

        # 5. Recreate tags
        for tag_name in data.tag_names:
            tag_name = tag_name.strip().lower()

            tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()
            if not tag:
                tag = Tag(tag_name=tag_name)
                db.add(tag)
                db.flush()

            tag_objects.append(tag)

        # 6. Recreate article-tag links
        for tag in tag_objects:
            link = ArticleTag(
                article_id=article.article_id,
                tag_id=tag.tag_id
            )
            db.add(link)

        # 7. Delete old vectors
        db.query(ArticleVector).filter(
            ArticleVector.article_id == article.article_id
        ).delete()

        # 8. Recompute vectors
        create_article_vector(db, article.article_id)

        # ✅ SINGLE COMMIT at the end
        db.commit()
        db.refresh(article)

        return article, [t.tag_name for t in tag_objects]

    except PermissionError:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise e
