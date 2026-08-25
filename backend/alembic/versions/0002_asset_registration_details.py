"""Complete asset registration fields and documents."""
from alembic import op
import sqlalchemy as sa

revision = '0002_asset_registration_details'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    bind=op.get_bind(); inspector=sa.inspect(bind); columns={c['name'] for c in inspector.get_columns('assets')}
    for name, column in [('invoice_reference',sa.String(length=150)),('warranty_start_date',sa.Date()),('warranty_document_path',sa.String(length=500)),('useful_life_months',sa.Integer())]:
        if name not in columns: op.add_column('assets',sa.Column(name,column,nullable=True))
    if 'asset_documents' not in inspector.get_table_names():
        op.create_table('asset_documents',sa.Column('id',sa.BigInteger(),primary_key=True),sa.Column('asset_id',sa.BigInteger(),sa.ForeignKey('assets.id'),nullable=False),sa.Column('document_type',sa.String(length=50),nullable=False),sa.Column('file_path',sa.String(length=500),nullable=False),sa.Column('title',sa.String(length=200),nullable=True),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False))
        op.create_index('ix_asset_documents_asset_id','asset_documents',['asset_id'])

def downgrade():
    op.drop_index('ix_asset_documents_asset_id', table_name='asset_documents')
    op.drop_table('asset_documents')
    op.drop_column('assets', 'useful_life_months')
    op.drop_column('assets', 'warranty_document_path')
    op.drop_column('assets', 'warranty_start_date')
    op.drop_column('assets', 'invoice_reference')
