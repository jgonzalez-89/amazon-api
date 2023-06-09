"""empty message

Revision ID: a7c939161eb6
Revises: 
Create Date: 2023-04-22 00:09:21.085164

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c939161eb6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('productos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=True),
    sa.Column('imagen', sa.String(), nullable=True),
    sa.Column('nombre', sa.String(), nullable=True),
    sa.Column('distribuidor', sa.String(), nullable=True),
    sa.Column('ASIN', sa.String(), nullable=True),
    sa.Column('precio', sa.Float(), nullable=True),
    sa.Column('EAN', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('productos')
    # ### end Alembic commands ###
