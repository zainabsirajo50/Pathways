# Pathways — Destination Catalog Starter

Georgia nature-destination catalog with SQLAlchemy models, Alembic migrations, an idempotent JSON importer, a read-only FastAPI API, and a React Explore frontend. Explore includes Mapbox display mapping; routing is not implemented yet.

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
- 9 destinations have no entrance records; their public arrival coordinates still need verification.
- No imported images, because usage licenses have not been reviewed.
- Local migrations and seed imports have been run; no real route requests have been made.

## Data conventions
- Geography points use EPSG:4326; `POINT(longitude latitude)`.
- Only publicize destinations after verifying their details and routable entrance.
- Source URLs in `sources.json` are reference starting points; a source row does not imply individual record verification.
- Importer validates a broad Georgia bounding box, not precise state boundaries.
- Multi-table publication checks belong in a future service layer; `verified` is not assigned by the importer.
- Existing image metadata is not overwritten. Future image imports require verified rights and attribution.

## Future improvements
- Add a service that enforces promotion to `verified` only after sources and entrances are reviewed.
- Add provider routing checks using the route-test history table.
- Extend integration coverage as review and publication services are added.
- Consider a more granular destination taxonomy (primary category plus tags).

## Destination verification workflow

Migration `0002_verification_infrastructure` is additive. It keeps catalog rows,
IDs, coordinates, and existing status values. New entrances default to
`point_kind = unknown` and `coordinate_review_status = pending`. Existing data
is not automatically approved or assigned provenance from the research report.
The original migration remains unchanged.

### Coordinate evidence

`Destination.location` is a display location, never an implicit routing endpoint.
An entrance now records:

- `point_kind`: unknown, gate, parking, visitor_center, or trailhead.
- `coordinate_source_url`: the HTTP(S) evidence URL for this specific point.
- `coordinate_review_status`: pending, reviewed, or rejected.
- `coordinate_reviewed_at`, `coordinate_reviewed_by`, and `coordinate_review_notes`.

A reviewed coordinate requires a location, source URL, named point kind, reviewer,
and review timestamp. These constraints require evidence metadata; they cannot
prove that the source is authoritative or the road is publicly accessible.
A reviewer must establish that separately. Coordinate review does not approve
routing or publish a destination. The legacy `verified_at` field remains for
compatibility; new coordinate reviews use the explicitly named review fields.

Changing location, point kind, or source URL resets coordinate review to pending,
clears reviewer/timestamps (including legacy `verified_at`), and resets
`routing_status` to untested through a PostgreSQL trigger. Notes and historical
route tests are retained. Set the candidate point/provenance first, flush and
refresh, then record a separate manual review; a combined coordinate-change and
approval update is deliberately reset to pending. ORM users must refresh after
these updates to see database-triggered changes.

### Protecting manual edits from seed imports

Destinations and entrances have a `reviewed_fields` JSON array of field names.
Reviewers can lock individual fields, including values intentionally left NULL.
For example, locking `description` protects an intentionally empty description
without marking the entire destination verified. SQL constraints reject unknown
field names; ORM list edits are tracked by SQLAlchemy MutableList.

The importer fills only NULL, unlocked fields on existing rows. It does not clear
values or replace populated fields, even if they have no review lock; this also
protects manual edits made before field-level locks existed. Seed changes to an
existing populated value require a separate reviewed edit. New rows still receive
seed values. Primary entrance choices already stored are preserved. Reviewed,
rejected, previously verified, or route-tested entrances are left untouched.
Verified destinations remain untouched. Existing sources and image metadata
retain their previous protection.

Seed files cannot supply field locks, reviewer metadata, coordinate review claims,
source verification timestamps, verified destination status, or routing results.
An evidence URL and point kind on a new seed entrance remain candidate metadata.
The importer does not read or write route history. No coordinates are inferred
from the verification report, and none of the nine general park GPS references
has been imported as an entrance.

Field locks currently protect against the seed importer, not arbitrary SQL or
future administrative APIs. Reviewers must use deliberate edits for corrections.
Entrance identity is still destination/name; renaming a seed entrance creates a
new candidate rather than renaming a reviewed entrance. Primary/cover changes
should be performed separately from bulk seed imports.

### Route verification history

`route_verifications` stores one test attempt per row, linked to an entrance:
provider, driving/walking travel mode, origin/destination latitude and longitude,
result (passed, failed, error, manual_review), timezone-aware `tested_at`, and
optional `error_details`. Error results require nonempty details. Coordinate
ranges and required fields are checked in PostgreSQL. Origins may be outside
Georgia; route coordinates therefore use WGS84 ranges, not the seed bounding box.

