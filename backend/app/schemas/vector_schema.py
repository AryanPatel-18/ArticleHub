from pydantic import BaseModel
from datetime import datetime

# This schema defines the data schemas for article and user vectors, including the article vector information and user vector information. These schemas ensure that the data sent to and received from the API regarding article and user vectors is structured and validated properly.

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
