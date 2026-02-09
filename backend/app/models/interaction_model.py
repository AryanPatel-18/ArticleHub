from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base

# The user interaction model for likes, saves and views

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    interaction_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.article_id", ondelete="CASCADE"), nullable=False)

    interaction_type = Column(String(20), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('view', 'like', 'save')",
            name="interaction_type_check"
        ),
    )

    user = relationship("User", back_populates="interactions")
    article = relationship("Article", back_populates="interactions")
