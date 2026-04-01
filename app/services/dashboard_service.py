from __future__ import annotations

from datetime import date, datetime, timedelta
from time import time

from sqlalchemy import and_, case, desc, func, literal, or_

from app import db
from app.models import Book, Configuration, KeyWord, KeyWordBook, Loan, StatusLoan, User

_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL_SHORT = 60
_CACHE_TTL_MEDIUM = 120


def _cache_get(cache_key: str):
    cached = _CACHE.get(cache_key)
    if not cached:
        return None
    expires_at, payload = cached
    if expires_at < time():
        _CACHE.pop(cache_key, None)
        return None
    return payload


def _cache_set(cache_key: str, payload, ttl: int):
    _CACHE[cache_key] = (time() + ttl, payload)


def _period_bounds(period: str):
    today = date.today()
    normalized = (period or 'all').strip().lower()

    if normalized == 'today':
        return today, today
    if normalized == 'week':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    if normalized == 'month':
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
        return start, end
    return None, None


def _popularidade_bounds(range_name: str):
    today = date.today()
    normalized = (range_name or 'anual').strip().lower()
    if normalized == 'mensal':
        return today - timedelta(days=30), today
    if normalized == 'semestral':
        return today - timedelta(days=182), today
    if normalized == 'anual':
        return today - timedelta(days=365), today
    return None, None


def _extract_period_expr():
    class_text = func.lower(func.coalesce(User.className, ''))
    return case(
        (class_text.like('%manh%'), literal('manha')),
        (class_text.like('%matut%'), literal('manha')),
        (class_text.like('%tard%'), literal('tarde')),
        (class_text.like('%vespert%'), literal('tarde')),
        else_=literal('nao_informado'),
    )


def _apply_engajamento_filters(query, serie=None, turma=None, periodo_escolar=None):
    if serie:
        try:
            query = query.filter(User.gradeNumber == int(serie))
        except ValueError:
            pass
    if turma:
        query = query.filter(func.lower(func.coalesce(User.className, '')).like(f"%{turma.lower()}%"))
    if periodo_escolar:
        query = query.filter(_extract_period_expr() == periodo_escolar)
    return query


def _lost_threshold_days():
    keys = ['DASHBOARD_LOST_THRESHOLD_DAYS', 'dashboard_lost_days', 'loan_lost_days', 'dias_extravio']
    config = Configuration.query.filter(Configuration.key.in_(keys)).order_by(Configuration.lastUpdate.desc()).first()
    if not config or not config.value:
        return 30
    try:
        val = int(str(config.value).strip())
        return val if val > 0 else 30
    except ValueError:
        return 30


def get_dashboard_kpis():
    active_statuses = [StatusLoan.ACTIVE, StatusLoan.OVERDUE, StatusLoan.LOST]

    total_books = db.session.query(func.coalesce(func.sum(Book.amount), 0)).filter(Book.deleted.is_(False)).scalar() or 0
    total_active_loans = Loan.query.filter(Loan.status.in_(active_statuses)).count()

    total_students = User.query.filter(
        User.deleted.is_(False),
        func.lower(User.userType).in_(['aluno', 'student'])
    ).count()
    total_collaborators = User.query.filter(
        User.deleted.is_(False),
        ~func.lower(User.userType).in_(['aluno', 'student'])
    ).count()

    overdue_count = Loan.query.filter(
        Loan.status.in_([StatusLoan.ACTIVE, StatusLoan.OVERDUE]),
        func.date(Loan.returnDate) < date.today(),
    ).count()

    return {
        'total_books': int(total_books),
        'total_active_loans': int(total_active_loans),
        'total_students': int(total_students),
        'total_collaborators': int(total_collaborators),
        'overdue_count': int(overdue_count),
    }


