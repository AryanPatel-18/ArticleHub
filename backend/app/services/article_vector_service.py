import json
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from collections import Counter
from models.article_model import Article, ArticleTag, Tag
from models.vector_model import ArticleVector
from core.logger import get_logger
logger = get_logger(__name__)


def create_article_vector(db: Session, article_id: int):
    """
    Recompute TF-IDF using ALL articles,
    then store vector ONLY for the given article_id.
    """

    logger.info(f"vector_recompute_start article_id={article_id}")

    try:
        # 1. Fetch all articles
        articles = db.query(Article).all()

        if not articles:
            logger.warning("vector_recompute_skipped no_articles_exist")
            return

        article_ids = []
        texts = []

        for article in articles:
            article_ids.append(article.article_id)
            texts.append(article.content)

        logger.info(f"vector_corpus_loaded size={len(article_ids)}")

        # 2. Fetch tags
        rows = (
            db.query(ArticleTag.article_id, Tag.tag_name)
            .join(Tag, ArticleTag.tag_id == Tag.tag_id)
            .all()
        )

        tag_map = {}
        for aid, tag_name in rows:
            tag_map.setdefault(aid, []).append(tag_name)

        tag_texts = []
        for aid in article_ids:
            tag_texts.append(" ".join(tag_map.get(aid, [])))

        # 3. Fit TF-IDF
        text_vectorizer = TfidfVectorizer(stop_words="english", max_features=50000)
        tag_vectorizer = TfidfVectorizer()

        text_vectors = text_vectorizer.fit_transform(texts)
        tag_vectors = tag_vectorizer.fit_transform(tag_texts)

        logger.info("tfidf_fit_complete")

        # 4. Target article index
        target_index = article_ids.index(article_id)

        text_row = text_vectors[target_index]
        tag_row = tag_vectors[target_index]

        text_vector_json = {
            "indices": text_row.indices.tolist(),
            "values": text_row.data.tolist()
        }

        tag_vector_json = {
            "indices": tag_row.indices.tolist(),
            "values": tag_row.data.tolist()
        }

        vector = ArticleVector(
            article_id=article_id,
            text_vector=json.dumps(text_vector_json),
            tag_vector=json.dumps(tag_vector_json),
            vector_version=1
        )

        db.add(vector)
        db.commit()

        logger.info(f"article_vector_created article_id={article_id}")

    except Exception:
        db.rollback()
        logger.exception(f"vector_recompute_failed article_id={article_id}")
        raise


TOKEN_PATTERN = re.compile(r"\b[a-zA-Z]{2,}\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_query_vector(db: Session, query: str) -> dict:
    """
    Builds a TF-IDF sparse vector for a search query.
    """

    logger.info("query_vector_build_start")

    try:
        sample_vector = (
            db.query(ArticleVector)
            .order_by(ArticleVector.vector_version.desc())
            .first()
        )

        if not sample_vector:
            logger.error("query_vector_build_failed no_article_vectors")
            raise RuntimeError("No article vectors exist. Cannot build query vector.")

        vocab = sample_vector.text_vector["vocabulary"]
        idf = sample_vector.text_vector["idf"]

        tokens = tokenize(query)
        if not tokens:
            logger.warning("query_vector_empty_query")
            return {"indices": [], "values": []}

        term_counts = Counter(tokens)
        total_terms = sum(term_counts.values())

        indices = []
        values = []

        for term, count in term_counts.items():
            if term not in vocab:
                continue

            idx = vocab[term]
            tf = count / total_terms
            tf_idf = tf * idf[idx]

            indices.append(idx)
            values.append(tf_idf)

        logger.info(f"query_vector_built terms={len(indices)}")

        return {
            "indices": indices,
            "values": values
        }

    except Exception:
        logger.exception("query_vector_build_failed")
        raise
