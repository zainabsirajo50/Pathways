import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db.seed import import_seeds, load_json


@pytest.fixture(scope='session')
def integration_engine():
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to a dedicated disposable PostgreSQL/PostGIS database')
    database = make_url(url).database
    if not database or not database.startswith('pathways_test_'):
        pytest.fail('Integration database name must start with pathways_test_; never use the development database')
    engine = create_engine(url)
    with engine.connect() as c:
        assert c.scalar(text('SELECT current_database()')) == database
        assert c.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='destinations'")) == 0, 'Test database must be empty'
    previous = os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL'] = url
    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'alembic'))
    try:
        command.upgrade(cfg, '0001_destination_catalog')
        with engine.begin() as c:
            for d in load_json('destinations.json'):
                c.execute(text('INSERT INTO destinations (id,slug,name,category,region,city,status) VALUES (gen_random_uuid(),:slug,:name,:category,:region,:city,:status)'), d)
            e = load_json('entrances.json')[0]
            c.execute(text("INSERT INTO destination_entrances (id,destination_id,name,address,location,is_primary) SELECT gen_random_uuid(),id,:name,:address,ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326)::geography,true FROM destinations WHERE slug=:destination_slug"), e)
        with engine.connect() as c:
            original = c.execute(text('SELECT id,slug,name,status FROM destinations ORDER BY slug')).all()
            original_entrance = c.execute(text('SELECT id,name,address,ST_AsText(location::geometry),routing_status,verified_at FROM destination_entrances')).all()
        command.upgrade(cfg, 'head')
        with engine.connect() as c:
            assert c.execute(text('SELECT id,slug,name,status FROM destinations ORDER BY slug')).all() == original
            assert c.execute(text('SELECT id,name,address,ST_AsText(location::geometry),routing_status,verified_at FROM destination_entrances')).all() == original_entrance
            assert c.scalar(text('SELECT count(*) FROM destinations WHERE reviewed_fields = \'[]\'::jsonb')) == 10
        # Exercise reversal only on this disposable database, never on development.
        command.downgrade(cfg, '0001_destination_catalog')
        with engine.connect() as c:
            assert c.execute(text('SELECT id,slug,name,status FROM destinations ORDER BY slug')).all() == original
            assert c.execute(text('SELECT id,name,address,ST_AsText(location::geometry),routing_status,verified_at FROM destination_entrances')).all() == original_entrance
        command.upgrade(cfg, 'head')
        with Session(engine) as session:
            import_seeds(session)
        command.check(cfg)
        yield engine
    finally:
        if previous is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous
        engine.dispose()


@pytest.fixture
def db(integration_engine):
    with integration_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode='create_savepoint') as session:
            yield session
        transaction.rollback()
