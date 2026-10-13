"""Destination catalog models; GeoAlchemy uses WGS84 geography coordinates."""
import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = (
        CheckConstraint("category IN ('waterfall','lake','gorge','forest','river','coast','mountain','garden','park')", name="valid_category"),
        CheckConstraint("region IN ('north','northeast','northwest','metro_atlanta','central','west','south','coastal')", name="valid_region"),
        CheckConstraint("status IN ('draft','needs_review','verified')", name="valid_status"),
        CheckConstraint("state = 'GA'", name="valid_state"),
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="valid_slug"),
        CheckConstraint("length(btrim(name)) > 0", name="valid_name"),
        Index("destinations_category_idx", "category"),
        Index("destinations_status_idx", "status"),
        CheckConstraint("jsonb_typeof(reviewed_fields) = 'array' AND reviewed_fields <@ '[\"name\",\"category\",\"region\",\"city\",\"state\",\"description\",\"location\",\"official_website\",\"access_notes\",\"status\"]'::jsonb", name="valid_destination_reviewed_fields"),
        Index("destinations_location_idx", "location", postgresql_using="gist"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    region: Mapped[str] = mapped_column(String(30), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2), nullable=False, server_default=text("'GA'"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True)
    official_website: Mapped[Optional[str]] = mapped_column(Text)
    access_notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'draft'"))
    reviewed_fields: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSONB), nullable=False, default=list, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    entrances: Mapped[list["DestinationEntrance"]] = relationship(back_populates="destination", cascade="all, delete-orphan")
    sources: Mapped[list["DestinationSource"]] = relationship(back_populates="destination", cascade="all, delete-orphan")
    images: Mapped[list["DestinationImage"]] = relationship(back_populates="destination", cascade="all, delete-orphan")


class DestinationEntrance(Base):
    __tablename__ = "destination_entrances"
    __table_args__ = (
        CheckConstraint("routing_status IN ('untested','passed','failed','manual_review')", name="valid_routing_status"),
        Index("one_primary_entrance", "destination_id", unique=True, postgresql_where=text("is_primary = TRUE")),
        UniqueConstraint("destination_id", "name", name="uq_entrance_destination_name"),
        CheckConstraint("point_kind IN ('unknown','gate','parking','visitor_center','trailhead')", name="valid_point_kind"),
        CheckConstraint("coordinate_review_status IN ('pending','reviewed','rejected')", name="valid_coordinate_review_status"),
        CheckConstraint("coordinate_source_url IS NULL OR coordinate_source_url ~ '^https?://[^/[:space:]]+'", name="valid_coordinate_source_url"),
        CheckConstraint("coordinate_review_status != 'reviewed' OR (location IS NOT NULL AND coordinate_source_url IS NOT NULL AND coordinate_reviewed_at IS NOT NULL AND length(btrim(coordinate_reviewed_by)) > 0 AND coordinate_reviewed_by IS NOT NULL AND point_kind != 'unknown')", name="reviewed_coordinate_evidence"),
        CheckConstraint("jsonb_typeof(reviewed_fields) = 'array' AND reviewed_fields <@ '[\"name\",\"address\",\"location\",\"is_primary\",\"point_kind\",\"coordinate_source_url\"]'::jsonb", name="valid_entrance_reviewed_fields"),
        Index("entrances_location_idx", "location", postgresql_using="gist"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    routing_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'untested'"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    point_kind: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'unknown'"))
    coordinate_source_url: Mapped[Optional[str]] = mapped_column(Text)
    coordinate_review_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    coordinate_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    coordinate_reviewed_by: Mapped[Optional[str]] = mapped_column(String(160))
    coordinate_review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_fields: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSONB), nullable=False, default=list, server_default=text("'[]'::jsonb"))
    destination: Mapped[Destination] = relationship(back_populates="entrances")


class RouteVerification(Base):
    """Historical test evidence; inserting a result never approves a destination."""
    __tablename__ = "route_verifications"
    __table_args__ = (
        CheckConstraint("length(btrim(provider)) > 0", name="valid_route_provider"),
        CheckConstraint("travel_mode IN ('driving','walking')", name="valid_route_travel_mode"),
        CheckConstraint("result IN ('passed','failed','error','manual_review')", name="valid_route_result"),
        CheckConstraint("origin_latitude BETWEEN -90 AND 90 AND destination_latitude BETWEEN -90 AND 90 AND origin_longitude BETWEEN -180 AND 180 AND destination_longitude BETWEEN -180 AND 180", name="valid_route_coordinates"),
        CheckConstraint("result != 'error' OR (error_details IS NOT NULL AND length(btrim(error_details)) > 0)", name="route_error_details_required"),
        Index("route_verifications_entrance_tested_idx", "entrance_id", "tested_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("destination_entrances.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    travel_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    error_details: Mapped[Optional[str]] = mapped_column(Text)


class DestinationSource(Base):
    __tablename__ = "destination_sources"
    __table_args__ = (
        CheckConstraint("source_type IN ('georgia_dnr','nps','osm','other')", name="valid_source_type"),
        UniqueConstraint("destination_id", "source_url", name="uq_source_destination_url"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(150))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    destination: Mapped[Destination] = relationship(back_populates="sources")


class DestinationImage(Base):
    __tablename__ = "destination_images"
    __table_args__ = (
        Index("one_cover_image", "destination_id", unique=True, postgresql_where=text("is_cover = TRUE")),
        UniqueConstraint("destination_id", "image_url", name="uq_image_destination_url"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    attribution: Mapped[Optional[str]] = mapped_column(Text)
    license: Mapped[Optional[str]] = mapped_column(String(100))
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    destination: Mapped[Destination] = relationship(back_populates="images")
