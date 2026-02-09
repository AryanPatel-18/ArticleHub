import json
import pickle
from sqlalchemy.orm import Session
import re
# from collections import Counter
from pathlib import Path

from app.models.article_model import Article, ArticleTag, Tag
from app.models.vector_model import ArticleVector
from app.core.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path("model_store")
TEXT_MODEL_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
TAG_MODEL_PATH = MODEL_DIR / "tag_vectorizer.pkl"

_text_vectorizer = None
_tag_vectorizer = None


def load_vectorizers():
    global _text_vectorizer, _tag_vectorizer

    if _text_vectorizer is None:
        with open(TEXT_MODEL_PATH, "rb") as f:
            _text_vectorizer = pickle.load(f)

    if _tag_vectorizer is None:
        with open(TAG_MODEL_PATH, "rb") as f:
            _tag_vectorizer = pickle.load(f)

    return _text_vectorizer, _tag_vectorizer


def create_article_vector(db: Session, article_id: int):
    logger.info(f"vector_recompute_start article_id={article_id}")

    try:
        text_vectorizer, tag_vectorizer = load_vectorizers()

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


TOKEN_PATTERN = re.compile(r"\b[a-zA-Z]{2,}\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_query_vector(db: Session, query: str) -> dict:
    logger.info("query_vector_build_start")

    try:
        text_vectorizer, _ = load_vectorizers()

        vec = text_vectorizer.transform([query])[0]

        return {
            "indices": vec.indices.tolist(),
            "values": vec.data.tolist(),
        }

    except Exception:
        logger.exception("query_vector_build_failed")
        raise
