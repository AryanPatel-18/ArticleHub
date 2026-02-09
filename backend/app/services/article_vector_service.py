import json
import re
from sqlalchemy.orm import Session

from app.models.article_model import Article, ArticleTag, Tag
from app.models.vector_model import ArticleVector
from app.core.logger import get_logger
from app.ml.tfidf_model_loader import get_vectorizers

logger = get_logger(__name__)

TOKEN_PATTERN = re.compile(r"\b[a-zA-Z]{2,}\b")


def create_article_vector(db: Session, article_id: int):
    logger.info(f"vector_recompute_start article_id={article_id}")

    try:
        text_vectorizer, tag_vectorizer = get_vectorizers()

        article = (
            db.query(Article)
            .filter(Article.article_id == article_id)
            .first()
        )

        if not article:
            logger.warning(f"article_not_found article_id={article_id}")
            return

        # -----------------------
        # TEXT VECTOR
        # -----------------------
        text = (article.content or "")[:5000]
        text_vector = text_vectorizer.transform([text])[0]

        text_vector_json = {
            "indices": text_vector.indices.tolist(),
            "values": text_vector.data.tolist(),
        }

        # -----------------------
        # TAG VECTOR
        # -----------------------
        rows = (
            db.query(Tag.tag_name)
            .join(ArticleTag, ArticleTag.tag_id == Tag.tag_id)
            .filter(ArticleTag.article_id == article_id)
            .all()
        )

        tag_text = " ".join([r[0] for r in rows])
        tag_vector = tag_vectorizer.transform([tag_text])[0]

        tag_vector_json = {
            "indices": tag_vector.indices.tolist(),
            "values": tag_vector.data.tolist(),
        }

        existing_vector = (
            db.query(ArticleVector)
            .filter(ArticleVector.article_id == article_id)
            .first()
        )

        if existing_vector:
            existing_vector.text_vector = json.dumps(text_vector_json)
            existing_vector.tag_vector = json.dumps(tag_vector_json)
            existing_vector.vector_version += 1
            logger.info(f"article_vector_updated article_id={article_id}")
        else:
            db.add(
                ArticleVector(
                    article_id=article_id,
                    text_vector=json.dumps(text_vector_json),
                    tag_vector=json.dumps(tag_vector_json),
                    vector_version=1
                )
            )
            logger.info(f"article_vector_created article_id={article_id}")

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(f"vector_recompute_failed article_id={article_id}")
        raise


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_query_vector(db: Session, query: str) -> dict:
    logger.info("query_vector_build_start")

    try:
        text_vectorizer, _ = get_vectorizers()

        vec = text_vectorizer.transform([query])[0]

        return {
            "indices": vec.indices.tolist(),
            "values": vec.data.tolist(),
        }

    except Exception:
        logger.exception("query_vector_build_failed")
        raise
