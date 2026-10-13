from datetime import datetime, timezone, timedelta
import uuid
from types import SimpleNamespace
import pytest
from sqlalchemy import select, text, func
from sqlalchemy.exc import DBAPIError
from app.models import Destination, DestinationEntrance, DestinationSource, RouteVerification, ContentReview, PublicationAudit
from app.services.publication import FIELDS, authorize, validate_review, record_review, approve_destination, revoke_destination, ReviewError, AuthorizationError
from app.content_admin import main
from app.db.seed import import_seeds
SOURCE='https://gastateparks.org/Vogel'
def evidence(location=None):
    stamp=datetime.now(timezone.utc).isoformat()
    e={f:dict(source_url=SOURCE,checked_at=stamp,note='Synthetic field-specific review') for f in FIELDS}
    e['location']=dict(kind='absent',source_url=None,checked_at=stamp,note='Explicit absence') if location is None else dict(kind='display_reference',source_url=SOURCE,checked_at=stamp,note='Display point only',**location)
    return e

def data():
    return dict(slug='synthetic',name='Synthetic place',category='park',region='north',city='Blairsville',state='GA',description='Synthetic description',official_website=SOURCE,access_notes='Reviewed access notes',location=None,sources=[dict(url=SOURCE,type='georgia_dnr',reference='Destination-specific source')])

@pytest.mark.parametrize('field',['name','description','city','official_website','access_notes'])
def test_required_content(field):
    d=data(); d[field]=''
    with pytest.raises(ReviewError): validate_review(d,evidence(),'Reviewed')
