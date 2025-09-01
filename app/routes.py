# from time import strftime
from datetime import date, timedelta

from flask import flash, redirect, render_template, request, session, url_for, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import func
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
    # Redirect admin users to the dashboard, others to the menu.
    if current_user.userType == 'admin':
        return redirect(url_for('dashboard'))
    return redirect(url_for('menu'))


@bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure only admin users can access the dashboard
    if current_user.userType != 'admin':
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('menu'))

    # KPIs
    total_books = db.session.query(func.sum(Book.amount)).scalar() or 0
    total_loans_active = Loan.query.filter_by(status=StatusLoan.ACTIVE).count()
    total_students = User.query.filter_by(userType='student').count() # Assuming 'student' type
    total_staff = User.query.filter(User.userType.in_(['admin', 'staff'])).count() # Assuming types
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
    # 'all' filter doesn't need a specific filter

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
    # This can be a page for non-admin users or a fallback.
    return render_template('menu.html')


@bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    print("--- 1. Acessando a rota /login ---")
    form = LoginForm()
    
    if form.validate_on_submit():
        print("--- 2. Formulário validado ---")
        usernameStr = form.username.data.strip().lower()
        print(f"--- 3. Tentando encontrar o usuário: {usernameStr} ---")
        user = User.query.filter_by(username=usernameStr).first()
        print(f"--- Query executada para o usuário: {usernameStr} ---")

        if user:
            print(f"--- 4. Usuário '{usernameStr}' encontrado no banco de dados. ---")
            print("--- 5. Verificando a senha... ---")
            if bcrypt.check_password_hash(user.password, form.password.data):
                print("--- 6. Senha correta. ---")
                session['logged_in'] = True
                session['username'] = usernameStr
                session['userId'] = user.userId
                session['userType'] = user.userType
                login_user(user)
                print(f"--- 7. Usuário logado. Tipo: {user.userType}. Redirecionando... ---")
                
                if user.userType == 'admin':
                    print("--- 8a. Redirecionando para /dashboard ---")
                    return redirect(url_for('main.dashboard'))
                
                print("--- 8b. Redirecionando para /index ---")
                return redirect(url_for('index'))
            else:
                print("--- 6. Senha incorreta. ---")
                flash('Usuário ou senha inválidos', 'danger')
        else:
            print(f"--- 4. Usuário '{usernameStr}' NÃO encontrado. ---")
            flash('Usuário ou senha inválidos', 'danger')
    
    elif request.method == 'POST':
        print("--- 2. Formulário inválido. Erros:", form.errors)

    print("--- Renderizando o template de login. ---")
    return render_template('login.html', form=form)


# ... (rest of the routes remain the same)
@bp.route('/livros', methods=['GET', 'POST'])
@login_required
def livros():
    form = SearchBooksForm()
    page = request.args.get(get_page_parameter(), 1, type=int)
    query = Book.query

    if form.validate():
        if form.bookId.data:
            query = query.filter(Book.bookId == form.bookId.data)
        if form.bookName.data:
            query = query.filter(Book.bookName.ilike(f"%{form.bookName.data}%"))
        # Add other filters as needed

    per_page = 10
    livros_paginados = query.paginate(page=page, per_page=per_page, error_out=False)

    livrosDisponiveis = []
    for livro in livros_paginados.items:
        emprestimosAtivos = Loan.query.filter_by(bookId=livro.bookId, status=StatusLoan.ACTIVE).all()
        quantidadeEmprestada = sum(emprestimo.amount for emprestimo in emprestimosAtivos)
        quantidadeDisponivel = livro.amount - quantidadeEmprestada
        livrosDisponiveis.append((livro, quantidadeDisponivel))

    pagination = Pagination(page=page, total=livros_paginados.total, per_page=per_page, css_framework='bootstrap4')
    return render_template('livros.html', form=form, livros=livrosDisponiveis, pagination=pagination)


@bp.route('/emprestimos', methods=['GET', 'POST'])
@login_required
def emprestimos():
    form = SearchLoansForm()
    page = request.args.get(get_page_parameter(), 1, type=int)
    query = Loan.query

    if form.validate():
        if form.loanId.data:
            query = query.filter(Loan.loanId == form.loanId.data)
        # Add other filters as needed

    per_page = 10
    emprestimosPaginados = query.paginate(page=page, per_page=per_page, error_out=False)
    pagination = Pagination(page=page, total=emprestimosPaginados.total, per_page=per_page, css_framework='bootstrap4')
    return render_template('emprestimos.html', form=form, loans=emprestimosPaginados, pagination=pagination)


@bp.route('/palavras_chave')
@login_required
def palavras_chave():
    palavras_chave = KeyWord.query.all()
    return render_template('palavras_chave.html', palavras_chave=palavras_chave)


