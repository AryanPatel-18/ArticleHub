from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id = Column(Integer, primary_key=True, index=True)

    admin_user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    action_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=False)

    target_snapshot = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    admin = relationship("User")
