"""Idempotent destination seed importer. Run from backend with: python -m app.db.seed."""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from geoalchemy2.elements import WKTElement
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Destination, DestinationEntrance, DestinationSource, DestinationImage

ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = ROOT / "data" / "seed"
CATEGORIES = {"waterfall", "lake", "gorge", "forest", "river", "coast", "mountain", "garden", "park"}
REGIONS = {"north", "northeast", "northwest", "metro_atlanta", "central", "west", "south", "coastal"}


def reject_review_claims(record):
    """Seeds supply candidates, never manual review metadata or field locks."""
    if record.get("reviewed_fields") not in (None, []):
        raise ValueError("Seeds cannot set reviewed field locks")
    if record.get("coordinate_review_status", "pending") != "pending":
        raise ValueError("Seeds cannot assert coordinate review")
    if any(record.get(k) is not None for k in (
        "coordinate_reviewed_at", "coordinate_reviewed_by", "coordinate_review_notes", "verified_at"
    )):
        raise ValueError("Seeds cannot supply manual review metadata")


def seed_values(obj, values):
    """Fill gaps only; preserve legacy manual edits and reviewed null values."""
    if obj is None:
        return values
    locked = set(obj.reviewed_fields or [])
    return {key: value for key, value in values.items()
            if key not in locked and getattr(obj, key) is None and value is not None}


def point(lat, lon):
    if lat is None and lon is None:
        return None
    if lat is None or lon is None:
        raise ValueError("Both latitude and longitude are required together")
    if isinstance(lat, bool) or isinstance(lon, bool) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise ValueError("Coordinates must be numbers")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid WGS84 latitude/longitude")
    # Basic Georgia bounding box, not a substitute for border/entrance verification.
    if not (30.3 <= lat <= 35.1 and -85.7 <= lon <= -80.7):
        raise ValueError("Coordinates outside broad Georgia bounding box")
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def require_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {value!r}")
    return value