@bp.route('/novo_livro', methods=['GET', 'POST'])
@login_required
def novo_livro():
    form = BookForm()
    if form.validate_on_submit():
        newBook = Book(
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
        db.session.add(newBook)
        db.session.commit()
        
        # Handle keywords
        keyWordsList = splitStringIntoList(form.keyWords.data)
        for keyWord_str in keyWordsList:
            keyWord_obj = KeyWord.query.filter_by(word=keyWord_str).first()
            if not keyWord_obj:
                keyWord_obj = KeyWord(word=keyWord_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                db.session.add(keyWord_obj)
                db.session.commit()
            newBook.keywords.append(keyWord_obj)
        db.session.commit()

        flash('Livro cadastrado com sucesso!', 'success')
        return redirect(url_for('novo_livro'))
    return render_template('novo_livro.html', form=form)


@bp.route('/novo_emprestimo', methods=['GET', 'POST'])
@login_required
def novo_emprestimo():
    form = LoanForm()
    if form.validate_on_submit():
        if validaEmprestimo(form, Loan, Book, StatusLoan):
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
            return redirect(url_for('novo_emprestimo'))
        else:
            flash('Erro ao cadastrar empréstimo: A validação falhou.', 'danger')
    return render_template('novo_emprestimo.html', form=form)


@bp.route('/nova_palavra_chave', methods=['GET', 'POST'])
@login_required
def nova_palavra_chave():
    form = KeyWordForm()
    if form.validate_on_submit():
        wordStr = form.word.data.strip().lower()
        newKeyWord = KeyWord(
            word=wordStr,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        db.session.add(newKeyWord)
        db.session.commit()
        flash('Palavra-chave cadastrada com sucesso!', 'success')
        return redirect(url_for('nova_palavra_chave'))
    return render_template('nova_palavra_chave.html', form=form)


@bp.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_livro(id):
    livro = Book.query.get_or_404(id)
    form = BookForm(obj=livro)
    
    if request.method == 'GET':
        # READ: Load existing keywords into the form field
        form.keyWords.data = '; '.join([keyword.word for keyword in livro.keywords])

    if form.validate_on_submit():
        # UPDATE/DELETE: Process keywords
        form.populate_obj(livro)
        
        # Get new and old keywords
        new_keywords_str = set(splitStringIntoList(form.keyWords.data))
        old_keywords_str = {keyword.word for keyword in livro.keywords}
        
        # Remove keywords that are no longer associated
        for keyword_obj in list(livro.keywords):
            if keyword_obj.word not in new_keywords_str:
                livro.keywords.remove(keyword_obj)
        
        # Add new keywords
        for keyword_str in new_keywords_str:
            if keyword_str not in old_keywords_str:
                keyWord_obj = KeyWord.query.filter_by(word=keyword_str).first()
                if not keyWord_obj:
                    keyWord_obj = KeyWord(word=keyword_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                    db.session.add(keyWord_obj)
                    db.session.commit()
                livro.keywords.append(keyWord_obj)
                
        livro.lastUpdate = date.today()
        livro.updatedBy = current_user.userId
        db.session.commit()
        flash('Livro atualizado com sucesso!', 'success')
        return redirect(url_for('livros'))
        
    return render_template('editar_livro.html', form=form)


@bp.route('/editar_emprestimo/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_emprestimo(id):
    emprestimo = Loan.query.get_or_404(id)
    form = LoanForm(obj=emprestimo)
    if form.validate_on_submit():
        form.populate_obj(emprestimo)
        emprestimo.lastUpdate = date.today()
        emprestimo.updatedBy = current_user.userId
        db.session.commit()
        flash('Empréstimo atualizado com sucesso!', 'success')
        return redirect(url_for('emprestimos'))
    return render_template('editar_emprestimo.html', form=form)


@bp.route('/editar_palavra_chave/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_palavra_chave(id):
    palavra_chave = KeyWord.query.get_or_404(id)
    form = KeyWordForm(obj=palavra_chave)
    if form.validate_on_submit():
        form.populate_obj(palavra_chave)
        palavra_chave.lastUpdate = date.today()
        palavra_chave.updatedBy = current_user.userId
        db.session.commit()
        flash('Palavra-chave atualizada com sucesso!', 'success')
        return redirect(url_for('palavras_chave'))
    return render_template('editar_palavra_chave.html', form=form)


@bp.route('/excluir_livro/<int:id>', methods=['POST'])
@login_required
def excluir_livro(id):
    livro = Book.query.get_or_404(id)
    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído com sucesso!', 'success')
    return redirect(url_for('livros'))


@bp.route('/excluir_emprestimo/<int:id>', methods=['POST'])
@login_required
def excluir_emprestimo(id):
    emprestimo = Loan.query.get_or_404(id)
    db.session.delete(emprestimo)
    db.session.commit()
    flash('Empréstimo excluído com sucesso!', 'success')
    return redirect(url_for('emprestimos'))


@bp.route('/excluir_palavra_chave/<int:id>', methods=['POST'])
@login_required
def excluir_palavra_chave(id):
    palavra_chave = KeyWord.query.get_or_404(id)
    db.session.delete(palavra_chave)
    db.session.commit()
    flash('Palavra-chave excluída com sucesso!', 'success')
    return redirect(url_for('palavras_chave'))


# User Management Routes
@bp.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@bp.route('/users/new', methods=['GET', 'POST'])
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
            notes=form.notes.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('list_users'))
    return render_template('new_user.html', form=form)

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.lastUpdate = date.today()
        user.updatedBy = current_user.userId
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('list_users'))
    return render_template('edit_user.html', form=form, user=user)

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('list_users'))