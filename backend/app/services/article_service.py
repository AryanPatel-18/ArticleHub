from sqlalchemy.orm import Session
from models.article_model import Article, ArticleTag, Tag
from models.user_model import User
from schemas.article_schema import ArticleReadResponse

def get_article_by_id(db: Session, get_id: int) -> ArticleReadResponse | None:
    article = (
        db.query(Article)
        .filter(Article.article_id == get_id)
        .filter(Article.is_published)
        .first()
    )

    if article is None:
        return None

    author = (
        db.query(User.user_name)
        .filter(User.user_id == article.author_id)
        .first()
    )

    if author is None:
        return None

    tag_rows = (
        db.query(Tag.tag_name)
        .join(ArticleTag, Tag.tag_id == ArticleTag.tag_id)
        .filter(ArticleTag.article_id == article.article_id)
        .all()
    )

    tags = [row.tag_name for row in tag_rows]

    return ArticleReadResponse(
        article_id=article.article_id,
        title=article.title,
        content=article.content,
        author_username=author.user_name,
        created_at=article.created_at,
        tags=tags
    )
