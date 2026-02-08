from sqlalchemy.orm import Session
from math import log
import time
import re
from models.article_model import Article, ArticleStat
from models.vector_model import ArticleVector
from models.user_model import User
from schemas.search_schema import SearchArticleResponse
from core.logger import get_logger
logger = get_logger(__name__)

# ------------------------------------------------------------------
# Text normalization & tokenization
# ------------------------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "with", "and", "or", "to", "of", "in", "on", "for"
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z]+")


def normalize_text(text: str) -> str:
    return text.lower().replace("-", " ")


def tokenize(text: str) -> set[str]:
    tokens = TOKEN_PATTERN.findall(normalize_text(text))
    return {t for t in tokens if t not in STOPWORDS}


def token_overlap_score(query: str, text: str) -> float:
    q_tokens = tokenize(query)
    t_tokens = tokenize(text)

    if not q_tokens or not t_tokens:
        return 0.0

    overlap = q_tokens & t_tokens
    return len(overlap) / len(q_tokens)


# ------------------------------------------------------------------
# Scoring helpers
# ------------------------------------------------------------------

def normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(value / max_value, 1.0)


def popularity_score(stats: ArticleStat) -> float:
    raw = (stats.like_count * 2) + (stats.save_count * 3)
    return log(raw + 1)


def recency_score(article: Article) -> float:
    age = time.time() - article.created_at.timestamp()
    if age < 0:
        age = 0
    return 1 / (1 + age)


# ------------------------------------------------------------------
# Hybrid search (phrase + token + fallback)
# ------------------------------------------------------------------

def hybrid_search(
    db: Session,
    query: str,
    user_id: int,
    limit: int = 5
) -> list[SearchArticleResponse]:

    logger.info(f"search_start query='{query}' user_id={user_id}")

    try:
        query_norm = normalize_text(query)

        candidates = (
            db.query(Article, ArticleVector, ArticleStat, User)
            .join(ArticleVector, Article.article_id == ArticleVector.article_id)
            .join(ArticleStat, Article.article_id == ArticleStat.article_id)
            .join(User, Article.author_id == User.user_id)
            .filter(
                Article.is_published.is_(True),
                Article.author_id != user_id
            )
            .limit(400)
            .all()
        )

        if not candidates:
            logger.warning("search_no_candidates")
            return []

        logger.info(f"search_candidates_loaded count={len(candidates)}")

        max_popularity = max(
            popularity_score(stats) for _, _, stats, _ in candidates
        )

        results: list[SearchArticleResponse] = []

        for article, _, stats, user in candidates:
            title = normalize_text(article.title)
            content = normalize_text(article.content)
            author_name = normalize_text(user.user_name)

            phrase_score = 1.0 if (
                query_norm in title
                or query_norm in content
                or query_norm in author_name
            ) else 0.0

            token_score = max(
                token_overlap_score(query, author_name),
                0.7 * token_overlap_score(query, title)
                + 0.3 * token_overlap_score(query, content)
            )

            popularity = normalize(
                popularity_score(stats),
                max_popularity
            )

            recency = recency_score(article)

            final_score = (
                0.45 * phrase_score +
                0.35 * token_score +
                0.12 * popularity +
                0.08 * recency
            )

            if final_score < 0.10:
                continue

            results.append(
                SearchArticleResponse(
                    article_id=article.article_id,
                    title=article.title,
                    content=article.content,
                    author_id=article.author_id,
                    created_at=article.created_at,
                    likes=stats.like_count,
                    score=round(final_score, 4)
                )
            )

        # Fallback logging
        if len(results) < limit:
            logger.info("search_fallback_triggered")

            fallback = (
                db.query(Article, ArticleStat)
                .join(ArticleStat, Article.article_id == ArticleStat.article_id)
                .filter(
                    Article.is_published.is_(True),
                    Article.author_id != user_id,
                    Article.article_id.notin_(
                        [r.article_id for r in results]
                    )
                )
                .order_by(
                    ArticleStat.like_count.desc(),
                    Article.created_at.desc()
                )
                .limit(limit - len(results))
                .all()
            )

            for article, stats in fallback:
                results.append(
                    SearchArticleResponse(
                        article_id=article.article_id,
                        title=article.title,
                        content=article.content,
                        author_id=article.author_id,
                        created_at=article.created_at,
                        likes=stats.like_count,
                        score=0.20
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)

        logger.info(
            f"search_completed query='{query}' results={len(results[:limit])}"
        )

        return results[:limit]

    except Exception:
        logger.exception(f"search_failed query='{query}'")
        raise

