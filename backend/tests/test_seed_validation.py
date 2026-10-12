import pytest
from app.db.seed import load_json, point, validate


def test_seed_files_are_consistent():
    validate(*(load_json(f) for f in ("destinations.json", "entrances.json", "sources.json", "images.json")))


def test_invalid_coordinates_rejected():
    with pytest.raises(ValueError):
        point(200, -84)
    with pytest.raises(ValueError):
        point(33, None)
    with pytest.raises(ValueError):
        point(40, -84)


def test_point_is_longitude_first():
    assert str(point(33.994622, -84.333933).data) == "POINT(-84.333933 33.994622)"


def test_seed_cannot_claim_verified():
    records = load_json("destinations.json")
    records[0]["status"] = "verified"
    with pytest.raises(ValueError):
        validate(records, [], [], [])
