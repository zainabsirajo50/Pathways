"""Create destination catalog with PostGIS geography points.

Revision ID: 0001_destination_catalog
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

revision = "0001_destination_catalog"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("region", sa.String(30), nullable=False),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(2), nullable=False, server_default="GA"),
        sa.Column("description", sa.Text()),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("official_website", sa.Text()),
        sa.Column("access_notes", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("category IN ('waterfall','lake','gorge','forest','river','coast','mountain','garden','park')", name="valid_category"),
        sa.CheckConstraint("region IN ('north','northeast','northwest','metro_atlanta','central','west','south','coastal')", name="valid_region"),
        sa.CheckConstraint("status IN ('draft','needs_review','verified')", name="valid_status"),
        sa.CheckConstraint("state = 'GA'", name="valid_state"),
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="valid_slug"),
        sa.CheckConstraint("length(btrim(name)) > 0", name="valid_name"),
    )
    op.create_index("destinations_category_idx", "destinations", ["category"])
    op.create_index("destinations_status_idx", "destinations", ["status"])
    op.execute("CREATE INDEX destinations_location_idx ON destinations USING GIST (location)")
    op.create_table(
        "destination_entrances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("routing_status", sa.String(20), nullable=False, server_default="untested"),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("routing_status IN ('untested','passed','failed','manual_review')", name="valid_routing_status"),
        sa.UniqueConstraint("destination_id", "name", name="uq_entrance_destination_name"),
    )
    op.create_index("one_primary_entrance", "destination_entrances", ["destination_id"], unique=True, postgresql_where=sa.text("is_primary = TRUE"))
    op.execute("CREATE INDEX entrances_location_idx ON destination_entrances USING GIST (location)")
    op.create_table(
        "destination_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(150)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("source_type IN ('georgia_dnr','nps','osm','other')", name="valid_source_type"),
        sa.UniqueConstraint("destination_id", "source_url", name="uq_source_destination_url"),
    )
    op.create_table(
        "destination_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("attribution", sa.Text()),
        sa.Column("license", sa.String(100)),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("destination_id", "image_url", name="uq_image_destination_url"),
    )
    op.create_index("one_cover_image", "destination_images", ["destination_id"], unique=True, postgresql_where=sa.text("is_cover = TRUE"))


def downgrade():
    op.drop_table("destination_images")
    op.drop_table("destination_sources")
    op.drop_table("destination_entrances")
    op.drop_table("destinations")
    # Extensions intentionally retained: other database objects may depend on them.