def get_devolucoes_data(quick_filter='today', student_query='', page=1, per_page=10):
    today = date.today()
    query = (
        db.session.query(
            Loan.loanId,
            Loan.loanDate,
            Loan.returnDate,
            Loan.status,
            Loan.amount,
            Book.bookName,
            User.userCompleteName,
            User.identificationCode,
            User.pcd,
        )
        .join(Book, Book.bookId == Loan.bookId)
        .join(User, User.userId == Loan.userId)
        .filter(Loan.status.in_([StatusLoan.ACTIVE, StatusLoan.OVERDUE]))
        .filter(Book.deleted.is_(False), User.deleted.is_(False))
    )

    normalized = (quick_filter or 'today').strip().lower()
    if normalized == 'today':
        query = query.filter(func.date(Loan.returnDate) == today)
    elif normalized == 'week':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        query = query.filter(func.date(Loan.returnDate) >= start, func.date(Loan.returnDate) <= end)
    elif normalized == 'overdue':
        query = query.filter(func.date(Loan.returnDate) < today)
    elif normalized == 'pending':
        pass

    if student_query:
        term = student_query.strip()
        query = query.filter(
            or_(
                User.userCompleteName.ilike(f"%{term}%"),
                User.identificationCode.ilike(f"%{term}%")
            )
        )

    pagination = query.order_by(Loan.returnDate.asc(), Loan.loanId.asc()).paginate(
        page=max(1, page),
        per_page=max(1, min(50, per_page)),
        error_out=False,
    )

    items = []
    due_today = 0
    overdue = 0
    for row in pagination.items:
        due_date = row.returnDate.date() if isinstance(row.returnDate, datetime) else row.returnDate
        if due_date < today:
            status_ui = 'atrasado'
            overdue += 1
        elif due_date == today:
            status_ui = 'vence_hoje'
            due_today += 1
        else:
            status_ui = 'no_prazo'

        days_overdue = max((today - due_date).days, 0)
        items.append({
            'loan_id': row.loanId,
            'book_name': row.bookName,
            'student_name': row.userCompleteName,
            'student_code': row.identificationCode,
            'pcd': bool(row.pcd),
            'loan_date': row.loanDate.isoformat() if row.loanDate else None,
            'due_date': row.returnDate.isoformat() if row.returnDate else None,
            'amount': row.amount,
            'status_name': row.status.name if row.status else None,
            'status_label': row.status.value if row.status else None,
            'status_ui': status_ui,
            'days_overdue': days_overdue,
        })

    # KPIs operacionais com query dedicada para não depender da página atual.
    base_active = Loan.query.filter(Loan.status.in_([StatusLoan.ACTIVE, StatusLoan.OVERDUE]))
    kpi_today = base_active.filter(func.date(Loan.returnDate) == today).count()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    kpi_week = base_active.filter(func.date(Loan.returnDate) >= start, func.date(Loan.returnDate) <= end).count()
    kpi_pending = base_active.count()
    kpi_overdue = base_active.filter(func.date(Loan.returnDate) < today).count()

    return {
        'items': items,
        'kpis': {
            'today': kpi_today,
            'week': kpi_week,
            'pending': kpi_pending,
            'overdue': kpi_overdue,
        },
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }
    }


def get_top_tags(limit=10):
    limit = max(1, min(int(limit), 30))
    cache_key = f"tags:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    rows = (
        db.session.query(
            KeyWord.wordId,
            KeyWord.word,
            func.count(KeyWordBook.wordId).label('usage_count'),
        )
        .join(KeyWordBook, KeyWord.wordId == KeyWordBook.wordId)
        .join(Book, Book.bookId == KeyWordBook.bookId)
        .filter(KeyWord.deleted.is_(False), Book.deleted.is_(False))
        .group_by(KeyWord.wordId, KeyWord.word)
        .order_by(desc('usage_count'), KeyWord.word.asc())
        .limit(limit)
        .all()
    )

    total_usage = sum(int(row.usage_count) for row in rows) or 1
    payload = {
        'items': [
            {
                'word_id': row.wordId,
                'word': row.word,
                'count': int(row.usage_count),
                'percentage': round((int(row.usage_count) / total_usage) * 100, 2),
            }
            for row in rows
        ]
    }
    _cache_set(cache_key, payload, _CACHE_TTL_SHORT)
    return payload


