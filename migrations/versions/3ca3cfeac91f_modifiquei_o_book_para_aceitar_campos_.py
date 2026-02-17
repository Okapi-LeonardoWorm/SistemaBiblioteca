"""Modifiquei o book para aceitar campos nulos

Revision ID: 3ca3cfeac91f
Revises: 
Create Date: 2024-09-03 21:07:03.714624

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '3ca3cfeac91f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
       bind = op.get_bind()

       from app.models import (
              User,
              Book,
              KeyWord,
              Loan,
              KeyWordBook,
              Permission,
              Role,
              RolePermission,
       )

       for model in (User, Book, KeyWord, Loan, KeyWordBook, Permission, Role, RolePermission):
              model.__table__.create(bind=bind, checkfirst=True)


def downgrade():
       pass
