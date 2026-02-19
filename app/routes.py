from datetime import date, timedelta, datetime, timezone
import json
from flask import flash, redirect, render_template, request, session, url_for, jsonify, current_app
from flask_login import current_user, login_required, login_user, logout_user, AnonymousUserMixin
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from flask import Blueprint

from . import bcrypt, db
from .dbExecute import addFromForm
from .forms import (BookForm, KeyWordForm, LoanForm, LoginForm, RegisterForm,
                    SearchBooksForm, UserForm, SearchLoansForm, ConfigForm)


from .models import Book, KeyWord, KeyWordBook, Loan, StatusLoan, User, Configuration, ConfigSpec, AuditLog, UserSession
from .audit import log_manual_event
from .validaEmprestimo import validaEmprestimo
from .utils import normalize_tag, splitStringIntoList
from uuid import uuid4 # Para gerar o session_id

bp = Blueprint('main', __name__)


@bp.before_app_request
def check_session_timeout():
    if current_user.is_authenticated:
        session.permanent = False  # Garante que o cookie expira ao fechar o navegador
        now = datetime.now(timezone.utc)
        
        # 1. Validação de Sessão no Banco (Server-Side)
        # Se existir um token na sessão, verifica se ele é válido no banco
        current_session_token = session.get('session_token')
        if current_session_token:
            user_session = UserSession.query.filter_by(session_id=current_session_token).first()
            
            # Se a sessão não existe no banco (foi revogada), desloga
            if not user_session:
                logout_user()
                session.clear()
                flash('Sua sessão foi encerrada remotamente.', 'warning')
                return redirect(url_for('main.login'))
            
            # 2. Verificação de Inatividade (Híbrido)
            # Busca configuração de inatividade do banco
            config_inactivity = Configuration.query.filter_by(key='SESSION_INACTIVITY_MINUTES').first()
            inactivity_minutes = int(config_inactivity.value) if (config_inactivity and config_inactivity.value.isdigit()) else 60
            
            # Se user_session.last_activity for naive, assume UTC ou converte. 
            # O modelo define default=datetime.now, que pode ser naive dependendo do sistema.
            # Vamos garantir comparação segura.
            last_activity = user_session.last_activity
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            
            if now - last_activity > timedelta(minutes=inactivity_minutes):
                # Remove sessão do banco
                db.session.delete(user_session)
                db.session.commit()
                
                logout_user()
                session.clear()
                flash('Sua sessão expirou por inatividade.', 'warning')
                return redirect(url_for('main.login'))
            
            # Atualiza last_activity
            user_session.last_activity = now
            db.session.commit()

        # 3. Verificação de Tempo Absoluto (12h - Fallback/Legacy)
        start_time_str = session.get('session_start')
        if start_time_str:
            try:
                # Converte string ISO de volta para datetime com timezone
                start_time = datetime.fromisoformat(start_time_str)
                
                # Busca configuração do banco de dados
                config_db = Configuration.query.filter_by(key='SESSION_LIFETIME_HOURS').first()
                if config_db and config_db.value.isdigit():
                    limit_hours = int(config_db.value)
                else:
                    # Fallback para o valor do config.py ou 12h
                    limit_config = current_app.config.get('PERMANENT_SESSION_LIFETIME')
                    limit_hours = limit_config.total_seconds() / 3600 if limit_config else 12

                limit = timedelta(hours=limit_hours)

                if now - start_time > limit:
                    # Tenta limpar do banco também
                    if current_session_token:
                         UserSession.query.filter_by(session_id=current_session_token).delete()
                         db.session.commit()

                    logout_user()
                    session.clear()
                    flash('Sua sessão expirou (limite de tempo total). Por favor, faça login novamente.', 'warning')
                    return redirect(url_for('main.login'))
            except (ValueError, TypeError):
                logout_user()
                session.clear()
                return redirect(url_for('main.login'))



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

def _get_config_bool(key: str) -> bool:
    config_entry = Configuration.query.filter_by(key=key).first()
    if not config_entry or config_entry.value is None:
        return False
    return str(config_entry.value).strip() == '1'

def _is_admin_user() -> bool:
    return bool(getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'userType', None) == 'admin')

def _parse_allowed_values(raw: str):
    return [item.strip() for item in (raw or '').split(',') if item.strip()]

