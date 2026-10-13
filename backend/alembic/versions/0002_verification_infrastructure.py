"""Add entrance review provenance, field locks, and route-test history.

Revision ID: 0002_verification_infrastructure
Revises: 0001_destination_catalog
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_verification_infrastructure'
down_revision = '0001_destination_catalog'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('destinations', sa.Column('reviewed_fields', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column('destination_entrances', sa.Column('reviewed_fields', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column('destination_entrances', sa.Column('point_kind', sa.String(20), nullable=False, server_default='unknown'))
    op.add_column('destination_entrances', sa.Column('coordinate_source_url', sa.Text()))
    op.add_column('destination_entrances', sa.Column('coordinate_review_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('destination_entrances', sa.Column('coordinate_reviewed_at', sa.DateTime(timezone=True)))
    op.add_column('destination_entrances', sa.Column('coordinate_reviewed_by', sa.String(160)))
    op.add_column('destination_entrances', sa.Column('coordinate_review_notes', sa.Text()))
    op.create_check_constraint('valid_destination_reviewed_fields', 'destinations', 'jsonb_typeof(reviewed_fields) = \'array\' AND reviewed_fields <@ \'["name","category","region","city","state","description","location","official_website","access_notes","status"]\'::jsonb')
    op.create_check_constraint('reviewed_coordinate_evidence', 'destination_entrances', "coordinate_review_status != 'reviewed' OR (location IS NOT NULL AND coordinate_source_url IS NOT NULL AND coordinate_reviewed_at IS NOT NULL AND length(btrim(coordinate_reviewed_by)) > 0 AND coordinate_reviewed_by IS NOT NULL AND point_kind != 'unknown')")
    op.create_check_constraint('valid_coordinate_review_status', 'destination_entrances', "coordinate_review_status IN ('pending','reviewed','rejected')")
    op.create_check_constraint('valid_coordinate_source_url', 'destination_entrances', "coordinate_source_url IS NULL OR coordinate_source_url ~ '^https?://[^/[:space:]]+'")
    op.create_check_constraint('valid_entrance_reviewed_fields', 'destination_entrances', 'jsonb_typeof(reviewed_fields) = \'array\' AND reviewed_fields <@ \'["name","address","location","is_primary","point_kind","coordinate_source_url"]\'::jsonb')
    op.create_check_constraint('valid_point_kind', 'destination_entrances', "point_kind IN ('unknown','gate','parking','visitor_center','trailhead')")
    op.create_table(
        'route_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entrance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('destination_entrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(80), nullable=False),
        sa.Column('travel_mode', sa.String(20), nullable=False),
        sa.Column('origin_latitude', sa.Float(), nullable=False),
        sa.Column('origin_longitude', sa.Float(), nullable=False),
        sa.Column('destination_latitude', sa.Float(), nullable=False),
        sa.Column('destination_longitude', sa.Float(), nullable=False),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('tested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('error_details', sa.Text()),
        sa.CheckConstraint("result != 'error' OR (error_details IS NOT NULL AND length(btrim(error_details)) > 0)", name='route_error_details_required'),
        sa.CheckConstraint('origin_latitude BETWEEN -90 AND 90 AND destination_latitude BETWEEN -90 AND 90 AND origin_longitude BETWEEN -180 AND 180 AND destination_longitude BETWEEN -180 AND 180', name='valid_route_coordinates'),
        sa.CheckConstraint('length(btrim(provider)) > 0', name='valid_route_provider'),
        sa.CheckConstraint("result IN ('passed','failed','error','manual_review')", name='valid_route_result'),
        sa.CheckConstraint("travel_mode IN ('driving','walking')", name='valid_route_travel_mode'),
    )
    op.create_index('route_verifications_entrance_tested_idx', 'route_verifications', ['entrance_id', 'tested_at'])
    op.execute("""
        CREATE FUNCTION pathways_invalidate_entrance_review() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF ST_AsEWKB(NEW.location::geometry) IS DISTINCT FROM ST_AsEWKB(OLD.location::geometry)
               OR NEW.point_kind IS DISTINCT FROM OLD.point_kind
               OR NEW.coordinate_source_url IS DISTINCT FROM OLD.coordinate_source_url THEN
                NEW.coordinate_review_status := 'pending';
                NEW.coordinate_reviewed_at := NULL;
                NEW.coordinate_reviewed_by := NULL;
                NEW.verified_at := NULL;
                NEW.routing_status := 'untested';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER invalidate_entrance_review
        BEFORE UPDATE ON destination_entrances
        FOR EACH ROW EXECUTE FUNCTION pathways_invalidate_entrance_review()
    """)


def downgrade():
    # Reverting removes new review metadata/history; destination catalog rows survive.
    op.execute('DROP TRIGGER invalidate_entrance_review ON destination_entrances')
    op.execute('DROP FUNCTION pathways_invalidate_entrance_review()')
    op.drop_table('route_verifications')
    op.drop_constraint('valid_point_kind', 'destination_entrances', type_="check")
    op.drop_constraint('valid_entrance_reviewed_fields', 'destination_entrances', type_="check")
    op.drop_constraint('valid_coordinate_source_url', 'destination_entrances', type_="check")
    op.drop_constraint('valid_coordinate_review_status', 'destination_entrances', type_="check")
    op.drop_constraint('reviewed_coordinate_evidence', 'destination_entrances', type_="check")
    op.drop_constraint('valid_destination_reviewed_fields', 'destinations', type_="check")
    op.drop_column("destination_entrances", 'coordinate_review_notes')
    op.drop_column("destination_entrances", 'coordinate_reviewed_by')
    op.drop_column("destination_entrances", 'coordinate_reviewed_at')
    op.drop_column("destination_entrances", 'coordinate_review_status')
    op.drop_column("destination_entrances", 'coordinate_source_url')
    op.drop_column("destination_entrances", 'point_kind')
    op.drop_column("destination_entrances", 'reviewed_fields')
    op.drop_column("destinations", "reviewed_fields")
