"""Content review evidence and append-only publication audit.
Revision ID: 0003_content_publication
Revises: 0002_verification_infrastructure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
revision = '0003_content_publication'
down_revision = '0002_verification_infrastructure'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('destination_content_reviews',
        sa.Column('id',pg.UUID(as_uuid=True),primary_key=True),
        sa.Column('destination_id',pg.UUID(as_uuid=True),sa.ForeignKey('destinations.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('actor',sa.String(160),nullable=False),
        sa.Column('reviewed_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column('notes',sa.Text(),nullable=False),
        sa.Column('snapshot',pg.JSONB(),nullable=False),
        sa.Column('evidence',pg.JSONB(),nullable=False),
        sa.CheckConstraint('length(btrim(actor)) > 0 AND length(btrim(notes)) > 0',name='content_review_identity'),
        sa.CheckConstraint("jsonb_typeof(snapshot) = 'object' AND jsonb_typeof(evidence) = 'object'",name='content_review_objects'))
    op.create_index('content_reviews_destination_idx','destination_content_reviews',['destination_id','reviewed_at'])
    op.create_table('destination_publication_audits',
        sa.Column('id',pg.UUID(as_uuid=True),primary_key=True),
        sa.Column('destination_id',pg.UUID(as_uuid=True),sa.ForeignKey('destinations.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('review_id',pg.UUID(as_uuid=True),sa.ForeignKey('destination_content_reviews.id',ondelete='RESTRICT')),
        sa.Column('actor',sa.String(160),nullable=False),
        sa.Column('action',sa.String(20),nullable=False),
        sa.Column('previous_status',sa.String(20),nullable=False),
        sa.Column('new_status',sa.String(20),nullable=False),
        sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('acted_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column('snapshot',pg.JSONB(),nullable=False),
        sa.CheckConstraint("action IN ('approve','revoke','invalidate')",name='publication_audit_action'),
        sa.CheckConstraint("previous_status IN ('draft','needs_review','verified') AND new_status IN ('draft','needs_review','verified')",name='publication_audit_status'),
        sa.CheckConstraint('length(btrim(actor)) > 0 AND length(btrim(reason)) > 0',name='publication_audit_identity'),
        sa.CheckConstraint("action != 'approve' OR (review_id IS NOT NULL AND new_status = 'verified')",name='publication_approval_review'))
    op.create_index('publication_audits_destination_idx','destination_publication_audits',['destination_id','acted_at'])
    op.execute("""
        CREATE FUNCTION pathways_immutable_review_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Content review and publication history is append-only'; END;
        $$
    """)
    for table in ('destination_content_reviews','destination_publication_audits'):
        op.execute(f'CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION pathways_immutable_review_history()')
    op.execute("""
        CREATE FUNCTION pathways_invalidate_publication() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.status = 'verified' AND
              (to_jsonb(NEW) - ARRAY['status','updated_at']) IS DISTINCT FROM
              (to_jsonb(OLD) - ARRAY['status','updated_at']) THEN
                NEW.status := 'needs_review';
                INSERT INTO destination_publication_audits
                  (id,destination_id,actor,action,previous_status,new_status,reason,snapshot)
                  VALUES (gen_random_uuid(),OLD.id,session_user,'invalidate','verified','needs_review',
                    'Published content changed; a new content review is required',to_jsonb(OLD));
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute('CREATE TRIGGER invalidate_content_publication BEFORE UPDATE ON destinations FOR EACH ROW EXECUTE FUNCTION pathways_invalidate_publication()')
    op.execute("""
        CREATE FUNCTION pathways_invalidate_source_publication() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid; old_data jsonb;
        BEGIN
            IF TG_OP = 'UPDATE' AND NEW IS NOT DISTINCT FROM OLD THEN RETURN NEW; END IF;
            FOR target IN SELECT DISTINCT x FROM unnest(CASE WHEN TG_OP = 'INSERT' THEN ARRAY[NEW.destination_id]
                 WHEN TG_OP = 'DELETE' THEN ARRAY[OLD.destination_id] ELSE ARRAY[OLD.destination_id,NEW.destination_id] END) x LOOP
                SELECT to_jsonb(d) INTO old_data FROM destinations d WHERE id=target AND status='verified' FOR UPDATE;
                IF old_data IS NOT NULL THEN
                    UPDATE destinations SET status='needs_review' WHERE id=target;
                    INSERT INTO destination_publication_audits
                       (id,destination_id,actor,action,previous_status,new_status,reason,snapshot)
                       VALUES (gen_random_uuid(),target,session_user,'invalidate','verified','needs_review',
                         'Source provenance changed; a new content review is required',old_data);
                END IF;
            END LOOP;
            RETURN NULL;
        END; $$
    """)
    op.execute('CREATE TRIGGER invalidate_source_publication AFTER INSERT OR UPDATE OR DELETE ON destination_sources FOR EACH ROW EXECUTE FUNCTION pathways_invalidate_source_publication()')

def downgrade():
    # Explicit downgrade discards new content evidence; never run on development.
    op.execute('DROP TRIGGER invalidate_source_publication ON destination_sources')
    op.execute('DROP FUNCTION pathways_invalidate_source_publication()')
    op.execute('DROP TRIGGER invalidate_content_publication ON destinations')
    op.execute('DROP FUNCTION pathways_invalidate_publication()')
    for table in ('destination_publication_audits','destination_content_reviews'):
        op.execute(f'DROP TRIGGER immutable_history ON {table}')
        op.drop_table(table)
    op.execute('DROP FUNCTION pathways_immutable_review_history()')

