from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_model import User
from app.models.article_model import Article, ArticleTag, ArticleStat, Tag
from app.models.interaction_model import UserInteraction
from app.models.vector_model import ArticleVector, UserVector
from app.models.user_model import UserRecommendationCache
from app.models.admin_model import AdminActionLog
from app.core.logger import get_logger

logger = get_logger(__name__)



def admin_delete_tag(
    db: Session,
    tag_id: int,
    admin_user_id: int,
    reason: str
):
    try:
        logger.info(f"Admin {admin_user_id} deleting tag {tag_id}")

        admin = db.query(User).filter(
            User.user_id == admin_user_id
        ).first()

        if not admin or admin.user_role != "admin":
            raise HTTPException(status_code=401, detail="Admin required")

        tag = db.query(Tag).filter(Tag.tag_id == tag_id).first()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        log_entry = AdminActionLog(
            admin_user_id=admin.user_id,
            action_type="DELETE",
            target_type="TAG",
            target_id=tag.tag_id,
            target_snapshot=tag.tag_name,
            reason=reason
        )
        db.add(log_entry)

        db.query(ArticleTag).filter(
            ArticleTag.tag_id == tag_id
        ).delete()

        db.delete(tag)
        db.commit()

        logger.info(
            f"Tag {tag_id} deleted by admin {admin_user_id} | reason={reason}"
        )

        return log_entry

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Tag deletion failed")
        raise



def admin_delete_article(
    db: Session,
    article_id: int,
    admin_user_id: int,
    reason: str
):
    try:
        logger.info(
            f"Admin {admin_user_id} requested deletion of article {article_id}"
        )

        admin = db.query(User).filter(
            User.user_id == admin_user_id
        ).first()

        if not admin or admin.user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin privileges required"
            )

        article = db.query(Article).filter(
            Article.article_id == article_id
        ).first()

        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        log_entry = AdminActionLog(
            admin_user_id=admin.user_id,
            action_type="DELETE",
            target_type="ARTICLE",
            target_id=article.article_id,
            target_snapshot=article.title,
            reason=reason
        )
        db.add(log_entry)

        db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id
        ).delete()

        db.query(UserInteraction).filter(
            UserInteraction.article_id == article_id
        ).delete()

        db.query(ArticleVector).filter(
            ArticleVector.article_id == article_id
        ).delete()

        db.query(ArticleStat).filter(
            ArticleStat.article_id == article_id
        ).delete()

        db.query(UserRecommendationCache).filter(
            UserRecommendationCache.article_id == article_id
        ).delete()

        db.delete(article)
        db.commit()

        logger.info(
            f"Article {article_id} deleted by admin {admin_user_id}"
        )

        return log_entry

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during article deletion")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception:
        db.rollback()
        logger.exception("Unexpected error during article deletion")
        raise HTTPException(status_code=500, detail="Unexpected error")


def admin_delete_user(
    db: Session,
    target_user_id: int,
    admin_user_id: int,
    reason: str
):
    try:
        logger.info(
            f"Admin {admin_user_id} requested deletion of user {target_user_id}"
        )

        admin = db.query(User).filter(
            User.user_id == admin_user_id
        ).first()

        if not admin or admin.user_role != "admin":
            raise HTTPException(status_code=401, detail="Admin required")

        if target_user_id == admin_user_id:
            raise HTTPException(status_code=400, detail="Admin cannot delete self")

        user = db.query(User).filter(
            User.user_id == target_user_id
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        log_entry = AdminActionLog(
            admin_user_id=admin.user_id,
            action_type="DELETE",
            target_type="USER",
            target_id=user.user_id,
            target_snapshot=user.user_name,
            reason=reason
        )
        db.add(log_entry)

        
        user_article_ids = [
            a.article_id for a in db.query(Article.article_id)
            .filter(Article.author_id == target_user_id)
            .all()
        ]

        if user_article_ids:
            db.query(ArticleTag).filter(
                ArticleTag.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

            db.query(UserInteraction).filter(
                UserInteraction.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

            db.query(ArticleVector).filter(
                ArticleVector.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

            db.query(ArticleStat).filter(
                ArticleStat.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

            db.query(UserRecommendationCache).filter(
                UserRecommendationCache.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

            db.query(Article).filter(
                Article.article_id.in_(user_article_ids)
            ).delete(synchronize_session=False)

       
        db.query(UserInteraction).filter(
            UserInteraction.user_id == target_user_id
        ).delete(synchronize_session=False)

        db.query(UserVector).filter(
            UserVector.user_id == target_user_id
        ).delete(synchronize_session=False)

        db.query(UserRecommendationCache).filter(
            UserRecommendationCache.user_id == target_user_id
        ).delete(synchronize_session=False)

        db.delete(user)
        db.commit()

        logger.info(
            f"User {target_user_id} deleted by admin {admin_user_id}"
        )

        return log_entry

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during user deletion")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception:
        db.rollback()
        logger.exception("Unexpected error during user deletion")
        raise HTTPException(status_code=500, detail="Unexpected error")
