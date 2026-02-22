from datetime import date, datetime, timedelta

from flask import Blueprint, flash, jsonify, render_template, request
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app.forms import LoanForm
from app.models import Book, Configuration, Loan, StatusLoan, User
from app.utils import calc_age, get_config_bool, parse_date
from app.validaEmprestimo import validaEmprestimo
from app import db

bp = Blueprint('loans', __name__)

@bp.route('/emprestimos')
@login_required
def emprestimos():
    query = Loan.query
    search_term = (request.args.get('search') or '').strip()
    if search_term:
        query = query.join(Loan.user).join(Loan.book).filter(
            or_(
                User.userCompleteName.ilike(f'%{search_term}%'),
                User.identificationCode.ilike(f'%{search_term}%'),
                Book.bookName.ilike(f'%{search_term}%')
            )
        ).distinct()

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    loans_pagination = query.order_by(Loan.loanDate.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # Get cancellation limit from config (in minutes)
    config_entry = Configuration.query.filter_by(key='TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO').first()
    cancellation_limit_minutes = int(config_entry.value) if config_entry and config_entry.value and config_entry.value.isdigit() else 0
    now = datetime.now()
    
    return render_template('emprestimos.html', loans=loans_pagination, search_term=search_term, per_page=per_page, cancellation_limit_minutes=cancellation_limit_minutes, now=now)

@bp.route('/emprestimos/cancel/<int:loan_id>', methods=['POST'])
@login_required
def cancelar_emprestimo(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
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
    cancellation_available = False
    can_edit_initial_note = False
    can_edit_final_note = False
    now = datetime.now()
    if loan_id:
        loan = Loan.query.get_or_404(loan_id)
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
    loan = Loan.query.get_or_404(loan_id)
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
    loan = Loan.query.get_or_404(loan_id)

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

