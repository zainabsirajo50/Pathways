import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config import Settings, get_settings
from app.main import create_app
from app.api.schemas import DestinationCategory
from app.db.seed import CATEGORIES, point
from app.db.session import get_session
from app.models import Destination


@pytest.fixture
def api(db):
    app = create_app(Settings(database_url='postgresql+psycopg://unused/pathways'))
    def override_session():
        yield db
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client


@pytest.fixture
def published(db):
    # All publication examples are synthetic and roll back in the disposable database.
    rows = [
        ('api-alpha', 'Alpha River', 'river', point(33.994622, -84.333933)),
        ('api-beta', 'Alpha River', 'river', None),
        ('api-lake', 'Quiet Lake', 'lake', None),
        ('api-falls', 'Z Falls', 'waterfall', None),
        ('api-percent', '100% Nature', 'park', None),
    ]
    for slug, name, category, location in rows:
        db.add(Destination(slug=slug,name=name,category=category,region='north',
            status='verified',location=location,description='Synthetic public description',
            reviewed_fields=['description']))
    for status in ('draft', 'needs_review'):
        db.add(Destination(slug=f'api-hidden-{status.replace("_","-")}',name='Alpha River Hidden',
            category='river',region='north',status=status))
    db.flush()


def test_initial_catalog_is_not_public(api):
    response = api.get('/api/v1/destinations')
    assert response.status_code == 200
    assert response.json() == dict(items=[], total=0, page=1, page_size=20)
    assert api.get('/api/v1/destinations/chattahoochee-island-ford').status_code == 404


def test_only_published_records_and_fields_are_returned(api, published):
    data = api.get('/api/v1/destinations').json()
    assert data['total'] == 5
    expected = {'slug','name','category','region','city','state','description','official_website','access_notes','latitude','longitude'}
    for item in data['items']:
        assert set(item) == expected
        assert 'hidden' not in item['slug']


def test_name_search_category_and_combined_filters(api, published):
    data = api.get('/api/v1/destinations', params={'q':' aLpHa ', 'category':'river'}).json()
    assert data['total'] == 2
    assert [item['slug'] for item in data['items']] == ['api-alpha','api-beta']
    assert api.get('/api/v1/destinations',params={'category':'lake'}).json()['total'] == 1
    assert api.get('/api/v1/destinations',params={'q':'Alpha','category':'lake'}).json()['total'] == 0


def test_search_wildcards_are_literal(api, published):
    assert api.get('/api/v1/destinations',params={'q':'%'}).json()['total'] == 1
    assert api.get('/api/v1/destinations',params={'q':'_'}).json()['total'] == 0


def test_pagination_is_stable_and_totals_are_filtered(api, published):
    first = api.get('/api/v1/destinations',params={'category':'river','page_size':1}).json()
    second = api.get('/api/v1/destinations',params={'category':'river','page_size':1,'page':2}).json()
    assert first['items'][0]['slug'] == 'api-alpha'
    assert second['items'][0]['slug'] == 'api-beta'
    assert first['total'] == second['total'] == 2
    assert second['page'] == 2 and second['page_size'] == 1
    beyond = api.get('/api/v1/destinations',params={'category':'river','page_size':1,'page':3}).json()
    assert beyond['items'] == [] and beyond['total'] == 2


def test_empty_search_and_no_match(api, published):
    assert api.get('/api/v1/destinations',params={'q':'  '}).json()['total'] == 5
    assert api.get('/api/v1/destinations',params={'q':'does not exist'}).json()['items'] == []


def test_detail_coordinates_and_null_locations(api, published):
    response = api.get('/api/v1/destinations/api-alpha')
    assert response.status_code == 200
    assert response.json()['latitude'] == pytest.approx(33.994622)
    assert response.json()['longitude'] == pytest.approx(-84.333933)
    empty = api.get('/api/v1/destinations/api-beta').json()
    assert empty['latitude'] is None and empty['longitude'] is None
    assert 'reviewed_fields' not in response.json() and 'status' not in response.json()