def get_ultimos_emprestimos(limit=10):
    limit = max(1, min(int(limit), 50))
    rows = (
        db.session.query(
            Loan.loanId,
            Loan.loanDate,
            Loan.returnDate,
            Loan.amount,
            Loan.status,
            Book.bookId,
            Book.bookName,
            User.userCompleteName,
            User.identificationCode,
        )
        .join(Book, Book.bookId == Loan.bookId)
        .join(User, User.userId == Loan.userId)
        .filter(Book.deleted.is_(False), User.deleted.is_(False))
        .order_by(Loan.loanDate.desc(), Loan.loanId.desc())
        .limit(limit)
        .all()
    )

    book_ids = [row.bookId for row in rows]
    tag_rows = []
    if book_ids:
        tag_rows = (
            db.session.query(KeyWordBook.bookId, KeyWord.word)
            .join(KeyWord, KeyWord.wordId == KeyWordBook.wordId)
            .filter(KeyWordBook.bookId.in_(book_ids), KeyWord.deleted.is_(False))
            .order_by(KeyWord.word.asc())
            .all()
        )

    book_tag_map: dict[int, str] = {}
    for tag_row in tag_rows:
        if tag_row.bookId not in book_tag_map:
            book_tag_map[tag_row.bookId] = tag_row.word

    return {
        'items': [
            {
                'loan_id': row.loanId,
                'book_name': row.bookName,
                'student_name': row.userCompleteName,
                'student_code': row.identificationCode,
                'loan_date': row.loanDate.isoformat() if row.loanDate else None,
                'due_date': row.returnDate.isoformat() if row.returnDate else None,
                'status_name': row.status.name if row.status else None,
                'status_label': row.status.value if row.status else None,
                'amount': row.amount,
                'principal_tag': book_tag_map.get(row.bookId),
            }
            for row in rows
        ]
    }


def get_engajamento(period='all', serie=None, turma=None, periodo_escolar=None, top_limit=10):
    top_limit = max(1, min(int(top_limit), 25))
    normalized_period = (period or 'all').lower()
    cache_key = f"eng:{normalized_period}:{serie or ''}:{turma or ''}:{periodo_escolar or ''}:{top_limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    start, end = _period_bounds(normalized_period)
    period_expr = _extract_period_expr()

    base = (
        db.session.query(Loan, User)
        .join(User, User.userId == Loan.userId)
        .filter(User.deleted.is_(False))
    )
    if start:
        base = base.filter(func.date(Loan.loanDate) >= start)
    if end:
        base = base.filter(func.date(Loan.loanDate) <= end)
    base = _apply_engajamento_filters(base, serie=serie, turma=turma, periodo_escolar=periodo_escolar)

    turma_rows = (
        base.with_entities(
            func.coalesce(User.className, literal('Sem turma')).label('turma'),
            func.count(Loan.loanId).label('total_loans')
        )
        .group_by('turma')
        .order_by(desc('total_loans'), 'turma')
        .all()
    )

    serie_rows = (
        base.with_entities(
            func.coalesce(User.gradeNumber, literal(0)).label('serie'),
            func.count(Loan.loanId).label('total_loans')
        )
        .group_by('serie')
        .order_by('serie')
        .all()
    )

    period_rows = (
        base.with_entities(
            period_expr.label('periodo_escolar'),
            func.count(Loan.loanId).label('total_loans')
        )
        .group_by('periodo_escolar')
        .order_by(desc('total_loans'))
        .all()
    )

    top_students_rows = (
        base.with_entities(
            User.userId,
            User.userCompleteName,
            User.identificationCode,
            func.count(Loan.loanId).label('total_loans')
        )
        .group_by(User.userId, User.userCompleteName, User.identificationCode)
        .order_by(desc('total_loans'), User.userCompleteName.asc())
        .limit(top_limit)
        .all()
    )

    payload = {
        'emprestimos_por_turma': [
            {'turma': row.turma or 'Sem turma', 'count': int(row.total_loans)} for row in turma_rows
        ],
        'emprestimos_por_serie': [
            {'serie': str(row.serie) if row.serie else 'Sem série', 'count': int(row.total_loans)} for row in serie_rows
        ],
        'comparativo_periodo': [
            {'periodo': row.periodo_escolar, 'count': int(row.total_loans)} for row in period_rows
        ],
        'top_alunos': [
            {
                'rank': idx + 1,
                'user_id': row.userId,
                'name': row.userCompleteName,
                'code': row.identificationCode,
                'count': int(row.total_loans),
            }
            for idx, row in enumerate(top_students_rows)
        ]
    }

    _cache_set(cache_key, payload, _CACHE_TTL_MEDIUM)
    return payload


