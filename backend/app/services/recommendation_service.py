import json
import math
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models import ArticleVector, Article, UserInteraction, User
from app.models.user_model import UserRecommendationCache
from app.models.vector_model import UserVector
from app.schemas.article_schema import ArticleRecommendationResponse, PaginatedArticleRecommendationResponse
from app.services.user_vector_service import recompute_user_vector_from_interactions
from app.core.logger import get_logger
logger = get_logger(__name__)

# Weights that are used for the recommendation vectors
INTERACTION_WEIGHTS = {
    "view": 1.0,
    "like": 2.0,
    "save": 3.0
}

# For finding the relation between two sparse vectors
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

# Converts the sparse vector stored in json format back to a dictionary format for easier manipulation.
def dict_from_sparse(vec_json):
    vec = json.loads(vec_json)
    return dict(zip(vec["indices"], vec["values"]))

# Main function to get the top recommended articles for a user. The function first checks if the user has a vector, if not it triggers a lazy recomputation of the user vector based on the user's interactions. Then it checks if there is a cache of recommendations for the user and session, if not it builds the cache by scoring all articles against the user vector and storing the top recommendations in the UserRecommendationCache table.
def build_user_vector_from_interactions(db: Session, user_id: int):
    logger.info(f"user_vector_build_start user_id={user_id}")

    interactions = (
        db.query(UserInteraction.article_id, UserInteraction.interaction_type)
        .filter(UserInteraction.user_id == user_id)
        .all()
    )

    if not interactions:
        logger.warning(f"user_vector_empty user_id={user_id}")
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
            logger.warning(
                f"user_vector_missing_article_vector article_id={interaction.article_id}"
            )
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
        logger.warning(f"user_vector_zero_weight user_id={user_id}")
        return {}, {}

    for k in weighted_text_vec:
        weighted_text_vec[k] /= total_weight

    for k in weighted_tag_vec:
        weighted_tag_vec[k] /= total_weight

    logger.info(
        f"user_vector_built user_id={user_id} "
        f"text_dims={len(weighted_text_vec)} tag_dims={len(weighted_tag_vec)}"
    )

    return dict(weighted_text_vec), dict(weighted_tag_vec)


# Retrieves the top recommended articles for a user based on their user vector and the article vectors. The function also implements pagination and caching of recommendations for performance optimization.
def get_top_articles_for_user(
    db: Session,
    user_id: int,
    session_id: str,
    page: int = 1,
    page_size: int = 5
):
    session_id = str(session_id)  # ← ensures DB type consistency

    logger.info(
        f"recommendation_request_start user_id={user_id} session_id={session_id}"
    )

    try:
        user_vec_row = (
            db.query(UserVector)
            .filter(UserVector.user_id == user_id)
            .first()
        )

        if not user_vec_row:
            logger.warning(f"recommendation_no_user_vector user_id={user_id}")
            return PaginatedArticleRecommendationResponse(
                page=page,
                page_size=page_size,
                total_results=0,
                total_pages=0,
                articles=[]
            )

        if user_vec_row.last_updated is None:
            logger.info(f"user_vector_lazy_recompute user_id={user_id}")
            recompute_user_vector_from_interactions(db, user_id)

            user_vec_row = (
                db.query(UserVector)
                .filter(UserVector.user_id == user_id)
                .first()
            )

        user_text_vec = dict_from_sparse(user_vec_row.text_vector)
        user_tag_vec = dict_from_sparse(user_vec_row.tag_vector)

        if not user_text_vec and not user_tag_vec:
            logger.warning(f"recommendation_empty_user_vector user_id={user_id}")
            return PaginatedArticleRecommendationResponse(
                page=page,
                page_size=page_size,
                total_results=0,
                total_pages=0,
                articles=[]
            )

        # ---- CACHE CLEANUP (safe string comparison) ----
        db.query(UserRecommendationCache).filter(
            UserRecommendationCache.user_id == user_id,
            UserRecommendationCache.session_id != session_id
        ).delete(synchronize_session=False)

        db.commit()
        logger.info(f"recommendation_cache_cleanup user_id={user_id}")

        cached_count = db.query(UserRecommendationCache).filter(
            UserRecommendationCache.user_id == user_id,
            UserRecommendationCache.session_id == session_id
        ).count()

        # ---- BUILD CACHE IF EMPTY ----
        if cached_count == 0:
            logger.info(f"recommendation_cache_build user_id={user_id}")

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

            logger.info(
                f"recommendation_scoring_complete user_id={user_id} "
                f"candidates={len(scored)}"
            )

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

        else:
            logger.info(f"recommendation_cache_hit user_id={user_id}")

        # ---- PAGINATION ----
        total_results = db.query(UserRecommendationCache).filter(
            UserRecommendationCache.user_id == user_id,
            UserRecommendationCache.session_id == session_id
        ).count()

        total_pages = (
            math.ceil(total_results / page_size)
            if total_results > 0 else 0
        )

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
            logger.info(f"recommendation_no_rows user_id={user_id}")
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

        logger.info(
            f"recommendation_page_served user_id={user_id} "
            f"page={page} results={len(result)}"
        )

        return PaginatedArticleRecommendationResponse(
            page=page,
            page_size=page_size,
            total_results=total_results,
            total_pages=total_pages,
            articles=result
        )

    except Exception:
        logger.exception(
            f"recommendation_failed user_id={user_id} session_id={session_id}"
        )
        raise