Record the exact requested points and actual test time, with a new row per test;
do not reinterpret a historical result after an entrance moves. The database
allows administrative corrections to history; immutable audit storage and snapped
provider endpoints are future extensions. Tests against old coordinates remain
historical evidence, never current approval. Inserting a passed result does not
update any entrance or destination status. Driving and walking evidence are
independent; the legacy entrance routing_status is not a per-mode readiness check.
Future publication logic must evaluate current coordinate review and current
mode-specific route evidence explicitly. No provider client or Mapbox integration
is included in this milestone.

Deleting a catalog entrance cascades to its route history, matching existing
catalog deletion behavior. Migration downgrade preserves catalog rows but deletes
new review metadata and route history; do not downgrade a reviewed database
without an appropriate backup.

### Tests and migrations on Windows

From `backend/`, use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m app.db.seed --dry-run
```

Without TEST_DATABASE_URL, database tests are explicitly skipped; unit tests still
run. Integration tests require an **empty disposable** PostgreSQL database whose
name starts with `pathways_test_`. They never use DATABASE_URL as a fallback and
exercise original-migration upgrade, populated-catalog upgrade/downgrade/re-upgrade,
constraints, review locks, endpoint invalidation, dry run, and repeated imports.
They use transactions/savepoints to roll back synthetic approvals and route tests.
No test data is written to the development database.

For the local installation created in this project, this runner creates a random
disposable database, runs all tests, and removes only that database in a finally
block. It reads the administrator password from ignored `.env.admin` and connects
to localhost:5432; it is a local development helper, not a CI credential mechanism:

```powershell
.\.venv\Scripts\python.exe tests/run_db_tests.py
```

Alternatively set TEST_DATABASE_URL to an empty disposable database with extension
creation permissions and run pytest. Keep credentials out of command history and
Git. DATABASE_URL, `.env`, `.env.admin`, and `.venv` remain local configuration.


## Read-only FastAPI catalog API

From `backend/`, install the updated dependencies and start Uvicorn:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive documentation. Stop the server with
Ctrl+C. Startup does not migrate, seed, or approve data. Existing migrations 0001
and 0002 must already be applied; this API milestone needs no new migration.

Configuration is loaded from `backend/.env` regardless of the current directory;
environment variables take precedence. DATABASE_URL must use
`postgresql+psycopg://` and identify a database. Credentials remain in ignored
local files. CORS_ORIGINS is a comma-separated list of exact HTTP(S) origins
without paths. Defaults are http://localhost:5173 and http://127.0.0.1:5173 for
Vite. Set a different port explicitly if Vite changes ports. CORS permits GET
requests and preflight, with no cookies/credentialed requests or wildcard origins.
CORS is a browser policy, not authentication or authorization.

### Endpoints

- `GET /api/v1/health`: returns `{"status":"ok"}`. This is application liveness,
  not database readiness; it intentionally performs no database query.
- `GET /api/v1/destinations`: returns `items`, filtered `total`, `page`, and
  `page_size`. Optional `q` searches names case-insensitively, trimming surrounding
  whitespace and treating percent/underscore literally. Empty search is no filter.
- `GET /api/v1/destinations/categories`: returns a `categories` array containing
  the supported taxonomy, even if there are no published destinations. It does
  not reveal categories/counts from private records.
- `GET /api/v1/destinations/{slug}`: returns one published destination or 404.
  Missing, draft, and needs_review slugs return the same generic 404 response.
  The static categories route is registered before the slug route.

Example: `/api/v1/destinations?q=falls&category=waterfall&page=1&page_size=10`.
Categories are waterfall, lake, gorge, forest, river, coast, mountain, garden,
and park. Category values are case-sensitive; invalid values return 422. Page
numbers start at 1 and are capped at 1,000,000; page sizes default to 20 and range
from 1 to 100. Search strings are limited to 160 characters. Invalid bounds/types
return 422. Beyond-the-end pages return empty items with the filtered total.
Results sort by lowercase name, then slug, for stable offset pagination.

Only `status = verified` rows are queried for lists, totals, and details.
There is no status override or administrative endpoint. The current ten local
needs_review records therefore produce an empty public catalog; this is expected.
No record is approved just to populate this API.

