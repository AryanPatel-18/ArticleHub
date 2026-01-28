from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    TIMESTAMP,
    CheckConstraint,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), unique=True, nullable=False)
    user_name = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    birth_date = Column(Date, nullable=True)
    bio = Column(Text, nullable=True)

    user_role = Column(String(20), nullable=False, default="user")
    social_link = Column(String(500), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "user_role IN ('user', 'admin', 'moderator')",
            name="user_role_check"
        ),
    )

    # Relationships
    articles = relationship("Article", back_populates="author", cascade="all, delete")
    interactions = relationship("UserInteraction", back_populates="user", cascade="all, delete")
    vector = relationship("UserVector", back_populates="user", uselist=False)


class UserPreferredTag(Base):
    __tablename__ = "user_preferred_tags"

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id = Column(
        Integer,
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True
    )