def get_popularidade(range_name='anual', serie=None, turma=None, periodo_escolar=None, limit=10):
    limit = max(1, min(int(limit), 20))
    normalized_range = (range_name or 'anual').lower()
    cache_key = f"pop:{normalized_range}:{serie or ''}:{turma or ''}:{periodo_escolar or ''}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    start, end = _popularidade_bounds(normalized_range)

    base = (
        db.session.query(Loan, Book, User)
        .join(Book, Book.bookId == Loan.bookId)
        .join(User, User.userId == Loan.userId)
        .filter(Book.deleted.is_(False), User.deleted.is_(False))
    )
    if start:
        base = base.filter(func.date(Loan.loanDate) >= start)
    if end:
        base = base.filter(func.date(Loan.loanDate) <= end)
    base = _apply_engajamento_filters(base, serie=serie, turma=turma, periodo_escolar=periodo_escolar)

    top_books = (
        base.with_entities(
            Book.bookId,
            Book.bookName,
            Book.authorName,
            func.count(Loan.loanId).label('total_loans')
        )
        .group_by(Book.bookId, Book.bookName, Book.authorName)
        .order_by(desc('total_loans'), Book.bookName.asc())
        .limit(limit)
        .all()
    )

    tag_rows = (
        base.with_entities(
            KeyWord.word,
            func.count(Loan.loanId).label('total_loans')
        )
        .join(KeyWordBook, KeyWordBook.bookId == Book.bookId)
        .join(KeyWord, KeyWord.wordId == KeyWordBook.wordId)
        .filter(KeyWord.deleted.is_(False))
        .group_by(KeyWord.word)
        .order_by(desc('total_loans'), KeyWord.word.asc())
        .limit(limit)
        .all()
    )

    payload = {
        'top_livros': [
            {
                'book_id': row.bookId,
                'title': row.bookName,
                'author': row.authorName,
                'count': int(row.total_loans),
            }
            for row in top_books
        ],
        'distribuicao_tags': [
            {
                'tag': row.word,
                'count': int(row.total_loans),
            }
            for row in tag_rows
        ]
    }

    _cache_set(cache_key, payload, _CACHE_TTL_MEDIUM)
    return payload