def load_json(name):
    data = json.loads((SEED_DIR / name).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{name} must be a JSON array")
    return data


def validate(records, entrances, sources, images):
    slugs = set()
    for d in records:
        reject_review_claims(d)
        slug = d["slug"]
        if slug in slugs or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 160:
            raise ValueError(f"Duplicate/invalid slug: {slug}")
        slugs.add(slug)
        if not d["name"].strip() or len(d["name"]) > 160 or d["category"] not in CATEGORIES or d["region"] not in REGIONS or d.get("state", "GA") != "GA":
            raise ValueError(f"Invalid destination: {slug}")
        if d.get("status", "draft") not in {"draft", "needs_review"}:
            raise ValueError(f"Seed importer cannot publish a verified destination: {slug}")
        point(d.get("latitude"), d.get("longitude"))
        if d.get("official_website"):
            require_url(d["official_website"])
    entrance_keys, primaries = set(), set()
    for e in entrances:
        reject_review_claims(e)
        if not e["name"].strip() or len(e["name"]) > 120:
            raise ValueError("Invalid entrance name")
        if e.get("point_kind", "unknown") not in {"unknown", "gate", "parking", "visitor_center", "trailhead"}:
            raise ValueError("Invalid entrance point kind")
        if e.get("coordinate_source_url"):
            require_url(e["coordinate_source_url"])
        slug = e["destination_slug"]
        if slug not in slugs:
            raise ValueError(f"Entrance references unknown destination: {slug}")
        key = (slug, e["name"])
        if key in entrance_keys:
            raise ValueError(f"Duplicate entrance: {key}")
        entrance_keys.add(key)
        if e.get("is_primary", False):
            if slug in primaries:
                raise ValueError(f"Multiple primary entrances: {slug}")
            primaries.add(slug)
        if e.get("routing_status", "untested") != "untested" or e.get("verified_at") is not None:
            raise ValueError("Seed importer must not assert successful routing or verification")
        point(e.get("latitude"), e.get("longitude"))
    source_keys = set()
    for s in sources:
        reject_review_claims(s)
        if s["destination_slug"] not in slugs or s["source_type"] not in {"georgia_dnr", "nps", "osm", "other"}:
            raise ValueError(f"Invalid source: {s}")
        require_url(s["source_url"])
        key = (s["destination_slug"], s["source_url"])
        if key in source_keys:
            raise ValueError(f"Duplicate source: {key}")
        source_keys.add(key)
    for im in images:
        if im["destination_slug"] not in slugs:
            raise ValueError("Image references unknown destination")
        require_url(im["image_url"])
        if not im.get("license"):
            raise ValueError("Every imported image must have an explicit license")
    return slugs


def upsert(session, model, keys, values):
    obj = session.scalar(select(model).filter_by(**keys).with_for_update())
    values = seed_values(obj, values) if hasattr(model, "reviewed_fields") else values
    if obj is None:
        obj = model(**keys)
        session.add(obj)
    for field, value in values.items():
        setattr(obj, field, value)
    session.flush()
    return obj


def import_seeds(session, dry_run=False):
    records = load_json("destinations.json")
    entrances = load_json("entrances.json")
    sources = load_json("sources.json")
    images = load_json("images.json")
    validate(records, entrances, sources, images)
    # All validation happens before the first write. Transaction rollback on failure.
    by_slug = {}
    for d in records:
        slug = d["slug"]
        obj = session.scalar(select(Destination).where(Destination.slug == slug).with_for_update())
        if obj is not None and obj.status == "verified":
            # Do not downgrade or overwrite manually approved destination data.
            by_slug[slug] = obj
            continue
        values = {k: d.get(k) for k in ("name", "category", "region", "city", "description", "official_website", "access_notes")}
        values["state"] = d.get("state", "GA")
        values["status"] = d.get("status", "needs_review")
        if d.get("latitude") is not None:
            values["location"] = point(d["latitude"], d["longitude"])
        by_slug[slug] = upsert(session, Destination, {"slug": slug}, values)
    for e in entrances:
        dest = by_slug[e["destination_slug"]]
        # Do not overwrite previously manually verified entrance information.
        existing = session.scalar(select(DestinationEntrance).filter_by(destination_id=dest.id, name=e["name"]).with_for_update())
        if existing is not None and (existing.verified_at is not None or existing.routing_status != "untested" or existing.coordinate_review_status != "pending"):
            continue
        values = {"address": e.get("address"), "is_primary": bool(e.get("is_primary", False)), "routing_status": "untested"}
        values["point_kind"] = e.get("point_kind", "unknown")
        values["coordinate_source_url"] = e.get("coordinate_source_url")
        if existing is None and values["is_primary"] and session.scalar(select(DestinationEntrance.id).where(DestinationEntrance.destination_id == dest.id, DestinationEntrance.is_primary.is_(True))):
            # Preserve a primary arrival point already chosen in the database.
            values["is_primary"] = False
        if e.get("latitude") is not None:
            values["location"] = point(e["latitude"], e["longitude"])
        upsert(session, DestinationEntrance, {"destination_id": dest.id, "name": e["name"]}, values)
    for s in sources:
        dest = by_slug[s["destination_slug"]]
        existing = session.scalar(select(DestinationSource).filter_by(destination_id=dest.id, source_url=s["source_url"]))
        if existing is None:
            upsert(session, DestinationSource, {"destination_id": dest.id, "source_url": s["source_url"]}, {
                "source_type": s["source_type"], "source_reference": s.get("source_reference"), "verified_at": None,
            })
    for im in images:
        dest = by_slug[im["destination_slug"]]
        existing = session.scalar(select(DestinationImage).filter_by(destination_id=dest.id, image_url=im["image_url"]))
        if existing is None:
            upsert(session, DestinationImage, {"destination_id": dest.id, "image_url": im["image_url"]}, {
                "attribution": im.get("attribution"), "license": im["license"], "is_cover": bool(im.get("is_cover", False)),
            })
    if dry_run:
        session.rollback()
    else:
        session.commit()
    return len(records), len(entrances), len(sources), len(images)


def main():
    parser = argparse.ArgumentParser(description="Import Pathways Georgia seed destinations")
    parser.add_argument("--dry-run", action="store_true", help="Validate and rollback database writes")
    args = parser.parse_args()
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        parser.error("DATABASE_URL environment variable is required")
    engine = create_engine(url)
    try:
        with Session(engine) as session:
            counts = import_seeds(session, dry_run=args.dry_run)
        print(f"{'Validated (rolled back)' if args.dry_run else 'Imported'}: {counts[0]} destinations, {counts[1]} entrances, {counts[2]} sources, {counts[3]} images")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
