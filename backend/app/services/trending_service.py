from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models.interaction_model import UserInteraction
from models.article_model import Article, Tag, ArticleTag
from models.user_model import User

def get_trending_articles(db: Session, days: int = 7, limit: int = 50):
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

    return results


def get_trending_tags(db: Session, days: int = 7, limit: int = 10):
    trending_articles = get_trending_articles(db, days=days, limit=100)

    article_ids = [row.article_id for row in trending_articles]

    if not article_ids:
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

    return tag_counts


def get_trending_authors(db: Session, days: int = 7, limit: int = 10):
    trending_articles = get_trending_articles(db, days=days, limit=100)

    article_ids = [row.article_id for row in trending_articles]

    if not article_ids:
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

    return author_counts