@pytest.mark.parametrize('slug', ['missing','api-hidden-draft','api-hidden-needs-review'])
def test_unknown_and_unapproved_slugs_have_identical_errors(api, published, slug):
    response = api.get(f'/api/v1/destinations/{slug}')
    assert response.status_code == 404
    assert response.json() == {'detail':'Destination not found'}


@pytest.mark.parametrize('params', [dict(category='invalid'),dict(category='River'),dict(page=0),
    dict(page=-1),dict(page='abc'),dict(page_size=0),dict(page_size=101),dict(q='x'*161)])
def test_invalid_filters_and_pagination(api, params):
    assert api.get('/api/v1/destinations',params=params).status_code == 422


def test_status_query_cannot_bypass_publication_filter(api, published):
    response = api.get('/api/v1/destinations',params={'status':'needs_review'})
    assert response.json()['total'] == 5
    assert all('hidden' not in item['slug'] for item in response.json()['items'])


def test_categories_are_static_and_route_is_not_shadowed(api):
    response = api.get('/api/v1/destinations/categories')
    assert response.status_code == 200
    assert set(response.json()['categories']) == CATEGORIES
    assert {category.value for category in DestinationCategory} == CATEGORIES


def test_api_does_not_modify_catalog(api, published, db):
    before = db.execute(text('SELECT to_jsonb(d) FROM destinations d ORDER BY slug')).all()
    api.get('/api/v1/destinations')
    api.get('/api/v1/destinations/api-alpha')
    assert db.execute(text('SELECT to_jsonb(d) FROM destinations d ORDER BY slug')).all() == before
    assert api.post('/api/v1/destinations').status_code == 405


def test_real_request_session_blocks_writes(integration_engine):
    app = create_app(Settings(database_url=str(integration_engine.url.render_as_string(hide_password=False))))
    @app.get('/test-write')
    def try_write(session: Session = Depends(get_session)):
        session.execute(text("UPDATE destinations SET name='Must not change'"))
    with TestClient(app) as client:
        assert client.get('/test-write').status_code == 503
        assert client.get('/api/v1/destinations').json()['total'] == 0


def test_health_cors_and_openapi_without_database():
    app = create_app(Settings(database_url='postgresql+psycopg://unused/pathways'))
    with TestClient(app) as client:
        response = client.get('/api/v1/health',headers={'Origin':'http://localhost:5173'})
        assert response.json() == {'status':'ok'}
        assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
        assert 'access-control-allow-origin' not in client.get('/api/v1/health',headers={'Origin':'https://untrusted.example'}).headers
        preflight = client.options('/api/v1/destinations',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
        assert preflight.status_code == 200
        assert client.options('/api/v1/destinations',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST'}).status_code == 400
        schemas = client.get('/openapi.json').json()['components']['schemas']
        assert 'reviewed_fields' not in schemas['DestinationResponse']['properties']


def test_database_error_does_not_leak_internal_details():
    app = create_app(Settings(database_url='postgresql+psycopg://unused/pathways'))
    def broken_session():
        raise SQLAlchemyError('SECRET credentials and SQL')
        yield
    app.dependency_overrides[get_session] = broken_session
    with TestClient(app) as client:
        response = client.get('/api/v1/destinations')
        assert response.status_code == 503
        assert response.json() == {'detail':'Catalog temporarily unavailable'}


@pytest.mark.parametrize('origins', [('*',),('http://localhost:5173/path',),('https://user:secret@example.com',)])
def test_invalid_cors_configuration_is_rejected(origins):
    with pytest.raises(ValueError):
        Settings(database_url='postgresql+psycopg://localhost/pathways',cors_origins=origins)


def test_environment_configuration_does_not_reveal_password(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://user:secret@localhost/pathways')
    monkeypatch.setenv('CORS_ORIGINS','http://localhost:5174, http://127.0.0.1:5174')
    settings = get_settings()
    assert settings.cors_origins == ('http://localhost:5174','http://127.0.0.1:5174')
    assert 'secret' not in repr(settings)
