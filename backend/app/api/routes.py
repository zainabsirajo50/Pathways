"""Version-one read-only catalog routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.api import catalog
from app.api.schemas import CategoryResponse, DestinationCategory, DestinationPage, DestinationResponse, HealthResponse
from app.db.session import get_session

router = APIRouter(prefix='/api/v1')
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get('/health', response_model=HealthResponse, tags=['health'])
def health():
    return HealthResponse(status='ok')


# Register the static route before /{slug} so "categories" is never treated as a slug.
@router.get('/destinations/categories', response_model=CategoryResponse, tags=['destinations'])
def categories():
    return CategoryResponse(categories=list(DestinationCategory))


@router.get('/destinations', response_model=DestinationPage, tags=['destinations'])
def destinations(session: DatabaseSession,
                 q: Annotated[str | None, Query(max_length=160)] = None,
                 category: DestinationCategory | None = None,
                 page: Annotated[int, Query(ge=1, le=1000000)] = 1,
                 page_size: Annotated[int, Query(ge=1, le=100)] = 20):
    return catalog.list_destinations(session, q, category, page, page_size)


@router.get('/destinations/{slug}', response_model=DestinationResponse, tags=['destinations'])
def destination(session: DatabaseSession, slug: Annotated[str, Path(max_length=160)]):
    item = catalog.get_destination(session, slug)
    if item is None:
        raise HTTPException(status_code=404, detail='Destination not found')
    return item
