"""Publication-filtered destination reads and public coordinate projections."""
from sqlalchemy import func, select
from geoalchemy2 import Geometry
from sqlalchemy.orm import Session
from app.models import Destination
from app.api.schemas import DestinationCategory, DestinationResponse


def public_columns():
    # Geography stores longitude first. Project in PostGIS rather than requiring Shapely.
    geometry = Destination.location.cast(Geometry(geometry_type='POINT', srid=4326))
    fields = ('slug', 'name', 'category', 'region', 'city', 'state', 'description', 'official_website', 'access_notes')
    return [getattr(Destination, field) for field in fields] + [
        func.ST_Y(geometry).label('latitude'), func.ST_X(geometry).label('longitude')]


def publication_filters(q: str | None = None, category: DestinationCategory | None = None):
    filters = [Destination.status == 'verified']
    if q and q.strip():
        # '%' and '_' in user input are literal characters, not wildcard operators.
        filters.append(Destination.name.icontains(q.strip(), autoescape=True))
    if category is not None:
        filters.append(Destination.category == category.value)
    return filters


def list_destinations(session: Session, q: str | None, category: DestinationCategory | None, page: int, page_size: int):
    filters = publication_filters(q, category)
    total = session.scalar(select(func.count()).select_from(Destination).where(*filters))
    query = select(*public_columns()).where(*filters).order_by(func.lower(Destination.name), Destination.slug).offset((page - 1) * page_size).limit(page_size)
    items = [DestinationResponse.model_validate(dict(row)) for row in session.execute(query).mappings()]
    return dict(items=items, total=total, page=page, page_size=page_size)


def get_destination(session: Session, slug: str):
    row = session.execute(select(*public_columns()).where(*publication_filters(), Destination.slug == slug)).mappings().one_or_none()
    return DestinationResponse.model_validate(dict(row)) if row is not None else None
