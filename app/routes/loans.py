from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, jsonify, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from app.forms import LoanForm
from app.models import Book, Configuration, KeyWord, Loan, StatusLoan, User
from app.utils import calc_age, enforce_api_feature_access, enforce_feature_access, get_config_bool, parse_date
from app.validaEmprestimo import validaEmprestimo
from app import db

bp = Blueprint('loans', __name__)


def _parse_int(value):
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _add_date_range_filter(query, column, start_raw, end_raw):
    start_date = parse_date((start_raw or '').strip())
    end_date = parse_date((end_raw or '').strip())
    if start_date:
        query = query.filter(column >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(column <= datetime.combine(end_date, datetime.max.time()))
    return query


def _build_sort_links(endpoint, base_params, sort_columns, current_sort_by, current_sort_dir):
    links = {}
    for key in sort_columns.keys():
        params = {k: v for k, v in base_params.items() if v is not None and v != ''}
        params['page'] = 1

        if current_sort_by != key:
            params['sort_by'] = key
            params['sort_dir'] = 'asc'
        elif current_sort_dir == 'asc':
            params['sort_by'] = key
            params['sort_dir'] = 'desc'
        else:
            params.pop('sort_by', None)
            params.pop('sort_dir', None)

        links[key] = url_for(endpoint, **params)
    return links

@bp.route('/emprestimos')
@login_required
def emprestimos():
    denial = enforce_feature_access('loans_browse', 'Acesso negado para visualizar empréstimos.')
    if denial:
        return denial

    query = Loan.query
    created_by_user = aliased(User)
    include_deleted = request.args.get('include_deleted') == '1'
    include_deleted_value = '1' if include_deleted else ''
    search_term = (request.args.get('search') or '').strip()
    sort_by = (request.args.get('sort_by') or '').strip()
    sort_dir = (request.args.get('sort_dir') or '').strip().lower()

    advanced_filters = {
        'loan_date_start': (request.args.get('loan_date_start') or '').strip(),
        'loan_date_end': (request.args.get('loan_date_end') or '').strip(),
        'return_date_start': (request.args.get('return_date_start') or '').strip(),
        'return_date_end': (request.args.get('return_date_end') or '').strip(),
        'loan_status': (request.args.get('loan_status') or '').strip(),
        'loan_amount_min': (request.args.get('loan_amount_min') or '').strip(),
        'loan_amount_max': (request.args.get('loan_amount_max') or '').strip(),
        'loan_created_by': (request.args.get('loan_created_by') or '').strip(),

        'user_code': (request.args.get('user_code') or '').strip(),
        'user_name': (request.args.get('user_name') or '').strip(),
        'user_type': (request.args.get('user_type') or '').strip(),
        'user_birth_start': (request.args.get('user_birth_start') or '').strip(),
        'user_birth_end': (request.args.get('user_birth_end') or '').strip(),
        'user_cpf': (request.args.get('user_cpf') or '').strip(),
        'user_rg': (request.args.get('user_rg') or '').strip(),
        'user_phone': (request.args.get('user_phone') or '').strip(),
        'user_grade': (request.args.get('user_grade') or '').strip(),
        'user_class': (request.args.get('user_class') or '').strip(),

        'book_name': (request.args.get('book_name') or '').strip(),
        'book_author': (request.args.get('book_author') or '').strip(),
        'book_publisher': (request.args.get('book_publisher') or '').strip(),
        'book_published_start': (request.args.get('book_published_start') or '').strip(),
        'book_published_end': (request.args.get('book_published_end') or '').strip(),
        'book_acquired_start': (request.args.get('book_acquired_start') or '').strip(),
        'book_acquired_end': (request.args.get('book_acquired_end') or '').strip(),
        'book_description': (request.args.get('book_description') or '').strip(),
        'book_tags': (request.args.get('book_tags') or '').strip(),
    }

    needs_user_join = bool(
        search_term
        or advanced_filters['user_code']
        or advanced_filters['user_name']
        or advanced_filters['user_type']
        or advanced_filters['user_birth_start']
        or advanced_filters['user_birth_end']
        or advanced_filters['user_cpf']
        or advanced_filters['user_rg']
        or advanced_filters['user_phone']
        or advanced_filters['user_grade']
        or advanced_filters['user_class']
    )
    needs_book_join = bool(
        search_term
        or advanced_filters['book_name']
        or advanced_filters['book_author']
        or advanced_filters['book_publisher']
        or advanced_filters['book_published_start']
        or advanced_filters['book_published_end']
        or advanced_filters['book_acquired_start']
        or advanced_filters['book_acquired_end']
        or advanced_filters['book_description']
        or advanced_filters['book_tags']
    )
    needs_created_user_join = bool(advanced_filters['loan_created_by'])
    needs_keyword_join = bool(advanced_filters['book_tags'])

    sort_columns = {
        'book': Book.bookName,
        'user': User.identificationCode,
        'loan_date': Loan.loanDate,
        'return_date': Loan.returnDate,
        'status': Loan.status,
        'deleted': or_(User.deleted.is_(True), Book.deleted.is_(True)),
    }
    if sort_by not in sort_columns:
        sort_by = ''
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = ''

    if sort_by == 'book':
        needs_book_join = True
    if sort_by == 'user':
        needs_user_join = True
    if sort_by == 'deleted':
        needs_book_join = True
        needs_user_join = True

    if needs_user_join:
        query = query.join(Loan.user)
    if needs_book_join:
        query = query.join(Loan.book)
    if needs_created_user_join:
        query = query.join(created_by_user, Loan.created_user)
    if needs_keyword_join:
        query = query.outerjoin(Book.keywords)

    if not include_deleted:
        query = query.filter(
            Loan.user.has(User.deleted.is_(False)),
            Loan.book.has(Book.deleted.is_(False)),
        )

    if search_term:
        query = query.filter(
            or_(
                User.userCompleteName.ilike(f'%{search_term}%'),
                User.identificationCode.ilike(f'%{search_term}%'),
                Book.bookName.ilike(f'%{search_term}%')
            )
        )

    # Categoria: Empréstimos
    query = _add_date_range_filter(
        query,
        Loan.loanDate,
        advanced_filters['loan_date_start'],
        advanced_filters['loan_date_end']
    )
    query = _add_date_range_filter(
        query,
        Loan.returnDate,
        advanced_filters['return_date_start'],
        advanced_filters['return_date_end']
    )
    if advanced_filters['loan_status']:
        status_name = advanced_filters['loan_status'].upper()
        if status_name in StatusLoan.__members__:
            query = query.filter(Loan.status == StatusLoan[status_name])

    amount_min = _parse_int(advanced_filters['loan_amount_min'])
    amount_max = _parse_int(advanced_filters['loan_amount_max'])
    if amount_min is not None:
        query = query.filter(Loan.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Loan.amount <= amount_max)

    if advanced_filters['loan_created_by']:
        query = query.filter(
            or_(
                created_by_user.identificationCode.ilike(f"%{advanced_filters['loan_created_by']}%"),
                created_by_user.userCompleteName.ilike(f"%{advanced_filters['loan_created_by']}%")
            )
        )

    # Categoria: Usuário
    if advanced_filters['user_code']:
        query = query.filter(User.identificationCode.ilike(f"%{advanced_filters['user_code']}%"))
    if advanced_filters['user_name']:
        query = query.filter(User.userCompleteName.ilike(f"%{advanced_filters['user_name']}%"))
    if advanced_filters['user_type']:
        query = query.filter(User.userType.ilike(f"%{advanced_filters['user_type']}%"))
    query = _add_date_range_filter(
        query,
        User.birthDate,
        advanced_filters['user_birth_start'],
        advanced_filters['user_birth_end']
    )
    if advanced_filters['user_cpf']:
        query = query.filter(User.cpf.ilike(f"%{advanced_filters['user_cpf']}%"))
    if advanced_filters['user_rg']:
        query = query.filter(User.rg.ilike(f"%{advanced_filters['user_rg']}%"))
    if advanced_filters['user_phone']:
        query = query.filter(User.userPhone.ilike(f"%{advanced_filters['user_phone']}%"))
    user_grade = _parse_int(advanced_filters['user_grade'])
    if user_grade is not None:
        query = query.filter(User.gradeNumber == user_grade)
    if advanced_filters['user_class']:
        query = query.filter(User.className.ilike(f"%{advanced_filters['user_class']}%"))

    # Categoria: Livro
    if advanced_filters['book_name']:
        query = query.filter(Book.bookName.ilike(f"%{advanced_filters['book_name']}%"))
    if advanced_filters['book_author']:
        query = query.filter(Book.authorName.ilike(f"%{advanced_filters['book_author']}%"))
    if advanced_filters['book_publisher']:
        query = query.filter(Book.publisherName.ilike(f"%{advanced_filters['book_publisher']}%"))

    book_published_start = parse_date(advanced_filters['book_published_start'])
    book_published_end = parse_date(advanced_filters['book_published_end'])
    if book_published_start:
        query = query.filter(Book.publishedDate >= book_published_start)
    if book_published_end:
        query = query.filter(Book.publishedDate <= book_published_end)

    query = _add_date_range_filter(
        query,
        Book.acquisitionDate,
        advanced_filters['book_acquired_start'],
        advanced_filters['book_acquired_end']
    )

    if advanced_filters['book_description']:
        query = query.filter(Book.description.ilike(f"%{advanced_filters['book_description']}%"))

    if advanced_filters['book_tags']:
        tags = [tag.strip() for tag in advanced_filters['book_tags'].split(',') if tag.strip()]
        if tags:
            query = query.filter(or_(*[KeyWord.word.ilike(f'%{tag}%') for tag in tags]))

    # DISTINCT is only required when joining keywords (many-to-many),
    # which can duplicate loans rows.
    if needs_keyword_join:
        query = query.distinct()

    if sort_by and sort_dir:
        sort_column = sort_columns[sort_by]
        if sort_dir == 'asc':
            query = query.order_by(sort_column.asc().nullslast())
        else:
            query = query.order_by(sort_column.desc().nullslast())
    else:
        query = query.order_by(Loan.loanDate.desc())

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    loans_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    base_params = {
        'search': search_term,
        'per_page': per_page,
        'include_deleted': include_deleted_value,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        **advanced_filters,
    }
    sort_links = _build_sort_links('loans.emprestimos', base_params, sort_columns, sort_by, sort_dir)

    # Get cancellation limit from config (in minutes)
    config_entry = Configuration.query.filter_by(key='TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO').first()
    cancellation_limit_minutes = int(config_entry.value) if config_entry and config_entry.value and config_entry.value.isdigit() else 0
    now = datetime.now()
    
    return render_template(
        'emprestimos.html',
        loans=loans_pagination,
        search_term=search_term,
        per_page=per_page,
        cancellation_limit_minutes=cancellation_limit_minutes,
        now=now,
        filters=advanced_filters,
        include_deleted=include_deleted,
        include_deleted_value=include_deleted_value,
        status_options=StatusLoan,
        sort_by=sort_by,
        sort_dir=sort_dir,
        sort_links=sort_links,
    )

@bp.route('/emprestimos/cancel/<int:loan_id>', methods=['POST'])
@login_required
def cancelar_emprestimo(loan_id):
    denial = enforce_api_feature_access('loans_cancel')
    if denial:
        return denial

    loan = db.session.get(Loan, loan_id)
    if not loan:
        abort(404)
    
    if loan.status != StatusLoan.ACTIVE:
        return jsonify({'success': False, 'message': 'Apenas empréstimos ativos podem ser cancelados.'}), 400

    config_entry = Configuration.query.filter_by(key='TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO').first()
    limit_minutes = int(config_entry.value) if config_entry and config_entry.value and config_entry.value.isdigit() else 0
    
    if limit_minutes <= 0:
         return jsonify({'success': False, 'message': 'Cancelamento não permitido por configuração.'}), 403

    elapsed = datetime.now() - loan.creationDate
    if elapsed.total_seconds() / 60 > limit_minutes:
        return jsonify({'success': False, 'message': 'Tempo limite para cancelamento excedido.'}), 403

    # Cancelar
    loan.status = StatusLoan.CANCELLED
    loan.finalNote = "Cancelado pelo usuário dentro do prazo permitido."
    loan.updatedBy = current_user.userId
    loan.lastUpdate = datetime.now()
    
    db.session.commit()
    flash('Empréstimo cancelado com sucesso.', 'success')
    return jsonify({'success': True})

@bp.route('/emprestimos/form', defaults={'loan_id': None}, methods=['GET'])
@bp.route('/emprestimos/form/<int:loan_id>', methods=['GET'])
@login_required
def get_loan_form(loan_id):
    denial = enforce_feature_access('loans_manage', 'Acesso negado para acessar o formulário de empréstimos.')
    if denial:
        return denial

    cancellation_available = False
    can_edit_initial_note = False
    can_edit_final_note = False
    now = datetime.now()
    if loan_id:
        loan = db.session.get(Loan, loan_id)
        if not loan:
            abort(404)
        form = LoanForm(obj=loan)
        user = loan.user
        book = loan.book

        # Check cancellation availability for this specific loan
        if loan.status == StatusLoan.ACTIVE:
            config_entry = Configuration.query.filter_by(key='TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO').first()
            cancellation_limit_minutes = int(config_entry.value) if config_entry and config_entry.value and config_entry.value.isdigit() else 0
            if cancellation_limit_minutes > 0:
                elapsed = (now - loan.creationDate).total_seconds() / 60
                if elapsed <= cancellation_limit_minutes:
                    cancellation_available = True

        is_active_loan = loan.status in (StatusLoan.ACTIVE, StatusLoan.OVERDUE)
        is_finalized_loan = loan.status in (StatusLoan.COMPLETED, StatusLoan.LOST)

        if is_active_loan:
            can_edit_initial_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_ATIVO')
        elif is_finalized_loan:
            can_edit_initial_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_FINALIZADO')
            can_edit_final_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_FINAL_EMPRESTIMO_FINALIZADO')

        loan_user_info = {
            'identificationCode': getattr(user, 'identificationCode', None) or '—',
            'name': getattr(user, 'userCompleteName', None) or getattr(user, 'username', None) or '—',
            'age': calc_age(getattr(user, 'birthDate', None)) if user else None,
            'birthDate': user.birthDate.strftime('%d/%m/%Y') if user and user.birthDate else '—',
            'gradeNumber': getattr(user, 'gradeNumber', None) or '—',
            'className': getattr(user, 'className', None) or '—',
            'cpf': getattr(user, 'cpf', None) or '—',
            'rg': getattr(user, 'rg', None) or '—',
        }

        loan_book_info = {
            'bookName': getattr(book, 'bookName', None) or '—',
            'authorName': getattr(book, 'authorName', None) or '—',
            'publisherName': getattr(book, 'publisherName', None) or '—',
            'publishedDate': book.publishedDate.strftime('%d/%m/%Y') if book and book.publishedDate else '—',
            'loanedAmount': loan.amount,
            'keywords': ', '.join([kw.word for kw in book.keywords]) if book and getattr(book, 'keywords', None) else '—',
        }
    else:
        loan = None
        form = LoanForm()
        loan_user_info = None
        loan_book_info = None
    return render_template(
        '_loan_form.html',
        form=form,
        loan_id=loan_id,
        loan=loan,
        loan_user_info=loan_user_info,
        loan_book_info=loan_book_info,
        cancellation_available=cancellation_available,
        can_edit_initial_note=can_edit_initial_note,
        can_edit_final_note=can_edit_final_note
    )

@bp.route('/emprestimos/new', methods=['POST'])
@login_required
def novo_emprestimo():
    denial = enforce_api_feature_access('loans_manage')
    if denial:
        return denial

    form = LoanForm()
    if form.validate_on_submit() and validaEmprestimo(form, Loan, Book, StatusLoan):
        new_loan = Loan(
            amount=form.amount.data,
            loanDate=form.loanDate.data,
            returnDate=form.returnDate.data,
            userId=form.userId.data,
            bookId=form.bookId.data,
            initialNote=form.initialNote.data,
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
            status=StatusLoan.ACTIVE,
        )
        db.session.add(new_loan)
        db.session.commit()
        flash('Empréstimo cadastrado com sucesso!', 'success')
        return jsonify({'success': True})
    
    errors = form.errors
    if not validaEmprestimo(form, Loan, Book, StatusLoan):
        errors['validation'] = ['Falha na validação customizada (ex: livro indisponível).']
        
    return jsonify({'success': False, 'errors': errors})

@bp.route('/emprestimos/edit/<int:loan_id>', methods=['POST'])
@login_required
def editar_emprestimo(loan_id):
    denial = enforce_api_feature_access('loans_manage')
    if denial:
        return denial

    loan = db.session.get(Loan, loan_id)
    if not loan:
        abort(404)
    raw_return_date = (request.form.get('returnDate') or '').strip()
    raw_initial_note = (request.form.get('initialNote') or '').strip()
    raw_final_note = (request.form.get('finalNote') or '').strip()
    informed_return_date = parse_date(raw_return_date)

    if not informed_return_date:
        return jsonify({'success': False, 'errors': {'returnDate': ['Informe uma data de devolução válida no formato YYYY-MM-DD.']}})

    if informed_return_date < loan.loanDate.date():
        return jsonify({'success': False, 'errors': {'returnDate': ['A data de devolução não pode ser anterior à data de empréstimo.']}})

    current_initial_note = (loan.initialNote or '').strip()
    current_final_note = (loan.finalNote or '').strip()

    is_active_loan = loan.status in (StatusLoan.ACTIVE, StatusLoan.OVERDUE)
    is_finalized_loan = loan.status in (StatusLoan.COMPLETED, StatusLoan.LOST)

    can_edit_initial_note = False
    can_edit_final_note = False
    if is_active_loan:
        can_edit_initial_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_ATIVO')
    elif is_finalized_loan:
        can_edit_initial_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_FINALIZADO')
        can_edit_final_note = get_config_bool('PERMITE_ALTERAR_OBSERVACAO_FINAL_EMPRESTIMO_FINALIZADO')

    errors = {}
    if raw_initial_note != current_initial_note and not can_edit_initial_note:
        errors['initialNote'] = ['Alteração da observação inicial não permitida para este empréstimo.']

    if raw_final_note != current_final_note and not can_edit_final_note:
        errors['finalNote'] = ['Alteração da observação final não permitida para este empréstimo.']

    if errors:
        return jsonify({'success': False, 'errors': errors})

    # Regras de imutabilidade na edição:
    # não permitir alterar livro, usuário, quantidade e data de início.
    # apenas a data de devolução pode ser atualizada por esta rota.
    # Convert date back to datetime for consistent storage (default to midnight)
    loan.returnDate = datetime.combine(informed_return_date, datetime.min.time())
    if can_edit_initial_note:
        loan.initialNote = raw_initial_note
    if can_edit_final_note:
        loan.finalNote = raw_final_note
    loan.lastUpdate = datetime.now()
    loan.updatedBy = current_user.userId
    db.session.commit()
    flash('Empréstimo atualizado com sucesso!', 'success')
    return jsonify({'success': True})


@bp.route('/emprestimos/return/<int:loan_id>', methods=['POST'])
@login_required
def informar_retorno_emprestimo(loan_id):
    """
    Finaliza um empréstimo mantendo registro histórico.
    Regras:
    - status permitido apenas: COMPLETED ou LOST
    - returnDate deve ser informada pelo usuário (YYYY-MM-DD)
    - empréstimo já finalizado (COMPLETED/LOST) não pode ser finalizado novamente
    """
    denial = enforce_api_feature_access('loans_return')
    if denial:
        return denial

    loan = db.session.get(Loan, loan_id)
    if not loan:
        abort(404)

    # Aceita tanto form-data quanto JSON
    raw_status = (request.form.get('status') or (request.get_json(silent=True) or {}).get('status') or '').strip().upper()
    raw_return_date = (request.form.get('returnDate') or (request.get_json(silent=True) or {}).get('returnDate') or '').strip()
    raw_final_note = (request.form.get('finalNote') or (request.get_json(silent=True) or {}).get('finalNote') or '').strip()

    allowed = {'COMPLETED', 'LOST'}
    if raw_status not in allowed:
        return jsonify({
            'success': False,
            'errors': {'status': ['Status inválido. Use LOST ou COMPLETED.']}
        }), 400

    informed_return_date = parse_date(raw_return_date)
    if not informed_return_date:
        return jsonify({
            'success': False,
            'errors': {'returnDate': ['Informe uma data de devolução válida no formato YYYY-MM-DD.']}
        }), 400

    if informed_return_date < loan.loanDate.date():
        return jsonify({
            'success': False,
            'errors': {'returnDate': ['A data de devolução não pode ser anterior à data de empréstimo.']}
        }), 400

    if loan.status in (StatusLoan.COMPLETED, StatusLoan.LOST):
        return jsonify({
            'success': False,
            'errors': {'status': [f'Este empréstimo já foi finalizado como {loan.status.name}.']}
        }), 409

    # Se o livro foi perdido, remover a quantidade do estoque físico
    if raw_status == 'LOST':
        if not loan.book:
            return jsonify({
                'success': False,
                'errors': {'book': ['Livro do empréstimo não encontrado.']}
            }), 404
        if loan.book.amount < loan.amount:
            return jsonify({
                'success': False,
                'errors': {'amount': ['Estoque insuficiente para registrar perda desse empréstimo.']}
            }), 409
        loan.book.amount -= loan.amount
        loan.book.lastUpdate = datetime.now()
        loan.book.updatedBy = current_user.userId

    loan.returnDate = datetime.combine(informed_return_date, datetime.min.time())
    loan.status = StatusLoan[raw_status]
    loan.finalNote = raw_final_note
    loan.lastUpdate = datetime.now()
    loan.updatedBy = current_user.userId

    db.session.commit()
    flash('Retorno do empréstimo registrado com sucesso!', 'success')
    return jsonify({
        'success': True,
        'loanId': loan.loanId,
        'status': loan.status.name,
        'returnDate': loan.returnDate.isoformat()
    })


# Keyword Management Routes


@bp.route('/excluir_emprestimo/<int:id>', methods=['POST'])
@login_required
def excluir_emprestimo(id):
    denial = enforce_api_feature_access('loans_manage')
    if denial:
        return denial

    return jsonify({
        'success': False,
        'errors': {'delete': ['A exclusão de empréstimos está desativada no sistema.']}
    }), 403
    """
    emprestimo = Loan.query.get_or_404(id)
    db.session.delete(emprestimo)
    db.session.commit()
    flash('Empréstimo excluído com sucesso!', 'success')
    return redirect(url_for('loans.emprestimos'))
    """

