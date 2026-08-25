"""Add contract renewal workflow and history."""

from alembic import op
import sqlalchemy as sa


revision = "0003_contract_renewal_workflow"
down_revision = "0002_asset_registration_details"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "contract_renewals" not in inspector.get_table_names():
        op.create_table(
            "contract_renewals",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column(
                "contract_id",
                sa.BigInteger(),
                sa.ForeignKey("service_contracts.id"),
                nullable=False,
            ),
            sa.Column(
                "approval_id",
                sa.BigInteger(),
                sa.ForeignKey("approval_requests.id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("old_start_date", sa.Date(), nullable=True),
            sa.Column("old_end_date", sa.Date(), nullable=True),
            sa.Column("new_start_date", sa.Date(), nullable=True),
            sa.Column("new_end_date", sa.Date(), nullable=True),
            sa.Column("old_value", sa.Numeric(14, 2), nullable=True),
            sa.Column("new_value", sa.Numeric(14, 2), nullable=True),
            sa.Column("reference_number", sa.String(length=100), nullable=True),
            sa.Column("document_path", sa.String(length=500), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("renewed_by", sa.String(length=80), nullable=True),
            sa.Column("renewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_contract_renewals_contract_id",
            "contract_renewals",
            ["contract_id"],
        )
        op.create_index(
            "ix_contract_renewals_approval_id",
            "contract_renewals",
            ["approval_id"],
            unique=True,
        )


def downgrade():
    op.drop_index("ix_contract_renewals_approval_id", table_name="contract_renewals")
    op.drop_index("ix_contract_renewals_contract_id", table_name="contract_renewals")
    op.drop_table("contract_renewals")