Responses whitelist slug, name, category, region, city, state, description,
official_website, access_notes, latitude, and longitude through Pydantic schemas.
Coordinates are projected by PostGIS from `Destination.location`, with latitude
from Y and longitude from X. Missing locations return null for both. These are
**display points**, not visitor entrance/routing endpoints. Entrances, route
history, source review metadata, field locks, internal IDs, and verification
statuses are not returned. Image and entrance responses are deferred until their
publication rules are defined.

Each database-backed request uses a synchronous, request-scoped SQLAlchemy session
and a PostgreSQL read-only transaction, rolled back and closed on completion.
Synchronous handlers match the existing psycopg/ORM code; no async driver or new
schema is introduced. Database errors return a sanitized 503 response without
SQL or connection credentials. The engine pool is disposed at server shutdown.

### API tests

Run the **full** suite with the existing disposable-database helper:

```powershell
.\.venv\Scripts\python.exe tests/run_db_tests.py
```

API publication examples exist only inside rollback-protected fixtures in the
isolated test database. Tests cover filtering, literal search, stable pagination,
empty results, publication restrictions, response field whitelists, PostGIS
latitude/longitude projection, validation errors, CORS, sanitized database errors,
and rejection of writes by real API request sessions. Development data is not
approved or modified by these tests. Plain pytest without TEST_DATABASE_URL skips
database-dependent tests rather than falling back to the development database.

## React frontend and Explore preview

The `frontend/` application uses React, TypeScript, Vite, Tailwind CSS 4,
React Router, and TanStack Query. Node.js 22.12+ (or a current supported LTS)
and pnpm are required. Install pnpm using your preferred Node package-manager
setup if it is not already available. The committed pnpm lockfile pins dependencies.

