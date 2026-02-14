from datetime import date, timedelta
from flask import flash, redirect, render_template, request, session, url_for, jsonify
from flask_login import current_user, login_required, login_user, logout_user, AnonymousUserMixin
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import func, or_
from flask import Blueprint

from . import bcrypt, db
from .dbExecute import addFromForm
from .forms import (BookForm, KeyWordForm, LoanForm, LoginForm, RegisterForm,
                    SearchBooksForm, UserForm, SearchLoansForm)


from .models import Book, KeyWord, KeyWordBook, Loan, StatusLoan, User
import unicodedata
from .validaEmprestimo import validaEmprestimo


bp = Blueprint('main', __name__)


def splitStringIntoList(string):
    if not string:
        return []
    string_list = [item.strip().lower() for item in string.split(';') if item.strip()]
    return string_list

def _normalize_tag(token: str) -> str:
    if not token:
        return ''
    # remove leading/trailing spaces
    token = token.strip()
    # remove accents
    nfkd = unicodedata.normalize('NFKD', token)
    ascii_only = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    # uppercase
    up = ascii_only.upper()
    # keep only allowed chars: A-Z, 0-9, space, hyphen
    allowed = []
    for ch in up:
        if ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch in [' ', '-']:
            allowed.append(ch)
    cleaned = ''.join(allowed)
    # collapse multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def _calc_age(birth_date):
    if not birth_date:
        return None
    try:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except Exception:
        return None

def _parse_date(value: str):
    if not value:
        return None
    try:
        # espera AAAA-MM-DD
        return date.fromisoformat(value)
    except Exception:
        return None

def _available_copies_for_range(book, start_date, end_date):
    if not book:
        return 0
    q = db.session.query(func.coalesce(func.sum(Loan.amount), 0)).filter(
        Loan.bookId == book.bookId,
        Loan.status == StatusLoan.ACTIVE
    )
    if start_date and end_date:
        # empréstimos que se sobrepõem ao intervalo
        q = q.filter(Loan.loanDate <= end_date, Loan.returnDate >= start_date)
    else:
        # disponibilidade hoje
        today = date.today()
        q = q.filter(Loan.loanDate <= today, Loan.returnDate >= today)
    used = q.scalar() or 0
    available = book.amount - used
    return max(available, 0)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    if current_user.userType == 'admin':
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.menu'))


