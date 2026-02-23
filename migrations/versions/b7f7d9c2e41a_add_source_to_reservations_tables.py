"""add source to reservations tables

Revision ID: b7f7d9c2e41a
Revises: 872a0eaffe0e
Create Date: 2026-02-17 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f7d9c2e41a'
down_revision = '872a0eaffe0e'
branch_labels = None
depends_on = None


def _get_columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


def upgrade():
    pre_columns = _get_columns('pre_reservations')
    if 'source' not in pre_columns:
        op.add_column('pre_reservations', sa.Column('source', sa.String(length=20), nullable=True, server_default='web'))
        op.execute(sa.text("UPDATE pre_reservations SET source = 'web' WHERE source IS NULL OR source = ''"))
        with op.batch_alter_table('pre_reservations', schema=None) as batch_op:
            batch_op.alter_column('source', existing_type=sa.String(length=20), nullable=False, server_default='web')
            batch_op.create_index(batch_op.f('ix_pre_reservations_source'), ['source'], unique=False)

    res_columns = _get_columns('reservations')
    if 'source' not in res_columns:
        op.add_column('reservations', sa.Column('source', sa.String(length=20), nullable=True, server_default='web'))
        op.execute(sa.text("UPDATE reservations SET source = 'web' WHERE source IS NULL OR source = ''"))
        with op.batch_alter_table('reservations', schema=None) as batch_op:
            batch_op.alter_column('source', existing_type=sa.String(length=20), nullable=False, server_default='web')
            batch_op.create_index(batch_op.f('ix_reservations_source'), ['source'], unique=False)


def downgrade():
    pre_columns = _get_columns('pre_reservations')
    if 'source' in pre_columns:
        with op.batch_alter_table('pre_reservations', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_pre_reservations_source'))
            batch_op.drop_column('source')

    res_columns = _get_columns('reservations')
    if 'source' in res_columns:
        with op.batch_alter_table('reservations', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_reservations_source'))
            batch_op.drop_column('source')