@pytest.mark.parametrize('mutation',['missing','future','stale','naive','unofficial','absent','entrance','coordinates','authority'])
def test_bad_evidence(mutation):
    d=data(); e=evidence()
    if mutation=='missing': del e['name']
    if mutation=='future': e['name']['checked_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    if mutation=='stale': e['name']['checked_at']=(datetime.now(timezone.utc)-timedelta(days=31)).isoformat()
    if mutation=='naive': e['name']['checked_at']='2026-10-12T00:00:00'
    if mutation=='unofficial': e['name']['source_url']='https://untrusted.example/'
    if mutation=='absent': e['location']['kind']='display_reference'
    if mutation in {'entrance','coordinates'}:
        d['location']=dict(latitude=34.73194,longitude=-83.91694); e=evidence(d['location'])
        if mutation=='entrance': e['location']['kind']='gate'
        else: e['location']['latitude']=34.5
    if mutation=='authority': d['sources'][0]['url']='https://gastateparks.org.evil.example/Vogel'
    with pytest.raises(ReviewError): validate_review(d,e,'Reviewed')
def test_null_and_sourced_display_coordinates_allowed():
    d=data(); validate_review(d,evidence(),'Reviewed absence')
    d['location']=dict(latitude=34.73194,longitude=-83.91694)
    validate_review(d,evidence(d['location']),'Display review only')
def test_authorization_uses_authenticated_role():
    session=SimpleNamespace(scalar=lambda _: 'actual_role')
    with pytest.raises(AuthorizationError): authorize(session,set())
    with pytest.raises(AuthorizationError): authorize(session,{'pretend_reviewer'})
    assert authorize(session,{'actual_role'})=='actual_role'
def test_cli_disabled(monkeypatch):
    monkeypatch.setenv('PATHWAYS_CONTENT_REVIEW_ROLES','')
    with pytest.raises(SystemExit): main(['inspect','vogel-state-park'])
def test_cli_write_confirmation(monkeypatch):
    monkeypatch.setenv('PATHWAYS_CONTENT_REVIEW_ROLES','some_role')
    with pytest.raises(SystemExit): main(['revoke','vogel-state-park','--reason','test'])
@pytest.fixture
def candidate(db):
    row=db.scalar(select(Destination).where(Destination.slug=='vogel-state-park'))
    row.description='Synthetic reviewed description'; row.official_website=SOURCE; row.access_notes='Synthetic reviewed access notes'
    db.add(DestinationSource(destination_id=row.id,source_type='georgia_dnr',source_url=SOURCE,source_reference='Synthetic specific source')); db.flush()
    return row,{db.scalar(text('SELECT session_user'))}
def test_review_approve_revoke_seed_protection_and_routing_unchanged(db,candidate):
    row,roles=candidate; entrance=db.scalar(select(DestinationEntrance))
    original=(entrance.routing_status,entrance.coordinate_review_status,entrance.verified_at,entrance.location.data)
    review=record_review(db,row.slug,evidence(),'Synthetic review',roles)
    assert row.status=='needs_review'
    approve_destination(db,row.slug,review.id,'Synthetic publication',roles)
    assert row.status=='verified'
    revoke_destination(db,row.slug,'Synthetic withdrawal',roles)
    locks=list(row.reviewed_fields); import_seeds(db); db.refresh(row); db.refresh(entrance)
    assert row.status=='needs_review' and row.description=='Synthetic reviewed description' and row.location is None
    assert row.reviewed_fields==locks and 'location' in locks and 'status' in locks
    assert (entrance.routing_status,entrance.coordinate_review_status,entrance.verified_at,entrance.location.data)==original
    assert db.scalar(select(func.count()).select_from(RouteVerification))==0
    audits=db.scalars(select(PublicationAudit)).all()
    assert {a.action for a in audits}=={'approve','revoke'} and all(a.actor in roles for a in audits)
    assert db.get(ContentReview,review.id).snapshot['description']=='Synthetic reviewed description'
@pytest.mark.parametrize('change',['content','source','locks'])
def test_approval_rejects_changed_review(db,candidate,change):
    row,roles=candidate; review=record_review(db,row.slug,evidence(),'Review',roles)
    if change=='content': row.description='Changed content'
    if change=='source': db.scalar(select(DestinationSource).where(DestinationSource.source_url==SOURCE)).source_reference='Changed source'
    if change=='locks': row.reviewed_fields=[]
    db.flush()
    with pytest.raises(ReviewError): approve_destination(db,row.slug,review.id,'Reason',roles)
    assert row.status=='needs_review' and db.scalar(select(func.count()).select_from(PublicationAudit))==0
@pytest.mark.parametrize('action',['review','approve','revoke'])
def test_unauthorized_writes_nothing(db,candidate,action):
    row,_=candidate
    with pytest.raises(AuthorizationError):
        if action=='review': record_review(db,row.slug,evidence(),'Notes',set())
        elif action=='approve': approve_destination(db,row.slug,uuid.uuid4(),'Reason',set())
        else: revoke_destination(db,row.slug,'Reason',set())
    assert db.scalar(select(func.count()).select_from(ContentReview))==0
    assert db.scalar(select(func.count()).select_from(PublicationAudit))==0
@pytest.mark.parametrize('change',['content','source','locks'])
def test_published_edits_invalidate_without_erasing_history(db,candidate,change):
    row,roles=candidate; r=record_review(db,row.slug,evidence(),'Review',roles)
    approve_destination(db,row.slug,r.id,'Reason',roles)
    if change=='content': row.description='Edited after approval'
    elif change=='locks': row.reviewed_fields=[]
    else: db.scalar(select(DestinationSource).where(DestinationSource.source_url==SOURCE)).source_reference='Changed evidence'
    db.flush(); db.refresh(row)
    assert row.status=='needs_review' and db.scalar(select(func.count()).select_from(PublicationAudit))==2
    assert db.get(ContentReview,r.id).snapshot['description']=='Synthetic reviewed description'
@pytest.mark.parametrize('table',['destination_content_reviews','destination_publication_audits'])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_append_only_history(db,candidate,table,operation):
    row,roles=candidate; r=record_review(db,row.slug,evidence(),'Review',roles); approve_destination(db,row.slug,r.id,'Reason',roles)
    with pytest.raises(DBAPIError),db.begin_nested():
        db.execute(text(f"UPDATE {table} SET actor='overwrite'" if operation=='UPDATE' else f'DELETE FROM {table}'))
def test_wrong_review_and_empty_reason(db,candidate):
    row,roles=candidate
    with pytest.raises(ReviewError): approve_destination(db,row.slug,uuid.uuid4(),'Reason',roles)
    r=record_review(db,row.slug,evidence(),'Review',roles)
    with pytest.raises(ReviewError): approve_destination(db,row.slug,r.id,' ',roles)
def test_approval_and_audit_rollback_together(db,candidate):
    row,roles=candidate; r=record_review(db,row.slug,evidence(),'Review',roles)
    with pytest.raises(RuntimeError):
        with db.begin_nested():
            approve_destination(db,row.slug,r.id,'Reason',roles); raise RuntimeError('Simulated failure')
    db.refresh(row)
    assert row.status=='needs_review' and db.scalar(select(func.count()).select_from(PublicationAudit))==0
def test_generic_directory_and_missing_source_scope_rejected():
    d=data(); d['sources'][0]['reference']=None
    with pytest.raises(ReviewError): validate_review(d,evidence(),'Review')
    d=data(); d['sources'][0]['url']='https://gastateparks.org/Parks'
    with pytest.raises(ReviewError): validate_review(d,evidence(),'Review')

def test_expired_review_rejected(db,candidate):
    from app.services.publication import snapshot
    row,roles=candidate
    r=ContentReview(destination_id=row.id,actor=next(iter(roles)),reviewed_at=datetime.now(timezone.utc)-timedelta(days=31),notes='Old review',snapshot=snapshot(db,row),evidence=evidence())
    db.add(r); row.reviewed_fields=list(FIELDS); db.flush()
    with pytest.raises(ReviewError): approve_destination(db,row.slug,r.id,'Reason',roles)
    assert row.status=='needs_review'

def test_revocation_requires_new_review_for_reapproval(db,candidate):
    row,roles=candidate; r=record_review(db,row.slug,evidence(),'Review',roles)
    approve_destination(db,row.slug,r.id,'Reason',roles)
    revoke_destination(db,row.slug,'Withdrawal',roles)
    with pytest.raises(ReviewError): approve_destination(db,row.slug,r.id,'Reapprove old review',roles)
    assert row.status=='needs_review'

def test_cli_denies_role_and_leaves_database_unchanged(db,candidate,monkeypatch,capsys):
    import app.content_admin as cli
    from app.config import Settings
    row,_=candidate
    monkeypatch.setenv('PATHWAYS_CONTENT_REVIEW_ROLES','not_authenticated_role')
    monkeypatch.setattr(cli,'get_settings',lambda: Settings(database_url='postgresql+psycopg://unused/pathways'))
    class Engine:
        def dispose(self): pass
    monkeypatch.setattr(cli,'create_engine',lambda *a,**k: Engine())
    class ContextSession:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def begin(self): return self
        def scalar(self,q): return next(iter(candidate[1]))
    monkeypatch.setattr(cli,'Session',lambda _: ContextSession())
    assert cli.main(['revoke',row.slug,'--reason','Denied test','--confirm'])==1
    assert 'not authorized' in capsys.readouterr().out
    assert db.scalar(select(func.count()).select_from(PublicationAudit))==0

def test_cli_exposes_no_http_approval_endpoints(db):
    from app.config import Settings
    from app.main import create_app
    from fastapi.testclient import TestClient
    app=create_app(Settings(database_url='postgresql+psycopg://unused/pathways'))
    with TestClient(app) as client:
        assert client.post('/api/v1/destinations/vogel-state-park/approve').status_code==404
        assert client.post('/api/v1/admin/destinations/vogel-state-park/revoke').status_code==404

def test_content_publication_and_revocation_control_public_reads(db,candidate):
    from app.api.catalog import get_destination
    row,roles=candidate
    assert get_destination(db,row.slug) is None
    r=record_review(db,row.slug,evidence(),'Review',roles)
    approve_destination(db,row.slug,r.id,'Reason',roles)
    assert get_destination(db,row.slug).description=='Synthetic reviewed description'
    revoke_destination(db,row.slug,'Withdrawal',roles)
    assert get_destination(db,row.slug) is None

def test_failed_review_does_not_lock_or_write(db,candidate):
    row,roles=candidate; before=list(row.reviewed_fields)
    e=evidence(); e['name']['source_url']='https://untrusted.example/'
    with pytest.raises(ReviewError): record_review(db,row.slug,e,'Notes',roles)
    assert row.reviewed_fields==before and row.status=='needs_review'
    assert db.scalar(select(func.count()).select_from(ContentReview))==0

def test_audit_constraint_rejects_approval_without_review(db,candidate):
    row,roles=candidate
    with pytest.raises(DBAPIError),db.begin_nested():
        db.add(PublicationAudit(destination_id=row.id,actor=next(iter(roles)),action='approve',previous_status='needs_review',new_status='verified',reason='No review',snapshot={}))
        db.flush()

@pytest.mark.parametrize('case',['website','category','region','state','notes','bounds','missing-coordinate-evidence'])
def test_invalid_content_or_coordinate_claim(case):
    d=data(); e=evidence(); notes='Notes'
    if case=='website': d['official_website']='https://user:secret@gastateparks.org/Vogel'
    if case=='category': d['category']='invalid'
    if case=='region': d['region']='invalid'
    if case=='state': d['state']='FL'
    if case=='notes': notes=' '
    if case=='bounds': d['location']=dict(latitude=20,longitude=-80); e=evidence(d['location'])
    if case=='missing-coordinate-evidence': d['location']=dict(latitude=34.73194,longitude=-83.91694)
    with pytest.raises(ReviewError): validate_review(d,e,notes)
def test_destination_publication_preserves_related_entrance_and_route_history(db,candidate):
    row,roles=candidate
    e=DestinationEntrance(destination_id=row.id,name='Synthetic pending entrance',routing_status='untested',point_kind='unknown',coordinate_review_status='pending',reviewed_fields=['location'])
    db.add(e); db.flush()
    history=RouteVerification(entrance_id=e.id,provider='synthetic-test',travel_mode='driving',origin_latitude=33.994622,origin_longitude=-84.333933,destination_latitude=33.994622,destination_longitude=-84.333933,result='failed',error_details='Synthetic historical test; not an actual route claim')
    db.add(history); db.flush()
    review=record_review(db,row.slug,evidence(),'Review',roles)
    approve_destination(db,row.slug,review.id,'Reason',roles)
    revoke_destination(db,row.slug,'Withdrawal',roles)
    db.refresh(e); db.refresh(history)
    assert e.routing_status=='untested' and e.coordinate_review_status=='pending' and e.location is None and e.verified_at is None
    assert e.reviewed_fields==['location']
    assert history.result=='failed' and history.provider=='synthetic-test'
