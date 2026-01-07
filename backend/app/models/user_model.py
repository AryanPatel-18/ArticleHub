from sqlalchemy import Column, Date, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from database.db import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, unique=True, nullable=False)
    user_name = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    birth_date = Column(Date, nullable = False)
    about_author = Column(String, default=None)
    user_role = Column(String, default="user")
    social_link = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now()) 