Start the backend as described above, then in a second terminal:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Open http://127.0.0.1:5173/explore. Vite uses a strict port and proxies `/api`
to http://127.0.0.1:8000. Stop either server with Ctrl+C in its terminal.
On this computer, Node and pnpm are available through Codex's bundled runtime
rather than the global PATH. From the project root you can instead run
`./frontend/start-local.ps1`; it uses installed tools or that existing runtime,
installs locked project dependencies, and starts Vite without installing global
software. Do not run a second copy while port 5173 is already in use.
The workspace configuration permits only esbuild's required dependency build
script. The project uses pnpm 11, pinned in `package.json`.
The production build needs an HTTP host with an SPA fallback to `index.html`.
Use a reverse proxy for `/api`, or set public `VITE_API_BASE_URL` before building
(e.g. https://api.example.com) and configure the backend's exact CORS origin.
Never put database credentials or secret keys in `VITE_` variables: they are
embedded in the browser bundle. Optional local configuration belongs in ignored
`frontend/.env.local`; `frontend/.env.example` is safe to copy.

Explore searches destination **names** on form submission, supports the API's
category taxonomy, and paginates six cards per page. Filters and page changes
clear selection; the selected card's public data is shown in the adjacent panel.
Queries pass cancellation signals and use separate caches per data mode. Only
GET requests are made. Categories are loaded from the API rather than inferred
from private records. Loading, retryable errors, and an empty public catalog
have explicit states. Submitted search, category, page and development preview mode are stored in URL query parameters and survive detail-page navigation and reload.

### Development fixtures

The current public catalog is empty because the ten database candidates still
need review. The frontend preserves that empty state. In development only,
choose **Preview fixtures** or open
http://127.0.0.1:5173/explore?preview=1 to opt into the separate preview dataset.
The banner explicitly labels sample content as unverified and not route-ready.
Choose **Use public API** to return to real API results. There is no automatic
fixture fallback after an API error or an empty response.

Fixtures are in `frontend/src/dev/fixtures.ts`, not seed files or database rows.
Only Island Ford includes an NPS-published entrance reference, explicitly routing-untested; the other nine have null coordinates. They contain no approved imagery or review claims. They are loaded
only through a development-guarded dynamic import; Vite removes the fixture
module and preview controls from production builds. `?preview=1` has no effect
in production. These examples are not destination verification evidence.

Cards use original, labeled decorative illustrations, not destination photos.
The right panel uses Mapbox Outdoors with markers only for valid display coordinates.
Public latitude/longitude values, when available, are explicitly labeled display
points and never treated as arrival coordinates. No directions, authentication, or backend trip persistence is included.
On mobile the catalog and details panel stack vertically.

### Frontend checks

From `frontend/`:

```powershell
pnpm test
pnpm build
pnpm preview
```

Tests exercise real query hooks and the API client with mocked HTTP responses:
filtering, pagination, selection, loading/error/retry/empty states, explicit
fixture isolation, production preview restrictions, and malformed API responses.
Production build type-checks the application. `pnpm preview` serves that build
locally and inherits the local API proxy; an actual deployment must configure
API hosting as above. Preview is a validation server, not a production server.
Backend tests remain independent and run against the disposable database.


## Mapbox display map

Mapbox GL JS uses the Outdoors v12 style and an initial Georgia overview.
The 40/60 workspace, cards, filters, pagination and compact preview are retained.

Create `frontend/.env.local` (ignored by Git), and add your **public** token:

```dotenv
VITE_MAPBOX_ACCESS_TOKEN=pk.YOUR_PUBLIC_TOKEN
```

Restart `pnpm dev` (or `./frontend/start-local.ps1` from the repository root)
after changing environment variables. For deployment, supply the same variable
at build time. Vite embeds public tokens in the browser bundle; never use an
`sk.` secret token here. Obtain a token from your own Mapbox account and configure
its allowed URLs for local development and your deployment domain as appropriate.
See [Mapbox token documentation](https://docs.mapbox.com/help/dive-deeper/access-tokens/).
Map loading makes requests to Mapbox and uses your account's map usage allowance.

Without a public token, Explore shows setup instructions while the list and
preview continue working. Map loading, WebGL/token/network errors with retry,
and empty coordinate results have explicit states. A ResizeObserver keeps the
map sized to the existing responsive panel. Attribution and navigation controls
remain visible. Markers are native keyboard-accessible buttons; the list offers
an equivalent way to select every destination. Reduced-motion settings disable
selection animation. View Details opens the responsive destination details route.

Only records on the currently displayed page with **both** finite WGS84 latitude
and longitude get markers. Search/filter/page changes replace that marker set.
Selecting a card highlights its marker and centers the map when coordinates exist;
selecting a marker selects and scrolls its card into view. Closing the preview
clears selection, preserving the previous behavior. Missing coordinates never
hide a card or move the map to an invented location. Display points are not
entrances and provide no routing approval. Only the development Island Ford fixture carries the supplied NPS entrance reference (33.994622, -84.333933); routing is untested and the other nine retain null coordinates.
Fixtures remain development-only and absent from production builds.

Run `pnpm test` and `pnpm build` from `frontend/`. Map tests use a mocked renderer
and synthetic coordinates solely within tests, covering validation, marker
replacement/cleanup, selection, missing coordinates, setup and errors/retry.
These tests do not validate real tiles, real visitor entrances or routes. Live
map rendering requires a working public token, network access and WebGL.




The production build runs scripts/check-production-fixtures.mjs after bundling and fails if Island Ford fixture identity, its supplied coordinate literals, or its NPS evidence URL appear in browser JavaScript. Marker validation covers actual Explore selection/search/category/pagination interactions with a mocked Mapbox renderer; live browser checks confirm the entrance reference centers and selects correctly. This is map-display validation only, not routing verification.


## Destination details

`/destinations/:slug` loads `GET /api/v1/destinations/{slug}` in public mode.
Unapproved and unknown records receive the same unavailable page on API 404;
there is no fallback to seed or fixture data. In development only, `?preview=1`
loads the matching fixture through the existing guarded dynamic import. Preview
banners, separate query keys and the production fixture-leak check remain active.

Card titles and the map preview's **View Details** link open details. Submitted
Explore search/category/page/preview query parameters travel with those links;
**Back to Explore** restores them. Card and marker selection continue separately.
The page displays description, category, locality, access notes and an HTTP(S)
official link where supplied. Missing visitor information has explicit messages.
The current API does not expose approved-image metadata, so all details artwork
uses our labeled illustration; adding real photos requires a future approved
image response contract rather than loading unreviewed photos from seed data.

A compact Mapbox view appears only when both coordinates are valid. These markers
never establish route readiness. Island Ford preview identifies its published
entrance reference and untested routing status. Destinations without coordinates
remain available and show a location-unavailable message. Map loading and errors
use the existing map states. **Add to Trip** creates an browser-local draft stop; no trip API, auth or directions requests are made.

`pnpm test` covers single-record API loading, missing fields, unknown/unapproved
records, fixture restrictions, fixture provenance, details navigation and restored
Explore filters/pagination. `pnpm build` type-checks and checks production fixture
isolation. Local startup and Mapbox token setup remain unchanged above.


## Client-side Trip Builder

Open `/trips/new` for the public draft; development `/trips/new?preview=1` uses
an entirely separate fixture draft. Add destinations using **Add to Trip** on
Explore cards or details, then **Open draft** or **Day trips**. A destination can
appear once per draft. Trips have an editable name and optional date. New stops
start with 60 planned visiting minutes, an editable planning default, not an
estimated required visit duration. Enter whole minutes from 1 through 1440;
invalid edits display an error and retain the previous valid duration.

Use Up/Down buttons to reorder and Remove to delete a stop. These controls are
keyboard-accessible and do not require drag-and-drop. The summary totals planned
visit minutes only; it excludes all travel time. Numbered Mapbox markers match
the full itinerary order, so an unmapped stop leaves a gap in marker numbering.
Unmapped stops remain in the list with a clear label. Selecting a marker
highlights its stop. No lines, directions, road-access claims or arrival times
are generated; Island Ford preview routing remains untested.

DraftProvider keeps separate public and fixture drafts backed by browser localStorage, retained across navigation and reload. Nothing is written to backend trip storage. The public catalog still applies
all existing publication rules. Preview mode is development-only; its stops are
never submitted to APIs, cannot mix into the public draft, and remain excluded
from production by the existing build check. Switching to the public catalog
shows its independent draft. Browser map requests are display requests only.

Frontend tests cover additions from Explore/details, duplicate prevention,
removal/reorder/duration validation, navigation retention, public/preview
separation, production preview restrictions and numbered-marker ordering with
missing coordinates. Startup remains `pnpm dev` in frontend (or the existing
Windows helper); checks remain `pnpm test` and `pnpm build`.


### Browser-local trips and My Trips

Open `/trips/new` to build a trip and `/trips` to manage saved trips. Draft name, optional date, ordered destination snapshots, and visit durations are automatically retained in localStorage during edits. Choose **Save Trip** after entering a name to create a saved copy; saving an opened trip updates that copy. Draft changes are labeled unsaved until explicitly saved. My Trips supports opening, starting a new trip, and deleting with confirmation. Replacing an unsaved draft requires confirmation. Deleting an opened saved trip retains its current draft.

Trips exist only in this browser and origin (hostname/port). They are not synced to an account or backend, and clearing browser data removes them. Public trips use `pathways.trips.v1.public`; development preview trips use `pathways.trips.v1.fixtures`. Production never loads fixture storage. No trip data is sent to an API; catalog availability checks use the selected mode only. Do not manually move storage between modes. Multiple tabs are not synchronized; use a single editing tab to avoid stale overwrites.

Versioned envelopes validate mode, dates, destination structure and coordinate ranges, unique stop slugs and trip IDs, and whole-minute durations (1–1440). Malformed or unsupported data is not overwritten automatically: an error explains the issue and **Reset browser trips** explicitly discards that mode's stored trips after confirmation. Storage failures keep draft edits in memory and report that saving failed. Stored data is not proof of destination approval or route verification.

Saved stops retain the original catalog snapshot. An availability check labels unavailable destinations or catalog failures without removing or updating a stop. Review current destination details and visitor access before visiting; map positions are snapshot references only. No route lines, travel-time estimates, account authentication, or backend trip persistence are implemented.



## Local destination content approval

Content publication (`Destination.status = verified`) means reviewed catalog content only. It does **not** approve arrival entrances, road access, driving/walking routes, or travel times. `Destination.location` is an optional display reference; public coordinates must never be treated as an arrival endpoint. Existing ten destinations remain `needs_review` until individually reviewed and explicitly approved.

### Local security

Administration is a CLI, not an HTTP endpoint. PostgreSQL authenticates the database connection, and the service verifies `session_user` against `PATHWAYS_CONTENT_REVIEW_ROLES`. An empty allowlist disables administration. Configure the intended local database role in ignored `backend/.env`, for example `PATHWAYS_CONTENT_REVIEW_ROLES=pathways` **only if that is your intended authenticated local reviewer role**. Use the existing private `DATABASE_URL`; never put passwords in command arguments, evidence files, commits, or logs. No role grants, password changes, or authentication changes are performed by this feature. Keep PostgreSQL loopback-only and password-authenticated (SCRAM rather than trust); a shared role provides shared-role attribution, not individual accountability. This CLI is for trusted local developers with database access, not remote/multi-user administration. Database owners/superusers can bypass application policy; this is not a security boundary against the database administrator.

### Content policy

A human must review name, category, Georgia region/state/locality, description, HTTPS official website, access notes, and coordinate presence/absence. Every field needs dated evidence and a note explaining source support. At least one recorded destination-specific DNR or NPS source is required, with a nonempty `source_reference`. Generic directory/root URLs and lookalike domains are insufficient. Supported authoritative hosts are `gastateparks.org` and its subdomains, `gastateparks.reserveamerica.com`, and `nps.gov` and its subdomains, with matching source types. Official operator websites may be displayed when supported by DNR/NPS evidence. Source URLs are not fetched by the CLI: a reviewer must actually inspect them and confirm destination scope and current access restrictions.

Evidence and the review itself expire for **approval purposes** after 30 days; timestamps must include a timezone and cannot be in the future. This is an initial conservative local policy, not an automated guarantee that conditions remain current. Previously published content does not automatically expire; revoke it when stale or unsafe and schedule manual revisits. Known closures must be recorded with check dates/scope in access notes. A website's existence alone never constitutes review. No descriptions, sources, or coordinate evidence are generated by approval.

An explicitly reviewed absent display coordinate is allowed: the destination can be listed without a map marker. A present point requires exact numeric latitude/longitude evidence and `kind: display_reference`, within WGS84 and the existing broad Georgia bounds. Broad bounds are only validation, not proof of park membership. Gate/parking coordinates belong to the separately reviewed entrance model; no point is copied from entrances by these services. All entrance review fields, primary selection, routing statuses, and route-test history remain untouched.

### Workflow

From `backend/`, apply `alembic upgrade head` (new migration `0003_content_publication`; original migrations are unchanged), then use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m app.content_admin inspect vogel-state-park
.\.venv\Scripts\python.exe -m app.content_admin validate vogel-state-park --evidence-file reviewed-evidence.json
.\.venv\Scripts\python.exe -m app.content_admin review vogel-state-park --evidence-file reviewed-evidence.json --confirm
# Substitute the review UUID printed by the previous command; never approve an unreviewed seed.
.\.venv\Scripts\python.exe -m app.content_admin approve vogel-state-park --review-id REVIEW_UUID --reason "Individually reviewed catalog content" --confirm
.\.venv\Scripts\python.exe -m app.content_admin revoke vogel-state-park --reason "Visitor information needs another review" --confirm
```

`inspect` and `validate` do not write. `review` records an immutable current-content/source snapshot and merges field locks (including reviewed nulls); it does not publish. Existing locks are never removed. Content/source corrections must be made through an explicitly reviewed local data-edit process before these commands; this milestone does not add a bulk updater or modify the research report/seed proposals. `approve` accepts only a `needs_review` destination with a current matching review, complete locks, and a reason. It changes status and adds the authenticated actor/review/reason audit in one transaction. `revoke` returns a verified destination to `needs_review`, retaining all locks/history. Reapproval after revocation/invalidation requires a new review. Repeat approvals/revocations are rejected rather than generating duplicate actions.

Evidence JSON contains `notes` and exactly these keys under `evidence`: `name`, `category`, `region`, `city`, `state`, `description`, `official_website`, `access_notes`, `location`. Each non-coordinate field uses this structure, with its own actual check timestamp and explanation:

```json
{"source_url":"https://gastateparks.org/Vogel","checked_at":"2026-10-12T16:00:00-04:00","note":"Explain how the reviewed source supports this field."}
```

For an absent coordinate use:

```json
{"kind":"absent","source_url":null,"checked_at":"2026-10-12T16:00:00-04:00","note":"Explicitly reviewed: no approved display coordinate is stored."}
```

For a present coordinate use `kind: display_reference`, a recorded authoritative `source_url`, `checked_at`, an explanatory `note`, and the exact stored numeric `latitude` and `longitude`. Do not estimate them. These snippets are formats, not pre-approved evidence; the example timestamp must be replaced with the actual review time. Store local evidence outside seeds; never add publication claims to seed files.

Content or field-lock changes to a published row automatically return it to `needs_review` and append an `invalidate` audit. Source insert/update/delete does likewise. Immutable reviews/audits reject UPDATE/DELETE; their restrictive foreign keys preserve history against ordinary catalog deletion. Transaction rollback undoes both status and audit. Source/content snapshots prevent approval of stale reviews. Existing entrance invalidation safeguards remain independent. No new metadata is exposed by public API schemas.

Tests run with `.\.venv\Scripts\python.exe tests/run_db_tests.py`; this creates a dedicated disposable `pathways_test_*` database, exercises original-to-head migrations and downgrade/re-upgrade compatibility, and runs Alembic's metadata check. Never downgrade development to test migration reversal: it would discard the new history tables.

