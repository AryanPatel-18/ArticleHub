from pydantic import BaseModel
from datetime import datetime
from typing import List
# Contains the schemas for the search functionality, including the request model for search queries and the response models for search results. These schemas ensure that the data sent to and received from the search endpoints is structured and validated properly.

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
