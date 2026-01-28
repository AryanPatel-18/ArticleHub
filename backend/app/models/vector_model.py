from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class ArticleVector(Base):
    __tablename__ = "article_vectors"

    article_id = Column(
        Integer,
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        primary_key=True
    )

    text_vector = Column(String, nullable=False)
    tag_vector = Column(String, nullable=False)

    vector_version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())

    article = relationship("Article", back_populates="vector")


class UserVector(Base):
    __tablename__ = "user_vectors"

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    text_vector = Column(String, nullable=True)
    tag_vector = Column(String, nullable=True)

    last_updated = Column(TIMESTAMP)

    user = relationship("User", back_populates="vector")
