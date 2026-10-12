"""Destination catalog models; GeoAlchemy uses WGS84 geography coordinates."""
import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import UUID
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
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    routing_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'untested'"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    destination: Mapped[Destination] = relationship(back_populates="entrances")


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
