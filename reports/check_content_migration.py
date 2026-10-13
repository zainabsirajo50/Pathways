"""Apply additive content migration and assert catalog/review data are unchanged."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from app.config import get_settings
import os
backend = Path(__file__).resolve().parents[1] / 'backend'
settings = get_settings()
os.environ['DATABASE_URL'] = settings.database_url
engine = create_engine(settings.database_url, hide_parameters=True)
tables = ('destinations','destination_entrances','destination_sources','destination_images','route_verifications')
def fingerprints():
    with engine.connect() as c:
        return {table: c.execute(text(f'SELECT count(*), md5(coalesce(string_agg(t::text, chr(10) ORDER BY id), \'\')) FROM {table} t')).one() for table in tables}
before = fingerprints()
cfg = Config(str(backend / 'alembic.ini'))
cfg.set_main_option('script_location', str(backend / 'alembic'))
command.upgrade(cfg,'head')
assert fingerprints() == before, 'Existing catalog/review data changed during migration'
command.check(cfg)
with engine.connect() as c:
    assert c.scalar(text('SELECT count(*) FROM destinations')) == 10
    assert c.scalar(text("SELECT count(*) FROM destinations WHERE status='needs_review'")) == 10
    assert c.scalar(text('SELECT count(*) FROM destination_content_reviews')) == 0
    assert c.scalar(text('SELECT count(*) FROM destination_publication_audits')) == 0
    print('Development migration:',c.scalar(text('SELECT version_num FROM alembic_version')))
print('Preserved ten needs_review destinations and all existing entrances, sources, images, route history and locks. No reviews or approvals created.')
engine.dispose()
