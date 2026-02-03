from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class ArticleCreateRequest(BaseModel):
    token : str
    title: str = Field(..., min_length=5)
    content: str = Field(..., min_length=50)
    tag_names: List[str]


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


class PaginatedArticleRecommendationResponse(BaseModel):
    page: int
    page_size: int
    total_results: int
    total_pages: int
    articles: List[ArticleRecommendationResponse]

    class Config:
        from_attributes = True


class SavedArticleResponse(BaseModel):
    article_id: int
    likes : int
    title: str
    content: str
    author_username: str
    created_at: datetime


class PaginatedSavedArticlesResponse(BaseModel):
    page: int
    page_size: int
    total_results: int
    total_pages: int
    articles: List[SavedArticleResponse]
    
class UserArticleResponse(BaseModel):
    article_id: int
    title: str
    content: str
    author_username: str
    created_at: datetime


class PaginatedUserArticlesResponse(BaseModel):
    page: int
    page_size: int
    total_results: int
    total_pages: int
    articles: list[UserArticleResponse]

class UserArticleStatsResponse(BaseModel):
    total_articles: int
    published_articles: int
    total_views: int
    total_likes: int
    total_saves: int

class ArticleByTagSchema(BaseModel):
    article_id: int
    author_id: int
    title: str
    content: str
    created_at: datetime

class PaginatedArticlesByTagSchema(BaseModel):
    tag_id: int
    page: int
    page_size: int
    total_articles: int
    total_pages: int
    articles: List[ArticleByTagSchema]

class ArticleByAuthorSchema(BaseModel):
    article_id: int
    author_id: int
    title: str
    content: str
    created_at: datetime

class PaginatedArticlesByAuthorSchema(BaseModel):
    author_id: int
    page: int
    page_size: int
    total_articles: int
    total_pages: int
    articles: List[ArticleByAuthorSchema]

class SavedArticleSchema(BaseModel):
    article_id: int
    title: str
    content: str
    created_at: datetime
    like_count: int

class SavedArticlesResponseSchema(BaseModel):
    user_id: int
    articles: List[SavedArticleSchema]