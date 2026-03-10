"""add_book_year_fields

Revision ID: e4f9c2ab17de
Revises: d82c0569e058
Create Date: 2026-03-10 00:00:00.000000

"""
from datetime import date, datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4f9c2ab17de'
down_revision = 'd82c0569e058'
branch_labels = None
depends_on = None


def _extract_year(value):
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.year
    if isinstance(value, str):
        try:
            return int(value[:4])
        except (TypeError, ValueError):
            return None
    return None


def upgrade():
    op.add_column('books', sa.Column('publicationYear', sa.Integer(), nullable=True))
    op.add_column('books', sa.Column('acquisitionYear', sa.Integer(), nullable=True))

    connection = op.get_bind()
    books = sa.table(
        'books',
        sa.column('bookId', sa.Integer()),
        sa.column('publishedDate', sa.Date()),
        sa.column('acquisitionDate', sa.DateTime()),
        sa.column('publicationYear', sa.Integer()),
        sa.column('acquisitionYear', sa.Integer()),
    )

    rows = connection.execute(
        sa.select(books.c.bookId, books.c.publishedDate, books.c.acquisitionDate)
    ).fetchall()

    for row in rows:
        publication_year = _extract_year(row.publishedDate)
        acquisition_year = _extract_year(row.acquisitionDate)
        if publication_year is None and acquisition_year is None:
            continue
        connection.execute(
            sa.update(books)
            .where(books.c.bookId == row.bookId)
            .values(
                publicationYear=publication_year,
                acquisitionYear=acquisition_year,
            )
        )


def downgrade():
    op.drop_column('books', 'acquisitionYear')
    op.drop_column('books', 'publicationYear')
