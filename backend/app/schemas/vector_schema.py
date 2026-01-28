from pydantic import BaseModel
from datetime import datetime


class ArticleVectorInfo(BaseModel):
    article_id: int
    vector_version: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserVectorInfo(BaseModel):
    user_id: int
    last_updated: datetime | None

    class Config:
        from_attributes = True
