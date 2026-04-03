from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import Book, KeyWord, Loan, StatusLoan, User
from app.services.dashboard_service import (
    get_drilldown_details,
    get_acervo_data,
    get_dashboard_kpis,
    get_devolucoes_data,
    get_devolucoes_filter_options,
    get_engajamento,
    get_popularidade,
    get_top_tags,
    get_ultimos_emprestimos,
)
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


@bp.route('/api/keywords/<int:keyword_id>/book-history')
@login_required
def api_keyword_book_history(keyword_id):
    keyword = KeyWord.query.filter_by(wordId=keyword_id, deleted=False).first()
    if not keyword:
        return jsonify({'success': False, 'message': 'Tag não encontrada.'}), 404

    base_query = Book.query.join(Book.keywords).filter(
        KeyWord.wordId == keyword_id,
        Book.deleted.is_(False),
    )

    search_term = (request.args.get('q') or '').strip()
    filtered_query = base_query
    if search_term:
        filtered_query = filtered_query.filter(
            or_(
                Book.bookName.ilike(f"%{search_term}%"),
                Book.authorName.ilike(f"%{search_term}%"),
            )
        )

    books = filtered_query.order_by(Book.bookName.asc()).all()
    total_books = base_query.count()

    return jsonify({
        'success': True,
        'summary': {
            'total_books': total_books,
        },
        'items': [
            {
                'bookId': book.bookId,
                'bookName': book.bookName,
                'authorName': book.authorName,
            }
            for book in books
        ],
    })


@bp.route('/api/dashboard/kpis')
@login_required
def api_dashboard_kpis():
    data = get_dashboard_kpis()
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/devolucoes')
@login_required
def api_dashboard_devolucoes():
    quick_filter = (request.args.get('quick_filter') or 'today').strip().lower()
    student_query = (request.args.get('student') or '').strip()
    series = request.args.getlist('serie')
    turmas = request.args.getlist('turma')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        per_page = 10

    data = get_devolucoes_data(
        quick_filter=quick_filter,
        student_query=student_query,
        series=series,
        turmas=turmas,
        page=page,
        per_page=per_page,
    )
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/devolucoes/filter-options')
@login_required
def api_dashboard_devolucoes_filter_options():
    data = get_devolucoes_filter_options()
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/tags-top')
@login_required
def api_dashboard_tags_top():
    try:
        limit = int(request.args.get('limit', 10))
    except ValueError:
        limit = 10
    data = get_top_tags(limit=limit)
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/ultimos-emprestimos')
@login_required
def api_dashboard_ultimos_emprestimos():
    try:
        limit = int(request.args.get('limit', 10))
    except ValueError:
        limit = 10
    data = get_ultimos_emprestimos(limit=limit)
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/engajamento')
@login_required
def api_dashboard_engajamento():
    period = (request.args.get('period') or '').strip().lower()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()
    series = request.args.getlist('serie')
    turmas = request.args.getlist('turma')
    user_types = [item.strip() for item in request.args.getlist('user_type') if (item or '').strip()]
    user_type = (request.args.get('user_type') or '').strip()
    if not user_types and user_type:
        user_types = [user_type]
    serie = (request.args.get('serie') or '').strip()
    turma = (request.args.get('turma') or '').strip()
    periodo_escolar = (request.args.get('periodo') or '').strip().lower()
    try:
        top_limit = int(request.args.get('top_limit', 10))
    except ValueError:
        top_limit = 10

    data = get_engajamento(
        period=period or None,
        start_date=start_date or None,
        end_date=end_date or None,
        series=series or None,
        turmas=turmas or None,
        user_types=user_types or None,
        user_type=user_type or None,
        serie=serie or None,
        turma=turma or None,
        periodo_escolar=periodo_escolar or None,
        top_limit=top_limit,
    )
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/popularidade')
@login_required
def api_dashboard_popularidade():
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()
    range_name = (request.args.get('range') or 'anual').strip().lower()
    series = request.args.getlist('serie')
    turmas = request.args.getlist('turma')
    user_types = [item.strip() for item in request.args.getlist('user_type') if (item or '').strip()]
    user_type = (request.args.get('user_type') or '').strip()
    if not user_types and user_type:
        user_types = [user_type]
    serie = (request.args.get('serie') or '').strip()
    turma = (request.args.get('turma') or '').strip()
    periodo_escolar = (request.args.get('periodo') or '').strip().lower()
    try:
        limit = int(request.args.get('limit', 10))
    except ValueError:
        limit = 10

    data = get_popularidade(
        start_date=start_date or None,
        end_date=end_date or None,
        range_name=range_name,
        series=series or None,
        turmas=turmas or None,
        user_types=user_types or None,
        user_type=user_type or None,
        serie=serie or None,
        turma=turma or None,
        periodo_escolar=periodo_escolar or None,
        limit=limit,
    )
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/acervo')
@login_required
def api_dashboard_acervo():
    try:
        days_lost = int(request.args.get('days_lost', 30))
    except ValueError:
        days_lost = 30
    try:
        limit = int(request.args.get('limit', 20))
    except ValueError:
        limit = 20

    data = get_acervo_data(days_lost=days_lost, limit=limit)
    return jsonify({'success': True, 'data': data})


@bp.route('/api/dashboard/drilldown')
@login_required
def api_dashboard_drilldown():
    source = (request.args.get('source') or '').strip().lower()
    label = (request.args.get('label') or '').strip()
    key = request.args.get('key')
    period = (request.args.get('period') or 'all').strip().lower()
    range_name = (request.args.get('range') or 'anual').strip().lower()
    serie = (request.args.get('serie') or '').strip()
    turma = (request.args.get('turma') or '').strip()
    periodo_escolar = (request.args.get('periodo') or '').strip().lower()
    try:
        limit = int(request.args.get('limit', 50))
    except ValueError:
        limit = 50

    data = get_drilldown_details(
        source,
        label=label or None,
        key=key,
        period=period,
        range_name=range_name,
        serie=serie or None,
        turma=turma or None,
        periodo_escolar=periodo_escolar or None,
        limit=limit,
    )
    return jsonify({'success': True, 'data': data})

