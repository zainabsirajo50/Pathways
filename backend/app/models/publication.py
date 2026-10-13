"""Immutable content review and publication evidence (not route approval)."""
import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ContentReview(Base):
    __tablename__ = 'destination_content_reviews'
    __table_args__ = (
        CheckConstraint("length(btrim(actor)) > 0 AND length(btrim(notes)) > 0", name='content_review_identity'),
        CheckConstraint("jsonb_typeof(snapshot) = 'object' AND jsonb_typeof(evidence) = 'object'", name='content_review_objects'),
        Index('content_reviews_destination_idx', 'destination_id', 'reviewed_at'),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('destinations.id', ondelete='RESTRICT'), nullable=False)
    actor: Mapped[str] = mapped_column(String(160), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False)

class PublicationAudit(Base):
    __tablename__ = 'destination_publication_audits'
    __table_args__ = (
        CheckConstraint("action IN ('approve','revoke','invalidate')", name='publication_audit_action'),
        CheckConstraint("previous_status IN ('draft','needs_review','verified') AND new_status IN ('draft','needs_review','verified')", name='publication_audit_status'),
        CheckConstraint("length(btrim(actor)) > 0 AND length(btrim(reason)) > 0", name='publication_audit_identity'),
        CheckConstraint("action != 'approve' OR (review_id IS NOT NULL AND new_status = 'verified')", name='publication_approval_review'),
        Index('publication_audits_destination_idx', 'destination_id', 'acted_at'),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('destinations.id', ondelete='RESTRICT'), nullable=False)
    review_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('destination_content_reviews.id', ondelete='RESTRICT'))
    actor: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    acted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
