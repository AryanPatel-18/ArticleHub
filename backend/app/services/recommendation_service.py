import json
import math
from sqlalchemy.orm import Session
from models import ArticleVector, UserVector, Article, UserInteraction, User
from schemas.article_schema import ArticleRecommendationResponse

def cosine_sparse(v1, v2):
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0

    for idx, val in v1.items():
        norm1 += val * val
        if idx in v2:
            dot += val * v2[idx] * val

    for val in v2.values():
        norm2 += val * val

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


def dict_from_sparse(vec_json):
    vec = json.loads(vec_json)
    return dict(zip(vec["indices"], vec["values"]))


def get_top_articles_for_user(db: Session, user_id: int, limit: int = 5):
    user_vec_row = db.query(UserVector).filter(UserVector.user_id == user_id).first()
    if not user_vec_row:
        return []

    user_text_vec = dict_from_sparse(user_vec_row.text_vector)
    user_tag_vec = dict_from_sparse(user_vec_row.tag_vector)

    seen_articles = {
        i.article_id
        for i in db.query(UserInteraction.article_id)
        .filter(UserInteraction.user_id == user_id)
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
    top_ids = [aid for aid, _ in scored[:limit]]

    articles = (
        db.query(Article, User.user_name)
        .join(User, Article.author_id == User.user_id)
        .filter(Article.article_id.in_(top_ids))
        .all()
    )

    result = []
    for article, username in articles:
        result.append(
            ArticleRecommendationResponse(
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                author_username=username,
                created_at=article.created_at
            )
        )

    return result
