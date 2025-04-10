"""Add conversations table and update messages table

Revision ID: 63081acc8aaa
Revises: 
Create Date: 2025-04-06 16:44:10.601921

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63081acc8aaa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('conversation_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_message_conversation', 'conversations', ['conversation_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_constraint('fk_message_conversation', type_='foreignkey')
        batch_op.drop_column('conversation_id')

    # ### end Alembic commands ###
