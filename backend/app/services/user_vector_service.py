import json
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.vector_model import UserVector
from app.models.article_model import ArticleStat
from app.models.vector_model import ArticleVector
from app.models.interaction_model import UserInteraction
from datetime import datetime
from app.core.logger import get_logger
logger = get_logger(__name__)


INTERACTION_WEIGHTS = {
    "like": 2.0,
    "save": 3.0
}

def dict_from_sparse(vec_json: str) -> dict:
    data = json.loads(vec_json)
    return dict(zip(data["indices"], data["values"]))


def sparse_to_json(vec: dict) -> str:
    return json.dumps({
        "indices": list(vec.keys()),
        "values": list(vec.values())
    })


def create_default_user_vector(db: Session, user_id: int, top_n: int = 20):
    logger.info(f"default_user_vector_build_start user_id={user_id}")

    try:
        rows = (
            db.query(ArticleVector, ArticleStat)
            .join(ArticleStat, ArticleVector.article_id == ArticleStat.article_id)
            .order_by(
                (ArticleStat.view_count +
                 2 * ArticleStat.like_count +
                 3 * ArticleStat.save_count).desc()
            )
            .limit(top_n)
            .all()
        )

        if not rows:
            logger.warning("default_user_vector_no_articles")
            return

        text_accumulator = defaultdict(float)
        tag_accumulator = defaultdict(float)
        total_weight = 0.0

        for av, stats in rows:
            weight = (
                stats.view_count +
                2 * stats.like_count +
                3 * stats.save_count
            )

            if weight <= 0:
                continue

            text_vec = dict_from_sparse(av.text_vector)
            tag_vec = dict_from_sparse(av.tag_vector)

            for k, v in text_vec.items():
                text_accumulator[k] += weight * v

            for k, v in tag_vec.items():
                tag_accumulator[k] += weight * v

            total_weight += weight

        if total_weight == 0:
            logger.warning("default_user_vector_zero_weight")
            return

        for k in text_accumulator:
            text_accumulator[k] /= total_weight

        for k in tag_accumulator:
            tag_accumulator[k] /= total_weight

        existing = (
            db.query(UserVector)
            .filter(UserVector.user_id == user_id)
            .first()
        )

        if existing:
            existing.text_vector = sparse_to_json(text_accumulator)
            existing.tag_vector = sparse_to_json(tag_accumulator)
            logger.info(f"default_user_vector_updated user_id={user_id}")
        else:
            db.add(UserVector(
                user_id=user_id,
                text_vector=sparse_to_json(text_accumulator),
                tag_vector=sparse_to_json(tag_accumulator)
            ))
            logger.info(f"default_user_vector_created user_id={user_id}")

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(f"default_user_vector_failed user_id={user_id}")
        raise



def recompute_user_vector_from_interactions(db: Session, user_id: int):
    logger.info(f"user_vector_recompute_start user_id={user_id}")

    try:
        interactions = (
            db.query(UserInteraction.article_id, UserInteraction.interaction_type)
            .filter(UserInteraction.user_id == user_id)
            .filter(UserInteraction.interaction_type.in_(["like", "save"]))
            .all()
        )

        if not interactions:
            logger.warning(f"user_vector_recompute_no_interactions user_id={user_id}")
            return

        article_ids = [i.article_id for i in interactions]

        article_vectors = (
            db.query(ArticleVector)
            .filter(ArticleVector.article_id.in_(article_ids))
            .all()
        )

        vector_map = {v.article_id: v for v in article_vectors}

        text_accumulator = defaultdict(float)
        tag_accumulator = defaultdict(float)
        total_weight = 0.0

        for article_id, interaction_type in interactions:
            av = vector_map.get(article_id)
            if not av:
                logger.warning(f"user_vector_missing_article_vector article_id={article_id}")
                continue

            weight = INTERACTION_WEIGHTS[interaction_type]

            text_vec = dict_from_sparse(av.text_vector)
            tag_vec = dict_from_sparse(av.tag_vector)

            for k, v in text_vec.items():
                text_accumulator[k] += weight * v

            for k, v in tag_vec.items():
                tag_accumulator[k] += weight * v

            total_weight += weight

        if total_weight == 0:
            logger.warning(f"user_vector_recompute_zero_weight user_id={user_id}")
            return

        for k in text_accumulator:
            text_accumulator[k] /= total_weight

        for k in tag_accumulator:
            tag_accumulator[k] /= total_weight

        text_json = sparse_to_json(text_accumulator)
        tag_json = sparse_to_json(tag_accumulator)

        user_vec = (
            db.query(UserVector)
            .filter(UserVector.user_id == user_id)
            .first()
        )

        if user_vec:
            user_vec.text_vector = text_json
            user_vec.tag_vector = tag_json
            user_vec.last_updated = datetime.utcnow()
            logger.info(f"user_vector_updated user_id={user_id}")
        else:
            db.add(UserVector(
                user_id=user_id,
                text_vector=text_json,
                tag_vector=tag_json,
                last_updated=datetime.utcnow()
            ))
            logger.info(f"user_vector_created user_id={user_id}")

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(f"user_vector_recompute_failed user_id={user_id}")
        raise



def mark_user_vector_dirty(db: Session, user_id: int):
    try:
        user_vec = (
            db.query(UserVector)
            .filter(UserVector.user_id == user_id)
            .first()
        )

        if user_vec:
            user_vec.last_updated = None
            db.commit()
            logger.info(f"user_vector_marked_dirty user_id={user_id}")

    except Exception:
        db.rollback()
        logger.exception(f"user_vector_dirty_failed user_id={user_id}")
        raise
