from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(..., min_length=50)
    tag_ids: List[int]


class ArticleResponse(BaseModel):
    article_id: int
    author_id: int
    title: str
    content: str
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ArticleReadResponse(BaseModel):
    article_id: int
    title: str
    content: str
    author_username: str
    created_at: datetime
    tags: List[str]

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    tag_id: int
    tag_name: str

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    article_id: int
    title: str
    author_id: int
    created_at: datetime

class ArticleRecommendationResponse(BaseModel):
    article_id: int
    title: str
    content: str
    author_username: str
    created_at: datetime

    class Config:
        from_attributes = True
