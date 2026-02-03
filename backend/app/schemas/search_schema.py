from pydantic import BaseModel
from datetime import datetime
from typing import List


class SearchRequest(BaseModel):
    query: str


class SearchArticleResponse(BaseModel):
    article_id: int
    title: str
    content : str
    author_id: int
    created_at: datetime
    likes : int
    score: float


class SearchResponse(BaseModel):
    results: List[SearchArticleResponse]
