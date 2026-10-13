from types import SimpleNamespace
import pytest
from app.db.seed import load_json, seed_values, validate


def test_reviewed_null_and_existing_manual_values_are_preserved():
    obj = SimpleNamespace(reviewed_fields=['description'], description=None,
                          name='Manual name', city=None)
    assert seed_values(obj, {'description': 'Seed text', 'name': 'Seed name', 'city': 'Town'}) == {'city': 'Town'}


@pytest.mark.parametrize('field,value', [
    ('reviewed_fields', ['location']), ('coordinate_review_status', 'reviewed'),
    ('coordinate_review_status', 'rejected'), ('coordinate_reviewed_at', '2026-10-12'),
    ('coordinate_reviewed_by', 'reviewer'), ('coordinate_review_notes', 'approved'),
    ('verified_at', '2026-10-12'), ('routing_status', 'passed'),
])
def test_seed_cannot_supply_review_or_routing_claims(field, value):
    entrances = load_json('entrances.json')
    entrances[0][field] = value
    with pytest.raises(ValueError):
        validate(load_json('destinations.json'), entrances, [], [])


def test_seed_provenance_is_candidate_only():
    entrances = load_json('entrances.json')
    entrances[0].update(point_kind='gate', coordinate_source_url='https://www.nps.gov/chat/')
    validate(load_json('destinations.json'), entrances, [], [])
    entrances[0]['coordinate_source_url'] = 'not-a-url'
    with pytest.raises(ValueError):
        validate(load_json('destinations.json'), entrances, [], [])
