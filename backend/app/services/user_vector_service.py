import json
from collections import defaultdict
from sqlalchemy.orm import Session
from models.vector_model import UserVector
from models.article_model import ArticleStat
from models.vector_model import ArticleVector
from models.interaction_model import UserInteraction
from datetime import datetime

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
    """
    Build default user vector from most popular articles.
    Popularity = view + 2*like + 3*save
    V_user = Σ(popularity * V_article) / Σ(popularity)
    """

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
        return  # no articles exist yet

    text_accumulator = defaultdict(float)
    tag_accumulator = defaultdict(float)
    total_weight = 0.0

    for av, stats in rows:
        weight = (
            stats.view_count +
            2 * stats.like_count +
            3 * stats.save_count
        )

        # skip useless articles
        if weight <= 0:
            continue

        text_vec = dict_from_sparse(av.text_vector)
        tag_vec = dict_from_sparse(av.tag_vector)

        for k, v in text_vec.items():
            text_accumulator[k] += weight * v

        for k, v in tag_vec.items():
            tag_accumulator[k] += weight * v

        total_weight += weight

    # If all articles had zero stats, abort safely
    if total_weight == 0:
        return

    # Normalize
    for k in text_accumulator:
        text_accumulator[k] /= total_weight

    for k in tag_accumulator:
        tag_accumulator[k] /= total_weight

    # Upsert
    existing = (
        db.query(UserVector)
        .filter(UserVector.user_id == user_id)
        .first()
    )

    if existing:
        existing.text_vector = sparse_to_json(text_accumulator)
        existing.tag_vector = sparse_to_json(tag_accumulator)
    else:
        db.add(UserVector(
            user_id=user_id,
            text_vector=sparse_to_json(text_accumulator),
            tag_vector=sparse_to_json(tag_accumulator)
        ))

    db.commit()


def recompute_user_vector_from_interactions(db: Session, user_id: int):

    interactions = (
        db.query(UserInteraction.article_id, UserInteraction.interaction_type)
        .filter(UserInteraction.user_id == user_id)
        .filter(UserInteraction.interaction_type.in_(["like", "save"]))
        .all()
    )

    # No signal → do not change vector (keep default)
    if not interactions:
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
        return

    # Normalize
    for k in text_accumulator:
        text_accumulator[k] /= total_weight

    for k in tag_accumulator:
        tag_accumulator[k] /= total_weight

    text_json = sparse_to_json(text_accumulator)
    tag_json = sparse_to_json(tag_accumulator)

    # Update user_vectors table
    user_vec = (
        db.query(UserVector)
        .filter(UserVector.user_id == user_id)
        .first()
    )

    if user_vec:
        user_vec.text_vector = text_json
        user_vec.tag_vector = tag_json
        user_vec.last_updated = datetime.utcnow()
    else:
        db.add(UserVector(
            user_id=user_id,
            text_vector=text_json,
            tag_vector=tag_json,
            last_updated=datetime.utcnow()
        ))

    db.commit()


def mark_user_vector_dirty(db: Session, user_id: int):

    user_vec = (
        db.query(UserVector)
        .filter(UserVector.user_id == user_id)
        .first()
    )

    if user_vec:
        user_vec.last_updated = None
        db.commit()