def _normalize_boolean_string(raw_value: str):
    normalized = (raw_value or '').strip().lower()
    if normalized in ('1', 'true', 'sim', 'yes'):
        return '1'
    if normalized in ('0', 'false', 'nao', 'não', 'no'):
        return '0'
    return None

def _validate_config_value(raw_value: str, spec: ConfigSpec):
    value = (raw_value or '').strip()
    if spec.required and not value:
        return False, None, 'Este valor é obrigatório.'
    if not value:
        return True, '', None

    if spec.valueType == 'boolean':
        bool_value = _normalize_boolean_string(value)
        if bool_value is None:
            return False, None, 'Valor inválido. Para booleano, use 0 ou 1.'
        return True, bool_value, None

    if spec.valueType == 'integer':
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            return False, None, 'Valor inválido. Informe um número inteiro.'

        if spec.minValue is not None and int_value < spec.minValue:
            return False, None, f'Valor deve ser maior ou igual a {spec.minValue}.'
        if spec.maxValue is not None and int_value > spec.maxValue:
            return False, None, f'Valor deve ser menor ou igual a {spec.maxValue}.'
        return True, str(int_value), None

    if spec.valueType == 'enum':
        allowed = _parse_allowed_values(spec.allowedValues)
        if not allowed:
            return False, None, 'A configuração enum não possui opções válidas definidas.'
        if value not in allowed:
            return False, None, f'Valor inválido. Opções permitidas: {", ".join(allowed)}.'
        return True, value, None

    return True, value, None

def _build_or_update_spec_from_form(form: ConfigForm, existing_spec: ConfigSpec | None = None):
    spec = existing_spec or ConfigSpec()
    spec.key = form.key.data
    spec.valueType = form.valueType.data
    spec.allowedValues = (form.allowedValues.data or '').strip() or None
    spec.minValue = form.minValue.data if form.valueType.data == 'integer' else None
    spec.maxValue = form.maxValue.data if form.valueType.data == 'integer' else None
    spec.required = bool(form.required.data)
    spec.defaultValue = (form.defaultValue.data or '').strip() or None
    spec.description = (form.specDescription.data or '').strip() or None
    return spec

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
    try:
        log_manual_event('LOGOUT', 'User', current_user.userId)
    except Exception:
        pass
        
    # Remove sessão do servidor se existir
    session_token = session.get('session_token')
    if session_token:
        try:
            db.session.query(UserSession).filter_by(session_id=session_token).delete()
            db.session.commit()
        except:
            pass

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
            # Generate Session Token
            token_str = str(uuid4())
            
            session['logged_in'] = True
            session['username'] = usernameStr
            session['userId'] = user.userId
            session['userType'] = user.userType
            session['session_start'] = datetime.now(timezone.utc).isoformat()
            session['session_token'] = token_str

            login_user(user)

            # Grava no banco
            try:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr) # Use a separate variable
                user_agent = request.headers.get('User-Agent')
                new_session = UserSession(
                    user_id=user.userId,
                    session_id=token_str,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(timezone.utc),
                    last_activity=datetime.now(timezone.utc)
                )
                db.session.add(new_session)
                db.session.commit()

                log_manual_event('LOGIN', 'User', user.userId, changes={'username': usernameStr})
            except Exception:
                pass
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
        
        # Processar keywords com normalize_tag
        raw_keywords = splitStringIntoList(form.keyWords.data)
        # normalize_tag retorna string vazia se inválido
        keywords_list = [normalized for k in raw_keywords if (normalized := normalize_tag(k))]
        
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
        has_changes = False
        
        # 1. Verificar campos simples
        # Obs: campos como bookName, authorName etc
        for field in form:
            if field.name in ['csrf_token', 'keyWords']: continue
            if not hasattr(book, field.name): continue
            
            old_val = getattr(book, field.name)
            new_val = field.data
            
            # Normalizar None e String Vazia
            if isinstance(old_val, str) and new_val is None: new_val = ''
            if old_val is None and isinstance(new_val, str): old_val = ''
            
            if old_val != new_val:
                has_changes = True
                break
        
        # 2. Verificar keywords
        current_keywords = {kw.word for kw in book.keywords}
        
        raw_keywords = splitStringIntoList(form.keyWords.data)
        # normalize_tag retorna string vazia se inválido
        new_keywords = {normalized for k in raw_keywords if (normalized := normalize_tag(k))}
        
        if current_keywords != new_keywords:
            has_changes = True
            
        if not has_changes:
            # Se nada mudou, retorna sucesso sem tocar no banco
            return jsonify({'success': True, 'message': 'Nenhuma alteração detectada.'})

        form.populate_obj(book)
        
        new_keywords_str = new_keywords
        old_keywords_str = current_keywords
        
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
            can_edit_initial_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_ATIVO')
        elif is_finalized_loan:
            can_edit_initial_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_FINALIZADO')
            can_edit_final_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_FINAL_EMPRESTIMO_FINALIZADO')

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
    informed_return_date = _parse_date(raw_return_date)

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
        can_edit_initial_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_ATIVO')
    elif is_finalized_loan:
        can_edit_initial_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_FINALIZADO')
        can_edit_final_note = _get_config_bool('PERMITE_ALTERAR_OBSERVACAO_FINAL_EMPRESTIMO_FINALIZADO')

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

    informed_return_date = _parse_date(raw_return_date)
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
            normalized = normalize_tag(token)
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
        normalized = normalize_tag(form.word.data or '')
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