@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.userType != 'admin':
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('main.menu'))

    # KPIs
    total_books = db.session.query(func.sum(Book.amount)).scalar() or 0
    total_loans_active = Loan.query.filter_by(status=StatusLoan.ACTIVE).count()
    total_students = User.query.filter(func.lower(User.userType).in_(['aluno', 'student'])).count()
    total_staff = User.query.filter(
        func.lower(User.userType).in_(['colaborador', 'bibliotecario', 'bibliotecário', 'staff'])
    ).count()
    overdue_loans_count = Loan.query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE).count()

    # Loan filtering
    loan_filter = request.args.get('filter', 'today')
    page = request.args.get(get_page_parameter(), 1, type=int)
    per_page = int(request.args.get('per_page', 10))
    
    loans_query = Loan.query.filter(Loan.status == StatusLoan.ACTIVE)
    if loan_filter == 'today':
        loans_query = loans_query.filter(Loan.returnDate == date.today())
    elif loan_filter == 'week':
        end_of_week = date.today() + timedelta(days=7 - date.today().weekday())
        loans_query = loans_query.filter(Loan.returnDate >= date.today(), Loan.returnDate <= end_of_week)
    elif loan_filter == 'overdue':
        loans_query = loans_query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE)
    
    loans_pagination = loans_query.order_by(Loan.returnDate.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # Últimos empréstimos (para exibir quantidade retirada em cada empréstimo)
    recent_books_page = request.args.get('recent_books_page', 1, type=int)
    recent_books_per_page = int(request.args.get('recent_books_per_page', 10))
    recent_loans_query = Loan.query.order_by(Loan.loanDate.desc(), Loan.loanId.desc())

    recent_loans_pagination = recent_loans_query.paginate(page=recent_books_page, per_page=recent_books_per_page, error_out=False)

    recent_books_info = []
    for loan in recent_loans_pagination.items:
        if loan.book:
            recent_books_info.append({'book': loan.book, 'amount': loan.amount})

    # Distribuição de palavras-chave por ocorrências na tabela de relacionamento KeyWordBooks
    keyword_rows = db.session.query(
        KeyWord.word,
        func.count(KeyWordBook.wordId).label('usage_count')
    ).join(
        KeyWordBook, KeyWord.wordId == KeyWordBook.wordId
    ).group_by(
        KeyWord.wordId, KeyWord.word
    ).order_by(
        func.count(KeyWordBook.wordId).desc(), KeyWord.word.asc()
    ).all()

    keyword_top10 = [
        {
            'word': row.word,
            'count': row.usage_count,
        }
        for row in keyword_rows[:10]
    ]

    return render_template('dashboard.html',
                           total_books=total_books,
                           total_loans_active=total_loans_active,
                           total_students=total_students,
                           total_staff=total_staff,
                           overdue_loans_count=overdue_loans_count,
                           loans=loans_pagination,
                           loan_filter=loan_filter,
                           recent_books=recent_books_info,
                           recent_books_pagination=recent_loans_pagination,
                           keyword_top10=keyword_top10)


@bp.route('/menu')
@login_required
def menu():
    return render_template('menu.html')


@bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('main.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usernameStr = form.username.data.strip().lower()
        # Agora o login utiliza o identificationCode no lugar de username
        user = User.query.filter_by(identificationCode=usernameStr).first()
        valid_password = False
        if user:
            try:
                valid_password = bcrypt.check_password_hash(user.password, form.password.data)
            except ValueError:
                # Se a senha no banco não estiver hasheada (ex.: em testes), faz comparação direta
                valid_password = (user.password == form.password.data)
        if user and valid_password:
            session['logged_in'] = True
            session['username'] = usernameStr
            session['userId'] = user.userId
            session['userType'] = user.userType
            login_user(user)
            if user.userType == 'admin':
                return redirect(url_for('main.dashboard'))
            return redirect(url_for('main.index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    # Dynamically set choices for userType
    if isinstance(current_user, AnonymousUserMixin) or not current_user.is_authenticated:
        # Not logged in
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante')]
    elif current_user.userType == 'admin':
        # Logged in as admin
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante'), ('staff', 'Funcionário'), ('admin', 'Administrador')]
    else:
        # Logged in as non-admin (e.g., staff)
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante'), ('staff', 'Funcionário')]

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Determine createdBy and updatedBy
        creator_id = 1  # Default to system admin or a predefined ID
        if current_user.is_authenticated:
            creator_id = current_user.userId

        new_user = User(
            identificationCode=form.username.data.strip().lower(),
            userCompleteName=form.username.data.strip(),
            password=hashed_password,
            userType=form.userType.data,
            userPhone=form.userPhone.data,
            birthDate=form.birthDate.data,
            cpf=form.cpf.data,
            rg=form.rg.data,
            gradeNumber=form.gradeNumber.data,
            className=form.className.data,
            guardianName1=form.guardianName1.data,
            guardianPhone1=form.guardianPhone1.data,
            guardianName2=form.guardianName2.data,
            guardianPhone2=form.guardianPhone2.data,
            notes=form.notes.data,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=creator_id,
            updatedBy=creator_id
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuário registrado com sucesso!', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


# Book Management Routes
@bp.route('/livros')
@login_required
def livros():
    query = Book.query
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(
            or_(
                Book.bookName.ilike(f'%{search_term}%'),
                Book.authorName.ilike(f'%{search_term}%')
            )
        )

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    books_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('livros.html', books=books_pagination, search_term=search_term, per_page=per_page)


@bp.route('/livros/form', defaults={'book_id': None}, methods=['GET'])
@bp.route('/livros/form/<int:book_id>', methods=['GET'])
@login_required
def get_book_form(book_id):
    if book_id:
        book = Book.query.get_or_404(book_id)
        form = BookForm(obj=book)
        form.keyWords.data = '; '.join([kw.word for kw in book.keywords])
    else:
        form = BookForm()
    return render_template('_book_form.html', form=form, book_id=book_id)


@bp.route('/livros/new', methods=['POST'])
@login_required
def novo_livro():
    form = BookForm()
    if form.validate_on_submit():
        new_book = Book(
            bookName=(form.bookName.data or '').strip(),
            amount=form.amount.data,
            authorName=(form.authorName.data or '').strip() if form.authorName.data else None,
            publisherName=(form.publisherName.data or '').strip() if form.publisherName.data else None,
            publishedDate=form.publishedDate.data,
            acquisitionDate=form.acquisitionDate.data,
            description=(form.description.data or '').strip() if form.description.data else None,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        db.session.add(new_book)
        db.session.commit()
        
        keywords_list = splitStringIntoList(form.keyWords.data)
        for keyword_str in keywords_list:
            keyword_obj = KeyWord.query.filter_by(word=keyword_str).first()
            if not keyword_obj:
                keyword_obj = KeyWord(word=keyword_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                db.session.add(keyword_obj)
            new_book.keywords.append(keyword_obj)
        db.session.commit()

        flash('Livro cadastrado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/livros/edit/<int:book_id>', methods=['POST'])
@login_required
def editar_livro(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(request.form)
    if form.validate():
        form.populate_obj(book)
        
        new_keywords_str = set(splitStringIntoList(form.keyWords.data))
        old_keywords_str = {kw.word for kw in book.keywords}
        
        for keyword_obj in list(book.keywords):
            if keyword_obj.word not in new_keywords_str:
                book.keywords.remove(keyword_obj)
        
        for keyword_str in new_keywords_str:
            if keyword_str not in old_keywords_str:
                keyword_obj = KeyWord.query.filter_by(word=keyword_str).first()
                if not keyword_obj:
                    keyword_obj = KeyWord(word=keyword_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                    db.session.add(keyword_obj)
                book.keywords.append(keyword_obj)

        book.lastUpdate = date.today()
        book.updatedBy = current_user.userId
        db.session.commit()
        flash('Livro atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


# Loan Management Routes
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
    
    return render_template('emprestimos.html', loans=loans_pagination, search_term=search_term, per_page=per_page)

@bp.route('/emprestimos/form', defaults={'loan_id': None}, methods=['GET'])
@bp.route('/emprestimos/form/<int:loan_id>', methods=['GET'])
@login_required
def get_loan_form(loan_id):
    if loan_id:
        loan = Loan.query.get_or_404(loan_id)
        form = LoanForm(obj=loan)
        user = loan.user
        book = loan.book

        loan_user_info = {
            'identificationCode': getattr(user, 'identificationCode', None) or '—',
            'name': getattr(user, 'userCompleteName', None) or getattr(user, 'username', None) or '—',
            'age': _calc_age(getattr(user, 'birthDate', None)) if user else None,
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
            creationDate=date.today(),
            lastUpdate=date.today(),
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
    informed_return_date = _parse_date(raw_return_date)

    if not informed_return_date:
        return jsonify({'success': False, 'errors': {'returnDate': ['Informe uma data de devolução válida no formato YYYY-MM-DD.']}})

    if informed_return_date < loan.loanDate:
        return jsonify({'success': False, 'errors': {'returnDate': ['A data de devolução não pode ser anterior à data de empréstimo.']}})

    # Regras de imutabilidade na edição:
    # não permitir alterar livro, usuário, quantidade e data de início.
    # apenas a data de devolução pode ser atualizada por esta rota.
    loan.returnDate = informed_return_date
    loan.lastUpdate = date.today()
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

    allowed = {'COMPLETED', 'LOST'}
    if raw_status not in allowed:
        return jsonify({
            'success': False,
            'errors': {'status': ['Status inválido. Use LOST ou COMPLETED.']}
        }), 400

    informed_return_date = _parse_date(raw_return_date)
    if not informed_return_date:
        return jsonify({
            'success': False,
            'errors': {'returnDate': ['Informe uma data de devolução válida no formato YYYY-MM-DD.']}
        }), 400

    if informed_return_date < loan.loanDate:
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
        loan.book.lastUpdate = date.today()
        loan.book.updatedBy = current_user.userId

    loan.returnDate = informed_return_date
    loan.status = StatusLoan[raw_status]
    loan.lastUpdate = date.today()
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
@bp.route('/palavras_chave')
@login_required
def palavras_chave():
    query = KeyWord.query
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(KeyWord.word.ilike(f'%{search_term}%'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    keywords_pagination = query.order_by(KeyWord.word.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('palavras_chave.html', keywords=keywords_pagination, search_term=search_term, per_page=per_page)


@bp.route('/palavras_chave/form', defaults={'keyword_id': None}, methods=['GET'])
@bp.route('/palavras_chave/form/<int:keyword_id>', methods=['GET'])
@login_required
def get_keyword_form(keyword_id):
    if keyword_id:
        keyword = KeyWord.query.get_or_404(keyword_id)
        form = KeyWordForm(obj=keyword)
    else:
        form = KeyWordForm()
    return render_template('_keyword_form.html', form=form, keyword_id=keyword_id)


@bp.route('/palavras_chave/new', methods=['POST'])
@login_required
def nova_palavra_chave():
    form = KeyWordForm()
    if form.validate_on_submit():
        raw = form.word.data or ''
        # split por vírgula ou ponto e vírgula
        parts = []
        seen = set()
        for token in raw.replace(';', ',').split(','):
            normalized = _normalize_tag(token)
            if normalized and normalized not in seen:
                parts.append(normalized)
                seen.add(normalized)

        if not parts:
            return jsonify({'success': False, 'errors': {'word': ['Informe ao menos uma tag válida.']}})

        # buscar existentes
        existing = {kw.word for kw in KeyWord.query.filter(KeyWord.word.in_(parts)).all()}
        to_create = [p for p in parts if p not in existing]

        created = 0
        for w in to_create:
            kw = KeyWord(
                word=w,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=current_user.userId,
                updatedBy=current_user.userId
            )
            db.session.add(kw)
            created += 1
        if created:
            db.session.commit()
        msg = 'Tags processadas com sucesso.'
        if created and existing:
            msg = f'{created} nova(s) tag(s) criada(s); {len(existing)} já existia(m) e foram ignoradas.'
        elif created and not existing:
            msg = f'{created} nova(s) tag(s) criada(s).'
        elif not created and existing:
            msg = 'Todas as tags já existiam; nada foi criado.'
        flash(msg, 'success')
        return jsonify({'success': True, 'created': created, 'ignored': len(existing)})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/palavras_chave/edit/<int:keyword_id>', methods=['POST'])
@login_required
def editar_palavra_chave(keyword_id):
    keyword = KeyWord.query.get_or_404(keyword_id)
    form = KeyWordForm(request.form)
    if form.validate():
        normalized = _normalize_tag(form.word.data or '')
        if not normalized:
            return jsonify({'success': False, 'errors': {'word': ['Informe uma tag válida.']}})
        # verificar duplicidade com outras tags
        existing = KeyWord.query.filter_by(word=normalized).first()
        if existing and existing.word != keyword.word:
            return jsonify({'success': False, 'errors': {'word': ['Esta tag já existe.']}})

        keyword.word = normalized
        keyword.lastUpdate = date.today()
        keyword.updatedBy = current_user.userId
        db.session.commit()
        flash('Tag atualizada com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/excluir_livro/<int:id>', methods=['POST'])
@login_required
def excluir_livro(id):
    livro = Book.query.get_or_404(id)
    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído com sucesso!', 'success')
    return redirect(url_for('main.livros'))


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
    return redirect(url_for('main.emprestimos'))
    """

@bp.route('/excluir_palavra_chave/<int:id>', methods=['POST'])
@login_required
def excluir_palavra_chave(id):
    palavra_chave = KeyWord.query.get_or_404(id)
    db.session.delete(palavra_chave)
    db.session.commit()
    flash('Palavra-chave excluída com sucesso!', 'success')
    return redirect(url_for('main.palavras_chave'))


# User Management Routes
@bp.route('/users')
@login_required
def list_users():
    query = User.query
    search_term = request.args.get('search')
    if search_term:
        query = query.filter(User.userCompleteName.ilike(f"%{search_term}%"))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('users.html', users=users, search_term=search_term, per_page=per_page)

@bp.route('/users/form', defaults={'user_id': None}, methods=['GET'])
@bp.route('/users/form/<int:user_id>', methods=['GET'])
@login_required
def get_user_form(user_id):
    if user_id:
        user = User.query.get_or_404(user_id)
        form = UserForm(obj=user, mode='edit', instance_id=user.userId)
    else:
        form = UserForm(mode='create')
    return render_template('_user_form.html', form=form, user_id=user_id)

@bp.route('/users/new', methods=['POST'])
@login_required
def new_user():
    form = UserForm(mode='create')
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') if form.password.data else bcrypt.generate_password_hash('123456').decode('utf-8')
        new_user = User(
            identificationCode=form.identificationCode.data.strip(),
            userCompleteName=form.userCompleteName.data.strip(),
            password=hashed_password,
            userType=form.userType.data,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
            userPhone=form.userPhone.data,
            birthDate=form.birthDate.data,
            cpf=form.cpf.data,
            rg=form.rg.data,
            gradeNumber=form.gradeNumber.data,
            className=form.className.data,
            guardianName1=form.guardianName1.data,
            guardianPhone1=form.guardianPhone1.data,
            guardianName2=form.guardianName2.data,
            guardianPhone2=form.guardianPhone2.data,
            notes=form.notes.data,
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})

@bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(request.form, obj=user, mode='edit', instance_id=user.userId)
    if form.validate():
        # manual populate to avoid overwriting id fields
        user.userType = form.userType.data
        user.identificationCode = form.identificationCode.data.strip()
        user.userCompleteName = form.userCompleteName.data.strip()
        user.userPhone = form.userPhone.data
        user.birthDate = form.birthDate.data
        user.cpf = form.cpf.data
        user.rg = form.rg.data
        user.gradeNumber = form.gradeNumber.data
        user.className = form.className.data
        user.guardianName1 = form.guardianName1.data
        user.guardianPhone1 = form.guardianPhone1.data
        user.guardianName2 = form.guardianName2.data
        user.guardianPhone2 = form.guardianPhone2.data
        user.notes = form.notes.data
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.lastUpdate = date.today()
        user.updatedBy = current_user.userId
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})

@bp.route('/users/check-identification', methods=['GET'])
@login_required
def check_identification_code():
    code = (request.args.get('code') or '').strip()
    exists = False
    if code:
        exists = db.session.query(User.userId).filter_by(identificationCode=code).first() is not None
    return jsonify({'exists': exists})

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('main.list_users'))


# JSON APIs para autocomplete no modal de novo empréstimo
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
            'userType': u.userType,
            'age': _calc_age(u.birthDate),
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
    loan_date = _parse_date(request.args.get('loanDate'))
    return_date = _parse_date(request.args.get('returnDate'))
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
        available = _available_copies_for_range(b, loan_date, return_date)
        results.append({
            'bookId': b.bookId,
            'bookName': b.bookName,
            'authorName': b.authorName,
            'publisherName': b.publisherName,
            'publishedDate': b.publishedDate.isoformat() if b.publishedDate else None,
            'amount': b.amount,
            'available': available,
            'keywords': [kw.word for kw in getattr(b, 'keywords', [])]
        })
    return jsonify({'results': results})