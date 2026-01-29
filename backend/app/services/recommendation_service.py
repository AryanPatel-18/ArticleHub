import json
import math
from collections import defaultdict
from sqlalchemy.orm import Session
from models import ArticleVector, Article, UserInteraction, User
from models.user_model import UserRecommendationCache
from models.vector_model import UserVector
from schemas.article_schema import ArticleRecommendationResponse, PaginatedArticleRecommendationResponse
from services.user_vector_service import recompute_user_vector_from_interactions

INTERACTION_WEIGHTS = {
    "view": 1.0,
    "like": 2.0,
    "save": 3.0
}

def cosine_sparse(v1, v2):
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0

    for idx, val in v1.items():
        norm1 += val * val
        if idx in v2:
            dot += val * v2[idx]

    for val in v2.values():
        norm2 += val * val

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


def dict_from_sparse(vec_json):
    vec = json.loads(vec_json)
    return dict(zip(vec["indices"], vec["values"]))


def build_user_vector_from_interactions(db: Session, user_id: int):
    interactions = (
        db.query(UserInteraction.article_id, UserInteraction.interaction_type)
        .filter(UserInteraction.user_id == user_id)
        .all()
    )

    if not interactions:
        return {}, {}

    weighted_text_vec = defaultdict(float)
    weighted_tag_vec = defaultdict(float)
    total_weight = 0.0

    article_ids = [i.article_id for i in interactions]
    vectors = (
        db.query(ArticleVector)
        .filter(ArticleVector.article_id.in_(article_ids))
        .all()
    )

    vector_map = {v.article_id: v for v in vectors}

    for interaction in interactions:
        av = vector_map.get(interaction.article_id)
        if not av:
            continue

        weight = INTERACTION_WEIGHTS.get(interaction.interaction_type, 1.0)

        text_vec = dict_from_sparse(av.text_vector)
        tag_vec = dict_from_sparse(av.tag_vector)

        for k, v in text_vec.items():
            weighted_text_vec[k] += weight * v

        for k, v in tag_vec.items():
            weighted_tag_vec[k] += weight * v

        total_weight += weight

    if total_weight == 0:
        return {}, {}

    for k in weighted_text_vec:
        weighted_text_vec[k] /= total_weight

    for k in weighted_tag_vec:
        weighted_tag_vec[k] /= total_weight

    return dict(weighted_text_vec), dict(weighted_tag_vec)


def get_top_articles_for_user(
    db: Session,
    user_id: int,
    session_id: str,
    page: int = 1,
    page_size: int = 5
):
    # 0. Load user vector
    user_vec_row = (
        db.query(UserVector)
        .filter(UserVector.user_id == user_id)
        .first()
    )

    if not user_vec_row:
        return PaginatedArticleRecommendationResponse(
            page=page,
            page_size=page_size,
            total_results=0,
            total_pages=0,
            articles=[]
        )

    # 🔑 dirty check (lazy recompute)
    if user_vec_row.last_updated is None:
        recompute_user_vector_from_interactions(db, user_id)

        # reload after recompute
        user_vec_row = (
            db.query(UserVector)
            .filter(UserVector.user_id == user_id)
            .first()
        )

    # ✅ USE STORED USER VECTOR (not interactions)
    user_text_vec = dict_from_sparse(user_vec_row.text_vector)
    user_tag_vec = dict_from_sparse(user_vec_row.tag_vector)

    if not user_text_vec and not user_tag_vec:
        return PaginatedArticleRecommendationResponse(
            page=page,
            page_size=page_size,
            total_results=0,
            total_pages=0,
            articles=[]
        )

    # 1. Clear old sessions
    db.query(UserRecommendationCache).filter(
        UserRecommendationCache.user_id == user_id,
        UserRecommendationCache.session_id != session_id
    ).delete()
    db.commit()

    cached_count = db.query(UserRecommendationCache).filter(
        UserRecommendationCache.user_id == user_id,
        UserRecommendationCache.session_id == session_id
    ).count()

    if cached_count == 0:
        # Exclude liked/saved articles
        seen_articles = {
            row.article_id
            for row in db.query(UserInteraction.article_id)
            .filter(UserInteraction.user_id == user_id)
            .filter(UserInteraction.interaction_type.in_(["like", "save"]))
            .all()
        }

        article_vectors = db.query(ArticleVector).limit(1000).all()
        scored = []

        for av in article_vectors:
            if av.article_id in seen_articles:
                continue

            article_text_vec = dict_from_sparse(av.text_vector)
            article_tag_vec = dict_from_sparse(av.tag_vector)

            text_score = cosine_sparse(user_text_vec, article_text_vec)
            tag_score = cosine_sparse(user_tag_vec, article_tag_vec)

            score = 0.7 * text_score + 0.3 * tag_score
            scored.append((av.article_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        for pos, (article_id, _) in enumerate(scored):
            db.add(
                UserRecommendationCache(
                    user_id=user_id,
                    article_id=article_id,
                    rank_position=pos,
                    session_id=session_id
                )
            )
        db.commit()

    total_results = db.query(UserRecommendationCache).filter(
        UserRecommendationCache.user_id == user_id,
        UserRecommendationCache.session_id == session_id
    ).count()

    total_pages = math.ceil(total_results / page_size) if total_results > 0 else 0

    rows = (
        db.query(UserRecommendationCache)
        .filter(
            UserRecommendationCache.user_id == user_id,
            UserRecommendationCache.session_id == session_id
        )
        .order_by(UserRecommendationCache.rank_position)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    if not rows:
        return PaginatedArticleRecommendationResponse(
            page=page,
            page_size=page_size,
            total_results=total_results,
            total_pages=total_pages,
            articles=[]
        )

    article_ids = [row.article_id for row in rows]

    articles = (
        db.query(Article, User.user_name)
        .join(User, Article.author_id == User.user_id)
        .filter(Article.article_id.in_(article_ids))
        .all()
    )

    article_map = {
        article.article_id: (article, username)
        for article, username in articles
    }

    result = []
    for aid in article_ids:
        article, username = article_map[aid]
        result.append(
            ArticleRecommendationResponse(
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                author_username=username,
                created_at=article.created_at
            )
        )

    return PaginatedArticleRecommendationResponse(
        page=page,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        articles=result
    )