# Configuration Management Routes
@bp.route('/configuracoes')
@login_required
def configuracoes():
    if not _is_admin_user():
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('main.menu'))

    query = Configuration.query
    search_term = (request.args.get('search') or '').strip()
    if search_term:
        query = query.filter(
            or_(
                Configuration.key.ilike(f'%{search_term}%'),
                Configuration.description.ilike(f'%{search_term}%')
            )
        )

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    configs = query.order_by(Configuration.key.asc(), Configuration.configId.asc()).paginate(page=page, per_page=per_page, error_out=False)

    keys = [cfg.key for cfg in configs.items if cfg.key]
    specs_by_key = {}
    if keys:
        specs = ConfigSpec.query.filter(ConfigSpec.key.in_(keys)).all()
        specs_by_key = {spec.key: spec for spec in specs}

    return render_template('configuracoes.html', configs=configs, search_term=search_term, per_page=per_page, specs_by_key=specs_by_key)


@bp.route('/configuracoes/form', defaults={'config_id': None}, methods=['GET'])
@bp.route('/configuracoes/form/<int:config_id>', methods=['GET'])
@login_required
def get_config_form(config_id):
    if not _is_admin_user():
        return '<p class="text-danger">Acesso negado.</p>', 403

    if config_id:
        config = Configuration.query.get_or_404(config_id)
        form = ConfigForm(obj=config)
        spec = ConfigSpec.query.filter_by(key=config.key).first()
        if spec:
            form.valueType.data = spec.valueType
            form.allowedValues.data = spec.allowedValues
            form.minValue.data = spec.minValue
            form.maxValue.data = spec.maxValue
            form.required.data = spec.required
            form.defaultValue.data = spec.defaultValue
            form.specDescription.data = spec.description
    else:
        config = None
        form = ConfigForm()
        form.valueType.data = 'string'

    return render_template('_config_form.html', form=form, config=config, config_id=config_id)


@bp.route('/configuracoes/new', methods=['POST'])
@login_required
def nova_configuracao():
    if not _is_admin_user():
        return jsonify({'success': False, 'errors': {'auth': ['Acesso negado.']}}), 403

    form = ConfigForm()
    if not form.validate_on_submit():
        return jsonify({'success': False, 'errors': form.errors})

    existing = Configuration.query.filter_by(key=form.key.data).first()
    if existing:
        return jsonify({'success': False, 'errors': {'key': ['Esta chave já existe. Edite o registro existente.']}})

    spec = _build_or_update_spec_from_form(form)
    ok, normalized_value, error_msg = _validate_config_value(form.value.data, spec)
    if not ok:
        return jsonify({'success': False, 'errors': {'value': [error_msg]}})

    spec.createdBy = current_user.userId
    spec.updatedBy = current_user.userId
    spec.creationDate = datetime.now()
    spec.lastUpdate = datetime.now()

    new_config = Configuration(
        key=form.key.data,
        value=normalized_value,
        description=(form.description.data or '').strip() or None,
        creationDate=datetime.now(),
        lastUpdate=datetime.now(),
        createdBy=current_user.userId,
        updatedBy=current_user.userId,
    )
    db.session.add(spec)
    db.session.add(new_config)
    db.session.commit()
    flash('Configuração criada com sucesso!', 'success')
    return jsonify({'success': True})


