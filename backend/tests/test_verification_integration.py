from datetime import datetime, timezone
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from app.models import Destination, DestinationEntrance, RouteVerification
from app.db.seed import import_seeds, point


def entrance(db):
    return db.scalar(select(DestinationEntrance))


def test_migration_roundtrip_preserves_original_catalog(db):
    assert db.scalar(select(func.count()).select_from(Destination)) == 10
    assert entrance(db).coordinate_review_status == 'pending'
    assert entrance(db).coordinate_source_url is None
    assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0003_content_publication'


def test_import_preserves_manual_fields_reviewed_nulls_and_ids(db):
    d = db.scalar(select(Destination).where(Destination.slug == 'amicalola-falls-state-park'))
    d.description = 'Manually edited description'
    d.city = None
    d.reviewed_fields.append('city')
    e = entrance(db)
    e.address = 'Manually edited arrival address'
    e.reviewed_fields.append('location')
    db.flush()
    ids = db.scalars(select(Destination.id).order_by(Destination.slug)).all()
    import_seeds(db)
    import_seeds(db)
    db.expire_all()
    assert d.description == 'Manually edited description'
    assert d.city is None
    assert e.address == 'Manually edited arrival address'
    assert db.scalars(select(Destination.id).order_by(Destination.slug)).all() == ids
    assert db.scalar(select(func.count()).select_from(DestinationEntrance)) == 1


def test_reviewed_and_rejected_entrances_are_preserved(db):
    e = entrance(db)
    e.coordinate_review_status = 'rejected'
    e.coordinate_review_notes = 'Wrong arrival point'
    db.flush()
    import_seeds(db)
    db.refresh(e)
    assert e.coordinate_review_status == 'rejected'
    assert e.coordinate_review_notes == 'Wrong arrival point'


def test_dry_run_leaves_database_unchanged(db):
    before = db.execute(text('SELECT id,name,description,city,status FROM destinations ORDER BY slug')).all()
    import_seeds(db, dry_run=True)
    assert db.execute(text('SELECT id,name,description,city,status FROM destinations ORDER BY slug')).all() == before


def test_review_requires_provenance_and_review_record(db):
    with pytest.raises(IntegrityError), db.begin_nested():
        entrance(db).coordinate_review_status = 'reviewed'
        db.flush()


def test_coordinate_change_invalidates_review_without_erasing_history(db):
    e = entrance(db)
    e.point_kind = 'gate'
    e.coordinate_source_url = 'https://www.nps.gov/chat/'
    db.flush()
    db.refresh(e)
    e.coordinate_review_status = 'reviewed'
    e.coordinate_reviewed_by = 'Synthetic test reviewer'
    e.coordinate_reviewed_at = datetime.now(timezone.utc)
    e.routing_status = 'passed'
    e.verified_at = datetime.now(timezone.utc)
    db.flush()
    route = RouteVerification(entrance_id=e.id,provider='test-fixture',travel_mode='driving',
        origin_latitude=33,origin_longitude=-84,destination_latitude=33.994622,
        destination_longitude=-84.333933,result='passed')
    db.add(route)
    db.flush()
    e.location = point(33.99, -84.33)
    db.flush()
    db.refresh(e)
    assert e.coordinate_review_status == 'pending'
    assert e.routing_status == 'untested'
    assert e.coordinate_reviewed_at is None and e.verified_at is None
    assert db.get(RouteVerification, route.id).destination_latitude == 33.994622


@pytest.mark.parametrize('field,value', [('point_kind','center'), ('coordinate_review_status','verified'),
    ('coordinate_source_url','invalid'), ('reviewed_fields',['not_a_field'])])
def test_entrance_constraints(db, field, value):
    with pytest.raises(IntegrityError), db.begin_nested():
        setattr(entrance(db), field, value)
        db.flush()


@pytest.mark.parametrize('changes', [dict(provider=' '),dict(travel_mode='flying'),dict(result='verified'),
    dict(origin_latitude=91),dict(destination_longitude=181),dict(result='error'),
    dict(origin_latitude=float('nan')),dict(destination_longitude=float('inf'))])
def test_route_constraints(db, changes):
    values = dict(entrance_id=entrance(db).id,provider='test-fixture',travel_mode='walking',
        origin_latitude=33,origin_longitude=-84,destination_latitude=33.994622,
        destination_longitude=-84.333933,result='manual_review')
    values.update(changes)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(RouteVerification(**values))
        db.flush()


def test_recording_history_never_approves_entrance(db):
    e = entrance(db)
    for mode in ('driving','walking'):
        db.add(RouteVerification(entrance_id=e.id,provider='test-fixture',travel_mode=mode,
            origin_latitude=33,origin_longitude=-84,destination_latitude=33.994622,
            destination_longitude=-84.333933,result='error',error_details='Synthetic provider timeout'))
    db.flush()
    db.refresh(e)
    assert e.routing_status == 'untested'
    assert e.coordinate_review_status == 'pending'
    assert db.scalar(select(func.count()).select_from(RouteVerification)) == 2


def test_verified_destination_is_never_downgraded_by_seed(db):
    d = db.scalar(select(Destination).where(Destination.slug == 'amicalola-falls-state-park'))
    d.status = 'verified'  # Synthetic test only; outer transaction always rolls back.
    d.name = 'Reviewed display name'
    db.flush()
    import_seeds(db)
    db.refresh(d)
    assert d.status == 'verified' and d.name == 'Reviewed display name'


def test_primary_arrival_choice_is_preserved(db):
    e = entrance(db)
    d = db.get(Destination, e.destination_id)
    e.is_primary = False
    db.add(DestinationEntrance(destination_id=d.id, name='Manually chosen arrival', is_primary=True))
    db.flush()
    import_seeds(db)
    db.refresh(e)
    assert not e.is_primary
    assert db.scalar(select(func.count()).select_from(DestinationEntrance).where(DestinationEntrance.is_primary.is_(True))) == 1


def test_reviewed_entrance_is_not_changed_by_import(db):
    e = entrance(db)
    e.point_kind = 'gate'
    e.coordinate_source_url = 'https://www.nps.gov/chat/'
    db.flush()
    db.refresh(e)
    e.coordinate_review_status = 'reviewed'
    e.coordinate_reviewed_at = datetime.now(timezone.utc)
    e.coordinate_reviewed_by = 'Synthetic test reviewer'
    e.address = None
    db.flush()
    import_seeds(db)
    db.refresh(e)
    assert e.address is None and e.coordinate_review_status == 'reviewed'


@pytest.mark.parametrize('field,value', [('coordinate_source_url','https://www.nps.gov/places/'),('point_kind','parking')])
def test_provenance_changes_also_invalidate_existing_approval(db, field, value):
    e = entrance(db)
    e.routing_status = 'passed'  # Isolated fixture evidence, not a live route test.
    db.flush()
    setattr(e, field, value)
    db.flush()
    db.refresh(e)
    assert e.routing_status == 'untested'


def test_unknown_destination_field_lock_is_rejected(db):
    with pytest.raises(IntegrityError), db.begin_nested():
        db.scalar(select(Destination)).reviewed_fields = ['typo']
        db.flush()

