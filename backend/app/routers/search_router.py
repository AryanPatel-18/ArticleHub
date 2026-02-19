from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.search_schema import SearchResponse
from app.services.search_service import hybrid_search

# This router handles the endpoint related to searching for articles based on keywords in the title, content, or tags. It uses a hybrid search approach that combines full-text search and tag-based search to provide relevant results to users.
router = APIRouter(prefix="/search", tags=["Search"])

# Endpoint to search for articles using keywords in the title, content, or tags. The search results are ranked based on relevance to the query and the user's interactions with articles
@router.get("", response_model=SearchResponse)
def search_articles(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    data = hybrid_search(db=db, query=q, user_id=user_id)

    return SearchResponse(
        articles=data["articles"],
        users=data["users"]
    )

