from datetime import date

from sqlalchemy import func

from app import db
from app.models import Loan, StatusLoan


def available_copies_for_range(book, start_date, end_date):
    if not book:
        return 0

    query = db.session.query(func.coalesce(func.sum(Loan.amount), 0)).filter(
        Loan.bookId == book.bookId,
        Loan.status == StatusLoan.ACTIVE,
    )

    if start_date and end_date:
        query = query.filter(Loan.loanDate <= end_date, Loan.returnDate >= start_date)
    else:
        today = date.today()
        query = query.filter(Loan.loanDate <= today, Loan.returnDate >= today)

    used = query.scalar() or 0
    available = book.amount - used
    return max(available, 0)
