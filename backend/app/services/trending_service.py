from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.interaction_model import UserInteraction
from app.models.article_model import Article, Tag, ArticleTag
from app.models.user_model import User
from app.core.logger import get_logger
logger = get_logger(__name__)



def get_trending_articles(db: Session, days: int = 7, limit: int = 50):
    logger.info(f"trending_articles_start days={days} limit={limit}")

    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        score_expr = func.sum(
            case(
                (UserInteraction.interaction_type == "view", 1),
                (UserInteraction.interaction_type == "like", 2),
                (UserInteraction.interaction_type == "save", 3),
                else_=0
            )
        ).label("trend_score")

        results = (
            db.query(
                UserInteraction.article_id,
                score_expr
            )
            .join(Article, Article.article_id == UserInteraction.article_id)
            .filter(UserInteraction.created_at >= cutoff)
            .filter(Article.is_published)
            .group_by(UserInteraction.article_id)
            .order_by(score_expr.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"trending_articles_loaded count={len(results)}")

        return results

    except Exception:
        logger.exception("trending_articles_failed")
        raise



def get_trending_tags(db: Session, days: int = 7, limit: int = 10):
    logger.info(f"trending_tags_start days={days}")

    try:
        trending_articles = get_trending_articles(db, days=days, limit=100)

        article_ids = [row.article_id for row in trending_articles]

        if not article_ids:
            logger.warning("trending_tags_no_articles")
            return []

        tag_counts = (
            db.query(
                Tag.tag_id,
                Tag.tag_name,
                func.count(ArticleTag.article_id).label("count")
            )
            .join(ArticleTag, ArticleTag.tag_id == Tag.tag_id)
            .filter(ArticleTag.article_id.in_(article_ids))
            .group_by(Tag.tag_id, Tag.tag_name)
            .order_by(func.count(ArticleTag.article_id).desc())
            .limit(limit)
            .all()
        )

        logger.info(f"trending_tags_loaded count={len(tag_counts)}")

        return tag_counts

    except Exception:
        logger.exception("trending_tags_failed")
        raise



def get_trending_authors(db: Session, days: int = 7, limit: int = 10):
    logger.info(f"trending_authors_start days={days}")

    try:
        trending_articles = get_trending_articles(db, days=days, limit=100)

        article_ids = [row.article_id for row in trending_articles]

        if not article_ids:
            logger.warning("trending_authors_no_articles")
            return []

        author_counts = (
            db.query(
                User.user_id,
                User.user_name,
                func.count(Article.article_id).label("count")
            )
            .join(Article, Article.author_id == User.user_id)
            .filter(Article.article_id.in_(article_ids))
            .group_by(User.user_id, User.user_name)
            .order_by(func.count(Article.article_id).desc())
            .limit(limit)
            .all()
        )

        logger.info(f"trending_authors_loaded count={len(author_counts)}")

        return author_counts

    except Exception:
        logger.exception("trending_authors_failed")
        raise
