"""Add updated_at to polls

Revision ID: c3a1f5b8d920
Revises: b82169a4e57a
Create Date: 2026-02-20 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3a1f5b8d920'
down_revision = 'b82169a4e57a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Backfill existing rows: set updated_at = created_at
    op.execute('UPDATE polls SET updated_at = created_at WHERE updated_at IS NULL')


def downgrade():
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
