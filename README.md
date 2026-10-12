# Pathways — Destination Catalog Starter

Initial Georgia nature-destination data layer. Includes SQLAlchemy models, Alembic migration, and an idempotent JSON importer. No frontend, API, or routing integration yet.

## Prerequisites
- Python 3.11+
- PostgreSQL 15+ with PostGIS available
- A database user permitted to create the PostGIS extension (or ask your DBA to enable it beforehand)

## Local setup
From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e '.[dev]'
cp .env.example .env  # On Windows, copy manually or use Copy-Item
# Edit .env with your database credentials.
alembic upgrade head
python -m app.db.seed --dry-run
python -m app.db.seed
pytest -q
```

The seed importer is safe to rerun: destinations are matched by slug, entrances by destination/name, and sources/images by destination/URL. It does **not** delete absent records. Manually approved destination records and verified entrance coordinates are preserved. All seed destinations begin as `needs_review`; all routes begin as `untested`.

## Initial data status
- 10 Georgia destination candidate records; all need review before publication.
- 1 NPS-published Island Ford entrance coordinate, still **not route-tested**.
- 9 remaining entrances need official coordinate verification.
- No imported images, because usage licenses have not been reviewed.
- No real route requests or live database migration have been run in this artifact-generation environment.

## Data conventions
- Geography points use EPSG:4326; `POINT(longitude latitude)`.
- Only publicize destinations after verifying their details and routable entrance.
- Source URLs in `sources.json` are reference starting points; a source row does not imply individual record verification.
- Importer validates a broad Georgia bounding box, not precise state boundaries.
- Multi-table publication checks belong in a future service layer; `verified` is not assigned by the importer.
- Existing image metadata is not overwritten. Future image imports require verified rights and attribution.

## Future improvements
- Add a service that enforces promotion to `verified` only after sources and entrances are reviewed.
- Add Mapbox routing checks and store results in a dedicated route-test history table.
- Add DB integration tests for migration, constraints, upsert repeatability, and primary entrance uniqueness.
- Consider a more granular destination taxonomy (primary category plus tags).
