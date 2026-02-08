from database.db import SessionLocal
from services.article_vector_service import create_article_vector


def create_article_vector_background(article_id: int):
    db = SessionLocal()

    try:
        create_article_vector(db, article_id)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[VECTOR JOB FAILED] article_id={article_id} error={e}")
    finally:
        db.close()
