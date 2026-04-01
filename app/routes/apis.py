from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import Book, Loan, StatusLoan, User
from app.utils import available_copies_for_range, calc_age, parse_date

bp = Blueprint('apis', __name__)

@bp.route('/api/users/search')
@login_required
def api_search_users():
    q = (request.args.get('q') or '').strip()
    try:
        limit = int(request.args.get('limit', 10))
    except Exception:
        limit = 10
    if not q:
        return jsonify({'results': []})
    users = (User.query
             .filter(User.deleted.is_(False))
             .filter(or_(
                 User.identificationCode.ilike(f"%{q}%"),
                 User.userCompleteName.ilike(f"%{q}%")
             ))
             .order_by(User.userCompleteName.asc())
             .limit(limit).all())
    results = []
    for u in users:
        results.append({
            'userId': u.userId,
            'identificationCode': u.identificationCode,
            'name': u.userCompleteName,
            'pcd': bool(u.pcd),
            'userType': u.userType,
            'age': calc_age(u.birthDate),
            'birthDate': u.birthDate.isoformat() if u.birthDate else None,
            'gradeNumber': u.gradeNumber,
            'className': u.className,
            'cpf': u.cpf,
            'rg': u.rg,
        })
    return jsonify({'results': results})


@bp.route('/api/books/search')
@login_required
def api_search_books():
    q = (request.args.get('q') or '').strip()
    try:
        limit = int(request.args.get('limit', 10))
    except Exception:
        limit = 10
    loan_date = parse_date(request.args.get('loanDate'))
    return_date = parse_date(request.args.get('returnDate'))
    if not q:
        return jsonify({'results': []})
    books = (Book.query
             .filter(Book.deleted.is_(False))
             .filter(or_(
                 Book.bookName.ilike(f"%{q}%"),
                 Book.authorName.ilike(f"%{q}%"),
                 Book.publisherName.ilike(f"%{q}%")
             ))
             .order_by(Book.bookName.asc())
             .limit(limit).all())
    results = []
    for b in books:
        available = available_copies_for_range(b, loan_date, return_date)
        results.append({
            'bookId': b.bookId,
            'bookName': b.bookName,
            'authorName': b.authorName,
            'publisherName': b.publisherName,
            'publishedDate': b.publishedDate.isoformat() if b.publishedDate else None,
            'publicationYear': b.publicationYear,
            'acquisitionDate': b.acquisitionDate.isoformat() if b.acquisitionDate else None,
            'acquisitionYear': b.acquisitionYear,
            'amount': b.amount,
            'available': available,
            'keywords': [kw.word for kw in getattr(b, 'keywords', [])]
        })
    return jsonify({'results': results})


@bp.route('/api/users/<int:user_id>/loan-history')
@login_required
def api_user_loan_history(user_id):
    user = User.query.filter_by(userId=user_id).first()
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404

    query = Loan.query.join(Loan.book).filter(Loan.userId == user_id)

    search_term = (request.args.get('q') or '').strip()
    if search_term:
        query = query.filter(Book.bookName.ilike(f"%{search_term}%"))

    raw_statuses = request.args.getlist('statuses')
    requested_statuses = []
    for status_name in raw_statuses:
        name = (status_name or '').strip().upper()
        if name in StatusLoan.__members__:
            requested_statuses.append(StatusLoan[name])

    if requested_statuses:
        query = query.filter(Loan.status.in_(requested_statuses))

    loans = query.order_by(Loan.loanDate.desc()).all()

    total_borrowed = Loan.query.filter(
        Loan.userId == user_id,
        Loan.status != StatusLoan.CANCELLED,
    ).count()
    total_returned = Loan.query.filter(
        Loan.userId == user_id,
        Loan.status == StatusLoan.COMPLETED,
    ).count()

    return jsonify({
        'success': True,
        'summary': {
            'total_borrowed': total_borrowed,
            'total_returned': total_returned,
        },
        'status_options': [
            {'name': status.name, 'label': status.value}
            for status in StatusLoan
        ],
        'items': [
            {
                'loanId': loan.loanId,
                'bookName': loan.book.bookName if loan.book else None,
                'loanDate': loan.loanDate.isoformat() if loan.loanDate else None,
                'returnDate': loan.returnDate.isoformat() if loan.returnDate else None,
                'statusName': loan.status.name if loan.status else None,
                'statusLabel': loan.status.value if loan.status else None,
            }
            for loan in loans
        ],
    })


@bp.route('/api/books/<int:book_id>/loan-history')
@login_required
def api_book_loan_history(book_id):
    book = Book.query.filter_by(bookId=book_id).first()
    if not book:
        return jsonify({'success': False, 'message': 'Livro não encontrado.'}), 404

    query = Loan.query.join(Loan.user).filter(Loan.bookId == book_id)

    search_term = (request.args.get('q') or '').strip()
    if search_term:
        query = query.filter(
            or_(
                User.identificationCode.ilike(f"%{search_term}%"),
                User.userCompleteName.ilike(f"%{search_term}%"),
            )
        )

    raw_statuses = request.args.getlist('statuses')
    requested_statuses = []
    for status_name in raw_statuses:
        name = (status_name or '').strip().upper()
        if name in StatusLoan.__members__:
            requested_statuses.append(StatusLoan[name])

    if requested_statuses:
        query = query.filter(Loan.status.in_(requested_statuses))

    loans = query.order_by(Loan.loanDate.desc()).all()

    total_borrowed = Loan.query.filter(
        Loan.bookId == book_id,
        Loan.status != StatusLoan.CANCELLED,
    ).count()
    total_returned = Loan.query.filter(
        Loan.bookId == book_id,
        Loan.status == StatusLoan.COMPLETED,
    ).count()

    return jsonify({
        'success': True,
        'summary': {
            'total_borrowed': total_borrowed,
            'total_returned': total_returned,
        },
        'status_options': [
            {'name': status.name, 'label': status.value}
            for status in StatusLoan
        ],
        'items': [
            {
                'loanId': loan.loanId,
                'userCode': loan.user.identificationCode if loan.user else None,
                'userName': loan.user.userCompleteName if loan.user else None,
                'loanDate': loan.loanDate.isoformat() if loan.loanDate else None,
                'returnDate': loan.returnDate.isoformat() if loan.returnDate else None,
                'statusName': loan.status.name if loan.status else None,
                'statusLabel': loan.status.value if loan.status else None,
            }
            for loan in loans
        ],
    })

