"""Initial normalized asset management schema.

The metadata-based create_all is deliberately only a local startup convenience;
this revision is the authoritative migration path for a clean MySQL deployment.
"""
from alembic import op
from app.models import Base
revision='0001_initial'; down_revision=None; branch_labels=None; depends_on=None
def upgrade(): Base.metadata.create_all(op.get_bind())
def downgrade(): Base.metadata.drop_all(op.get_bind())
