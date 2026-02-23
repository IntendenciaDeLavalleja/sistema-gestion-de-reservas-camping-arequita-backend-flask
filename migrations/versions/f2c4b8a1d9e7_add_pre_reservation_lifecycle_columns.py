"""Add pre_reservations lifecycle columns

Revision ID: f2c4b8a1d9e7
Revises: 90b0dee3a10f
Create Date: 2026-02-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2c4b8a1d9e7'
down_revision = '90b0dee3a10f'
branch_labels = None
depends_on = None


def _get_columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


def upgrade():
    columns = _get_columns('pre_reservations')

    if 'archive_reason' not in columns:
        op.add_column('pre_reservations', sa.Column('archive_reason', sa.Text(), nullable=True))

    if 'checked_in_at' not in columns:
        op.add_column('pre_reservations', sa.Column('checked_in_at', sa.DateTime(), nullable=True))

    if 'completed_at' not in columns:
        op.add_column('pre_reservations', sa.Column('completed_at', sa.DateTime(), nullable=True))

    # Normalize legacy status value if it still exists
    op.execute(
        sa.text(
            "UPDATE pre_reservations "
            "SET status = 'expired' "
            "WHERE status = 'archived_unconfirmed'"
        )
    )


def downgrade():
    columns = _get_columns('pre_reservations')

    if 'completed_at' in columns:
        op.drop_column('pre_reservations', 'completed_at')

    if 'checked_in_at' in columns:
        op.drop_column('pre_reservations', 'checked_in_at')

    if 'archive_reason' in columns:
        op.drop_column('pre_reservations', 'archive_reason')

    op.execute(
        sa.text(
            "UPDATE pre_reservations "
            "SET status = 'archived_unconfirmed' "
            "WHERE status = 'expired'"
        )
    )
