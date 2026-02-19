from typing import List
from pydantic import BaseModel
from datetime import datetime


class SearchArticleResponse(BaseModel):
    article_id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    likes: int
    score: float


class SearchUserResponse(BaseModel):
    user_id: int
    user_name: str
    bio: str | None


class SearchResponse(BaseModel):
    articles: List[SearchArticleResponse]
    users: List[SearchUserResponse]
