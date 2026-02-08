from database.db import SessionLocal
from services.article_vector_service import create_article_vector
from core.logger import get_logger
logger = get_logger(__name__)


def create_article_vector_background(article_id: int):
    logger.info(f"vector_background_job_start article_id={article_id}")

    db = SessionLocal()

    try:
        create_article_vector(db, article_id)
        db.commit()

        logger.info(f"vector_background_job_complete article_id={article_id}")

    except Exception:
        db.rollback()
        logger.exception(
            f"vector_background_job_failed article_id={article_id}"
        )

    finally:
        db.close()