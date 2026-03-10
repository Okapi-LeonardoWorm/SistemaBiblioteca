from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import Book, User
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

