"""init

Revision ID: ce9de746e741
Revises: 
Create Date: 2022-05-31 21:32:24.143458

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce9de746e741'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('character',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('marvel_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('modified', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_character_id'), 'character', ['id'], unique=False)
    op.create_index(op.f('ix_character_marvel_id'), 'character', ['marvel_id'], unique=False)
    op.create_table('thumbnail',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('extension', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['character.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_thumbnail_id'), 'thumbnail', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_thumbnail_id'), table_name='thumbnail')
    op.drop_table('thumbnail')
    op.drop_index(op.f('ix_character_marvel_id'), table_name='character')
    op.drop_index(op.f('ix_character_id'), table_name='character')
    op.drop_table('character')
    # ### end Alembic commands ###