def get_acervo_data(days_lost=None, limit=20):
    limit = max(1, min(int(limit), 50))
    threshold = int(days_lost) if days_lost else _lost_threshold_days()
    threshold = threshold if threshold > 0 else 30

    cache_key = f"acervo:{threshold}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    today = date.today()
    overdue_cut = today - timedelta(days=threshold)

    lost_query = (
        db.session.query(
            Loan.loanId,
            Loan.loanDate,
            Loan.returnDate,
            Loan.status,
            Book.bookName,
            User.userCompleteName,
            User.identificationCode,
        )
        .join(Book, Book.bookId == Loan.bookId)
        .join(User, User.userId == Loan.userId)
        .filter(Book.deleted.is_(False), User.deleted.is_(False))
        .filter(
            or_(
                Loan.status == StatusLoan.LOST,
                and_(
                    Loan.status.in_([StatusLoan.ACTIVE, StatusLoan.OVERDUE]),
                    func.date(Loan.returnDate) < overdue_cut,
                )
            )
        )
        .order_by(Loan.returnDate.asc(), Loan.loanId.asc())
    )

    rows = lost_query.limit(limit).all()
    total_lost = lost_query.count()

    payload = {
        'lost_threshold_days': threshold,
        'lost_count': int(total_lost),
        'items': [
            {
                'loan_id': row.loanId,
                'book_name': row.bookName,
                'last_user_name': row.userCompleteName,
                'last_user_code': row.identificationCode,
                'loan_date': row.loanDate.isoformat() if row.loanDate else None,
                'due_date': row.returnDate.isoformat() if row.returnDate else None,
                'status_name': row.status.name if row.status else None,
                'status_label': row.status.value if row.status else None,
                'days_overdue': max((today - row.returnDate.date()).days, 0) if row.returnDate else 0,
            }
            for row in rows
        ]
    }

    _cache_set(cache_key, payload, _CACHE_TTL_SHORT)
    return payload


def _safe_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _apply_loan_date_window(query, *, period=None, range_name=None):
    if range_name:
        start, end = _popularidade_bounds(range_name)
    else:
        start, end = _period_bounds(period or 'all')

    if start:
        query = query.filter(func.date(Loan.loanDate) >= start)
    if end:
        query = query.filter(func.date(Loan.loanDate) <= end)
    return query


