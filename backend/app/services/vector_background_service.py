from app.database.db import SessionLocal
from app.services.article_vector_service import create_article_vector
from app.core.logger import get_logger
logger = get_logger(__name__)

"""
    Recomputing the vectors takes a lot of time since TF-IDF is being used for vectors so all the services related to vector generation is done in the background to allow the user to browse the rest of the website without any performance issues. This file contains the functions that are used to create the article vectors and also to recompute the user vectors when the user interacts with an article. These functions are called in the background using Celery workers to avoid any performance issues for the user.
"""
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