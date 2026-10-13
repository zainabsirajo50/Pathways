"""Content review/publication services. Caller owns the transaction; no commits here."""
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import math
from sqlalchemy import select, text
from geoalchemy2 import Geometry
from sqlalchemy import func
from app.models import Destination, DestinationSource, ContentReview, PublicationAudit
from app.db.seed import CATEGORIES, REGIONS

FIELDS = ('name', 'category', 'region', 'city', 'state', 'description', 'official_website', 'access_notes', 'location')
REVIEW_MAX_AGE = timedelta(days=30)
class ReviewError(ValueError):
    pass
class AuthorizationError(PermissionError):
    pass

def authorize(session, allowed_roles):
    # Actor is the authenticated session identity, never a supplied reviewer string.
    actor = session.scalar(text('SELECT session_user'))
    if not actor or actor not in allowed_roles:
        raise AuthorizationError('Authenticated database role is not authorized for content administration')
    return actor

def destination(session, slug):
    row = session.scalar(select(Destination).where(Destination.slug == slug).with_for_update())
    if row is None:
        raise ReviewError('Destination not found')
    return row

def snapshot(session, row):
    geometry = Destination.location.cast(Geometry(geometry_type='POINT', srid=4326))
    lat, lon = session.execute(select(func.ST_Y(geometry), func.ST_X(geometry)).where(Destination.id == row.id)).one()
    sources = session.scalars(select(DestinationSource).where(DestinationSource.destination_id == row.id).order_by(DestinationSource.source_url).with_for_update()).all()
    return {**{key: getattr(row, key) for key in FIELDS if key != 'location'},
            'slug': row.slug, 'location': None if lat is None else {'latitude': lat, 'longitude': lon},
            'sources': [{'url': s.source_url, 'type': s.source_type, 'reference': s.source_reference} for s in sources]}

def url(value):
    if not isinstance(value, str): return False
    p = urlparse(value)
    return p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password and not any(c.isspace() for c in value)

def authoritative(source):
    if not url(source['url']) or not isinstance(source.get('reference'), str) or not source['reference'].strip(): return False
    path = urlparse(source['url']).path.rstrip('/').lower()
    if path in {'', '/parks', '/stateparks', '/state-parks', '/planyourvisit'}: return False
    host = urlparse(source['url']).hostname
    if source['type'] == 'nps': return host == 'nps.gov' or host.endswith('.nps.gov')
    if source['type'] == 'georgia_dnr': return host in {'gastateparks.org', 'gastateparks.reserveamerica.com'} or host.endswith('.gastateparks.org')
    return False

def checked(value, now):
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None or not now - REVIEW_MAX_AGE <= date <= now: raise ValueError
        return date
    except (ValueError, TypeError, AttributeError):
        raise ReviewError('Evidence check timestamps must be timezone-aware, not future, and within 30 days') from None

def validate_review(data, evidence, notes, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(notes, str) or not notes.strip(): raise ReviewError('Review notes are required')
    if any(not isinstance(data.get(f), str) or not data[f].strip() for f in ('name','description','official_website','access_notes')):
        raise ReviewError('Name, description, official website, and access notes are required')
    if data['category'] not in CATEGORIES or data['region'] not in REGIONS or data['state'] != 'GA' or not isinstance(data.get('city'), str) or not data['city'].strip():
        raise ReviewError('Valid category, Georgia region/state, and locality are required')
    if not url(data['official_website']): raise ReviewError('Official website must be a credential-free HTTPS URL')
    official = {s['url'] for s in data['sources'] if authoritative(s)}
    # Presence of an official page is insufficient; every field needs human evidence.
    if not official: raise ReviewError('At least one destination-specific DNR or NPS source is required')
    if not isinstance(evidence, dict) or set(evidence) != set(FIELDS): raise ReviewError('Evidence must cover every reviewed field exactly')
    for field in FIELDS:
        item = evidence[field]
        if not isinstance(item, dict) or not isinstance(item.get('note'), str) or not item['note'].strip(): raise ReviewError(f'{field}: explain the source support or explicit absence')
        checked(item.get('checked_at'), now)
        if field == 'location' and data['location'] is None:
            if item.get('kind') != 'absent' or item.get('source_url') is not None: raise ReviewError('Null location requires an explicit absent-coordinate review')
        else:
            if item.get('source_url') not in official: raise ReviewError(f'{field}: reference a recorded authoritative source')
    loc = data['location']
    if loc is not None:
        e = evidence['location']
        if e.get('kind') != 'display_reference': raise ReviewError('Destination coordinates must be reviewed as display references, not routing endpoints')
        for key, low, high in [('latitude',30.3,35.1), ('longitude',-85.7,-80.7)]:
            v = loc[key]
            if isinstance(v, bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low <= v <= high or e.get(key) != v:
                raise ReviewError('Coordinate evidence must match the exact stored Georgia display point')
    return data

def record_review(session, slug, evidence, notes, allowed_roles):
    actor = authorize(session, allowed_roles)
    row = destination(session, slug)
    data = snapshot(session, row)
    validate_review(data, evidence, notes)
    review = ContentReview(destination_id=row.id, actor=actor, notes=notes.strip(), snapshot=data, evidence=evidence)
    session.add(review)
    # Explicitly reviewed nulls are locked too. Never drop previous field locks.
    row.reviewed_fields = sorted(set(row.reviewed_fields or []) | set(FIELDS))
    session.flush()
    return review

def approve_destination(session, slug, review_id, reason, allowed_roles):
    actor = authorize(session, allowed_roles)
    row = destination(session, slug)
    review = session.get(ContentReview, review_id)
    if review is None or review.destination_id != row.id: raise ReviewError('Review must belong to this destination')
    if row.status != 'needs_review': raise ReviewError('Only needs_review destinations can be approved')
    data = snapshot(session, row)
    if data != review.snapshot: raise ReviewError('Content or sources changed since review; record a new review')
    now = datetime.now(timezone.utc)
    if not now - REVIEW_MAX_AGE <= review.reviewed_at <= now: raise ReviewError('Content review is stale; review again')
    withdrawn = session.scalar(select(func.max(PublicationAudit.acted_at)).where(PublicationAudit.destination_id == row.id, PublicationAudit.action.in_(['revoke', 'invalidate'])))
    if withdrawn is not None and review.reviewed_at <= withdrawn: raise ReviewError('Revoked or invalidated content needs a new review before reapproval')
    validate_review(data, review.evidence, review.notes, now)
    if not set(FIELDS).issubset(row.reviewed_fields): raise ReviewError('Reviewed field protection is incomplete')
    if not reason.strip(): raise ReviewError('Approval reason is required')
    session.add(PublicationAudit(destination_id=row.id, review_id=review.id, actor=actor, action='approve', previous_status=row.status, new_status='verified', reason=reason.strip(), snapshot=data))
    row.status = 'verified'
    row.reviewed_fields = sorted(set(row.reviewed_fields) | {'status'})
    session.flush()
    return row

def revoke_destination(session, slug, reason, allowed_roles):
    actor = authorize(session, allowed_roles)
    row = destination(session, slug)
    if row.status != 'verified': raise ReviewError('Only verified destinations can be revoked')
    if not reason.strip(): raise ReviewError('Revocation reason is required')
    session.add(PublicationAudit(destination_id=row.id, actor=actor, action='revoke', previous_status=row.status, new_status='needs_review', reason=reason.strip(), snapshot=snapshot(session,row)))
    row.status = 'needs_review'
    session.flush()
    return row

