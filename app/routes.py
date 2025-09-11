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
from .validaEmprestimo import validaEmprestimo


bp = Blueprint('main', __name__)


def splitStringIntoList(string):
    if not string:
        return []
    string_list = [item.strip().lower() for item in string.split(';') if item.strip()]
    return string_list

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
    total_students = User.query.filter_by(userType='student').count()
    total_staff = User.query.filter(User.userType.in_(['admin', 'staff'])).count()
    overdue_loans_count = Loan.query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE).count()

    # Loan filtering
    loan_filter = request.args.get('filter', 'today')
    page = request.args.get(get_page_parameter(), 1, type=int)
    per_page = int(request.args.get('per_page', 10))
    
    loans_query = Loan.query
    if loan_filter == 'today':
        loans_query = loans_query.filter(Loan.returnDate == date.today())
    elif loan_filter == 'week':
        end_of_week = date.today() + timedelta(days=7 - date.today().weekday())
        loans_query = loans_query.filter(Loan.returnDate >= date.today(), Loan.returnDate <= end_of_week)
    elif loan_filter == 'overdue':
        loans_query = loans_query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE)
    
    loans_pagination = loans_query.order_by(Loan.returnDate.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # Recently loaned books
    recent_books_page = request.args.get('recent_books_page', 1, type=int)
    recent_books_per_page = int(request.args.get('recent_books_per_page', 10))
    recent_loans_query = db.session.query(Loan.bookId, func.max(Loan.loanDate).label('max_loan_date')) \
        .group_by(Loan.bookId) \
        .order_by(func.max(Loan.loanDate).desc())
    
    recent_loans_pagination = recent_loans_query.paginate(page=recent_books_page, per_page=recent_books_per_page, error_out=False)
    
    recent_books_info = []
    for loan_info in recent_loans_pagination.items:
        book = Book.query.get(loan_info.bookId)
        if book:
            active_loans_count = db.session.query(func.sum(Loan.amount)).filter_by(bookId=book.bookId, status=StatusLoan.ACTIVE).scalar() or 0
            available_amount = book.amount - active_loans_count
            recent_books_info.append({'book': book, 'available': available_amount})

    return render_template('dashboard.html',
                           total_books=total_books,
                           total_loans_active=total_loans_active,
                           total_students=total_students,
                           total_staff=total_staff,
                           overdue_loans_count=overdue_loans_count,
                           loans=loans_pagination,
                           loan_filter=loan_filter,
                           recent_books=recent_books_info,
                           recent_books_pagination=recent_loans_pagination)


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
        user = User.query.filter_by(username=usernameStr).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
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
            username=form.username.data.strip().lower(),
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

    return render_template('main/register.html', form=form)


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
            bookName=form.bookName.data.lower().strip(),
            amount=form.amount.data,
            authorName=form.authorName.data.lower().strip(),
            publisherName=form.publisherName.data.lower().strip(),
            publishedDate=form.publishedDate.data,
            acquisitionDate=form.acquisitionDate.data,
            description=form.description.data.lower().strip(),
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
    search_term = request.args.get('search', '')
    if search_term:
        query = query.join(User).join(Book).filter(
            or_(
                User.username.ilike(f'%{search_term}%'),
                Book.bookName.ilike(f'%{search_term}%')
            )
        )

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
    else:
        form = LoanForm()
    return render_template('_loan_form.html', form=form, loan_id=loan_id)

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
    form = LoanForm(request.form)
    if form.validate():
        form.populate_obj(loan)
        loan.lastUpdate = date.today()
        loan.updatedBy = current_user.userId
        db.session.commit()
        flash('Empréstimo atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


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
        new_keyword = KeyWord(
            word=form.word.data.strip().lower(),
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId
        )
        db.session.add(new_keyword)
        db.session.commit()
        flash('Tag cadastrada com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/palavras_chave/edit/<int:keyword_id>', methods=['POST'])
@login_required
def editar_palavra_chave(keyword_id):
    keyword = KeyWord.query.get_or_404(keyword_id)
    form = KeyWordForm(request.form)
    if form.validate():
        form.populate_obj(keyword)
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
    emprestimo = Loan.query.get_or_404(id)
    db.session.delete(emprestimo)
    db.session.commit()
    flash('Empréstimo excluído com sucesso!', 'success')
    return redirect(url_for('main.emprestimos'))


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
        query = query.filter(User.username.ilike(f'%{search_term}%'))

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
        form = UserForm(obj=user)
    else:
        form = UserForm()
    return render_template('_user_form.html', form=form, user_id=user_id)

@bp.route('/users/new', methods=['POST'])
@login_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            userType=form.userType.data,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
            # ... add all other fields from form
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
    form = UserForm(request.form, obj=user)
    if form.validate():
        form.populate_obj(user)
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.lastUpdate = date.today()
        user.updatedBy = current_user.userId
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('main.list_users'))