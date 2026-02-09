from pydantic import BaseModel

# This schema defines the data schemas for trending articles, tags, and authors.

class TrendingArticleSchema(BaseModel):
    article_id: int
    score: float

class TrendingTagSchema(BaseModel):
    tag_id: int
    tag_name: str
    count: int

class TrendingAuthorSchema(BaseModel):
    user_id: int
    user_name: str
    count: int
