from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user_id
from schemas.search_schema import SearchResponse
from services.search_service import hybrid_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search_articles(q: str = Query(..., min_length=2),db: Session = Depends(get_db), user_id : int = Depends(get_current_user_id)):
    results = hybrid_search(db=db, query=q, user_id=user_id)
    return SearchResponse(results=results)