@bp.route('/configuracoes/edit/<int:config_id>', methods=['POST'])
@login_required
def editar_configuracao(config_id):
    if not _is_admin_user():
        return jsonify({'success': False, 'errors': {'auth': ['Acesso negado.']}}), 403

    config = Configuration.query.get_or_404(config_id)
    form = ConfigForm(request.form)
    if not form.validate():
        return jsonify({'success': False, 'errors': form.errors})

    if form.key.data != config.key:
        return jsonify({'success': False, 'errors': {'key': ['A chave não pode ser alterada na edição.']}})

    spec = ConfigSpec.query.filter_by(key=config.key).first()
    spec = _build_or_update_spec_from_form(form, spec)
    ok, normalized_value, error_msg = _validate_config_value(form.value.data, spec)
    if not ok:
        return jsonify({'success': False, 'errors': {'value': [error_msg]}})

    if not spec.configSpecId:
        spec.createdBy = current_user.userId
        spec.creationDate = datetime.now()
        db.session.add(spec)

    spec.updatedBy = current_user.userId
    spec.lastUpdate = datetime.now()

    config.value = normalized_value
    config.description = (form.description.data or '').strip() or None
    config.lastUpdate = datetime.now()
    config.updatedBy = current_user.userId
    db.session.commit()
    flash('Configuração atualizada com sucesso!', 'success')
    return jsonify({'success': True})





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

@bp.route('/audit_logs')
@login_required
def audit_logs():
    if not _is_admin_user():
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.index'))

    # Pagination
    try:
        page = request.args.get('page', 1, type=int)
    except ValueError:
        page = 1
    per_page = 20

    # Filter params
    action_filter = request.args.get('action', '').strip()
    target_type_filter = request.args.get('target_type', '').strip()
    user_id_filter = request.args.get('user_id', '').strip()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    query = AuditLog.query.options(joinedload(AuditLog.user))

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))
    
    if target_type_filter:
        query = query.filter(AuditLog.target_type.ilike(f"%{target_type_filter}%"))

    if user_id_filter:
        try:
            uid = int(user_id_filter)
            query = query.filter(AuditLog.user_id == uid)
        except ValueError:
             # Se for string (nome), tenta buscar pelo ID
             user_obj = User.query.filter(User.identificationCode.ilike(f"%{user_id_filter}%")).first()
             if user_obj:
                 query = query.filter(AuditLog.user_id == user_obj.userId)
             else:
                 query = query.filter(AuditLog.user_id == -1) # força vazio

    if start_date_str:
        try:
             start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
             query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
             pass

    if end_date_str:
        try:
             end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
             # Ajusta para final do dia
             end_dt = end_dt.replace(hour=23, minute=59, second=59)
             query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
             pass

    query = query.order_by(AuditLog.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items

    return render_template('audit_logs.html', logs=logs, pagination=pagination)


@bp.route('/admin/sessions')
@login_required
def manage_sessions():
    if current_user.userType != 'admin':
        flash('Acesso negado. Apenas administradores podem ver as sessões.', 'danger')
        return redirect(url_for('main.index'))
        
    sessions = UserSession.query.order_by(UserSession.last_activity.desc()).all()
    current_token = session.get('session_token')
    
    return render_template('admin_sessions.html', sessions=sessions, current_session_token=current_token)

@bp.route('/admin/sessions/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    if current_user.userType != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
        
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    if user_session:
        db.session.delete(user_session)
        db.session.commit()
        flash('Sessão encerrada com sucesso.', 'success')
    else:
        flash('Sessão não encontrada.', 'warning')
        
    return redirect(url_for('main.manage_sessions'))


    if start_date_str:
        start_date = _parse_date(start_date_str)
        if start_date:
            # Combine date with min time
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(AuditLog.timestamp >= start_dt)
    
    if end_date_str:
        end_date = _parse_date(end_date_str)
        if end_date:
            # Combine date with max time to include the whole day
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(AuditLog.timestamp <= end_dt)

    # Order by timestamp desc
    query = query.order_by(AuditLog.timestamp.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items

    # Pre-process logs to parse JSON changes if needed, or pass helper
    # We can do it in the template using a custom filter or just simple json.loads if available
    # But let's attach a parsed property or just handle strings in template
    
    return render_template(
        'audit_logs.html',
        logs=logs,
        pagination=pagination,
        action_filter=action_filter,
        target_type_filter=target_type_filter,
        user_id_filter=user_id_filter,
        start_date=start_date_str,
        end_date=end_date_str
    )
