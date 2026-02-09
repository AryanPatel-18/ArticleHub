from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base

# All database models related to the articles

class Article(Base):
    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)

    is_published = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP)

    # Relationships
    author = relationship("User", back_populates="articles")
    tags = relationship("ArticleTag", back_populates="article", cascade="all, delete")
    interactions = relationship("UserInteraction", back_populates="article", cascade="all, delete")
    vector = relationship("ArticleVector", back_populates="article", uselist=False)
    stats = relationship("ArticleStat", back_populates="article", uselist=False)


class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True)
    tag_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    articles = relationship("ArticleTag", back_populates="tag", cascade="all, delete")


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id = Column(
        Integer,
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id = Column(
        Integer,
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True
    )

    article = relationship("Article", back_populates="tags")
    tag = relationship("Tag", back_populates="articles")


class ArticleStat(Base):
    __tablename__ = "article_stats"

    article_id = Column(
        Integer,
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        primary_key=True
    )

    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)

    article = relationship("Article", back_populates="stats")