def get_drilldown_details(
    source,
    *,
    label=None,
    key=None,
    period='all',
    range_name='anual',
    serie=None,
    turma=None,
    periodo_escolar=None,
    limit=50,
):
    normalized_source = (source or '').strip().lower()
    safe_limit = max(1, min(_safe_int(limit) or 20, 100))

    if normalized_source == 'tags_top':
        tag_id = _safe_int(key)
        query = (
            db.session.query(
                Loan.loanId,
                Loan.loanDate,
                Loan.status,
                Book.bookName,
                User.userCompleteName,
                User.identificationCode,
            )
            .join(Book, Book.bookId == Loan.bookId)
            .join(User, User.userId == Loan.userId)
            .join(KeyWordBook, KeyWordBook.bookId == Book.bookId)
            .join(KeyWord, KeyWord.wordId == KeyWordBook.wordId)
            .filter(Book.deleted.is_(False), User.deleted.is_(False), KeyWord.deleted.is_(False))
        )
        if tag_id is not None:
            query = query.filter(KeyWord.wordId == tag_id)
        elif label:
            query = query.filter(KeyWord.word == label)

        rows = query.order_by(Loan.loanDate.desc(), Loan.loanId.desc()).limit(safe_limit).all()
        return {
            'title': f'Detalhes da tag: {label or "-"}',
            'items': [
                {
                    'headline': row.bookName,
                    'detail': f"{row.userCompleteName or '-'} ({row.identificationCode or '-'})",
                    'meta': f"Empréstimo: {row.loanDate.isoformat() if row.loanDate else '-'} | Status: {row.status.value if row.status else '-'}",
                }
                for row in rows
            ],
        }

    if normalized_source == 'popularidade_livros':
        book_id = _safe_int(key)
        query = (
            db.session.query(
                Loan.loanId,
                Loan.loanDate,
                Loan.returnDate,
                Loan.status,
                User.userCompleteName,
                User.identificationCode,
                Book.bookName,
                Book.authorName,
            )
            .join(Book, Book.bookId == Loan.bookId)
            .join(User, User.userId == Loan.userId)
            .filter(Book.deleted.is_(False), User.deleted.is_(False))
        )
        query = _apply_loan_date_window(query, range_name=range_name)
        query = _apply_engajamento_filters(query, serie=serie, turma=turma, periodo_escolar=periodo_escolar)
        if book_id is not None:
            query = query.filter(Book.bookId == book_id)
        elif label:
            query = query.filter(Book.bookName.ilike(f"%{label}%"))

        rows = query.order_by(Loan.loanDate.desc(), Loan.loanId.desc()).limit(safe_limit).all()
        return {
            'title': f'Detalhes do livro: {label or "-"}',
            'items': [
                {
                    'headline': row.bookName,
                    'detail': f"{row.userCompleteName or '-'} ({row.identificationCode or '-'})",
                    'meta': f"Empréstimo: {row.loanDate.isoformat() if row.loanDate else '-'} | Previsto: {row.returnDate.isoformat() if row.returnDate else '-'} | Status: {row.status.value if row.status else '-'}",
                }
                for row in rows
            ],
        }

    if normalized_source == 'popularidade_tags':
        tag_id = _safe_int(key)
        query = (
            db.session.query(
                Loan.loanId,
                Loan.loanDate,
                Loan.status,
                Book.bookName,
                User.userCompleteName,
                User.identificationCode,
                KeyWord.word,
            )
            .join(Book, Book.bookId == Loan.bookId)
            .join(User, User.userId == Loan.userId)
            .join(KeyWordBook, KeyWordBook.bookId == Book.bookId)
            .join(KeyWord, KeyWord.wordId == KeyWordBook.wordId)
            .filter(Book.deleted.is_(False), User.deleted.is_(False), KeyWord.deleted.is_(False))
        )
        query = _apply_loan_date_window(query, range_name=range_name)
        query = _apply_engajamento_filters(query, serie=serie, turma=turma, periodo_escolar=periodo_escolar)
        if tag_id is not None:
            query = query.filter(KeyWord.wordId == tag_id)
        elif label:
            query = query.filter(KeyWord.word == label)

        rows = query.order_by(Loan.loanDate.desc(), Loan.loanId.desc()).limit(safe_limit).all()
        return {
            'title': f'Detalhes da categoria: {label or "-"}',
            'items': [
                {
                    'headline': row.bookName,
                    'detail': f"{row.userCompleteName or '-'} ({row.identificationCode or '-'})",
                    'meta': f"Tag: {row.word} | Empréstimo: {row.loanDate.isoformat() if row.loanDate else '-'} | Status: {row.status.value if row.status else '-'}",
                }
                for row in rows
            ],
        }

    if normalized_source in {'engajamento_turma', 'engajamento_serie', 'engajamento_periodo'}:
        query = (
            db.session.query(
                User.userId,
                User.userCompleteName,
                User.identificationCode,
                func.count(Loan.loanId).label('total_loans'),
            )
            .join(Loan, Loan.userId == User.userId)
            .filter(User.deleted.is_(False))
        )
        query = _apply_loan_date_window(query, period=period)
        query = _apply_engajamento_filters(query, serie=serie, turma=turma, periodo_escolar=periodo_escolar)

        if normalized_source == 'engajamento_turma' and label:
            query = query.filter(func.coalesce(User.className, '') == label)
        if normalized_source == 'engajamento_serie':
            serie_num = _safe_int(key if key is not None else label)
            if serie_num is not None:
                query = query.filter(User.gradeNumber == serie_num)
        if normalized_source == 'engajamento_periodo' and label:
            query = query.filter(_extract_period_expr() == str(label).lower())

        rows = (
            query.group_by(User.userId, User.userCompleteName, User.identificationCode)
            .order_by(desc('total_loans'), User.userCompleteName.asc())
            .limit(safe_limit)
            .all()
        )

        return {
            'title': f'Detalhes de engajamento: {label or "-"}',
            'items': [
                {
                    'headline': row.userCompleteName or '-',
                    'detail': f"Código: {row.identificationCode or '-'}",
                    'meta': f"Total de empréstimos: {int(row.total_loans)}",
                }
                for row in rows
            ],
        }

    return {
        'title': 'Detalhamento',
        'items': [],
    }
