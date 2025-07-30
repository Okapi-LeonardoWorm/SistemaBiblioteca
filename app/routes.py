# from time import strftime
from datetime import date

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_paginate import Pagination, get_page_parameter

from . import app, bcrypt, db
from .dbExecute import addFromForm
from .forms import (BookForm, KeyWordForm, LoanForm, LoginForm, RegisterForm,
                    SearchBooksForm, StudentForm, SearchLoansForm)
from .models import Book, KeyWord, KeyWordBook, Loan, StatusLoan, Student, User
from .validaEmprestimo import validaEmprestimo


@app.route('/')
@app.route('/index')
@login_required
def index():
    # return render_template('index.html') # Original
    return redirect(url_for('menu')) # Inserida para redirecionar para a página de menu na criação do minimo para uso


@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')


@app.route('/logout')
@login_required
def logout():
    session['logged_in'] = False
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.username.data.strip().lower()

        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')

        new_user = User(
            username=name,
            password=hashed_password,
            userType="regular",
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId
        )
        if new_user:
            if addFromForm(new_user):
                flash('Usuário cadastrado com sucesso!', 'success')
                return redirect(url_for('register'))
            else:
                flash('Erro ao cadastrar usuário!', 'danger')
        # return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usernameStr = form.username.data.strip().lower()
        user = User.query.filter_by(username=usernameStr).first()

        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                session['logged_in'] = True
                session['username'] = usernameStr
                session['userId'] = user.userId
                session['userType'] = user.userType
                login_user(user)
                return redirect(url_for('index'))
            else:
                # Enviar mensagem de erro para o frontEnd
                pass
    else:
        print("Err:>", form.errors)
    return render_template('login.html', form=form)


@app.route('/livros', methods=['GET', 'POST'])
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
        if form.authorName.data:
            query = query.filter(Book.authorName.ilike(f"%{form.authorName.data}%"))
        if form.publisherName.data:
            query = query.filter(Book.publisherName.ilike(f"%{form.publisherName.data}%"))
        if form.publishedDate.data:
            query = query.filter(Book.publishedDate == form.publishedDate.data)
        if form.acquisitionDate.data:
            query = query.filter(Book.acquisitionDate == form.acquisitionDate.data)
        if form.keywords.data:
            query = query.join(Book.keywords).filter(KeyWord.word.ilike(f"%{form.keywords.data}%"))

    per_page = 10
    livros_paginados = query.paginate(page=page, per_page=per_page, error_out=False)

    # Calcular a quantidade de livros disponíveis
    livrosDisponiveis = []
    for livro in livros_paginados.items:
        emprestimosAtivos = Loan.query.filter_by(bookId=livro.bookId, status=StatusLoan.ACTIVE).all()
        quantidadeEmprestada = sum(emprestimo.amount for emprestimo in emprestimosAtivos)
        quantidadeDisponivel = livro.amount - quantidadeEmprestada
        livrosDisponiveis.append((livro, quantidadeDisponivel))
        
        # livro.pulishedDate = livro.publishedDate.strftime('%d/%m/%Y')
        # livro.acquisitionDate = livro.acquisitionDate.strftime('%d/%m/%Y')


    pagination = Pagination(page=page, total=livros_paginados.total, per_page=per_page, css_framework='bootstrap4')

    return render_template('livros.html', form=form, livros=livrosDisponiveis, pagination=pagination)


@app.route('/alunos')
@login_required
def alunos():
    alunos = Student.query.all()
    return render_template('alunos.html', alunos=alunos)


@app.route('/emprestimos', methods=['GET', 'POST'])
@login_required
def emprestimos():
    form = SearchLoansForm()
    page = request.args.get(get_page_parameter(), 1, type=int)
    
    query = Loan.query

    if form.validate():
        if form.loanId.data:
            query = query.filter(Loan.loanId == form.loanId.data)
        if form.bookId.data:
            query = query.filter(Loan.bookId == form.bookId.data)
        if form.studentId.data:
            query = query.filter(Loan.studentId == form.studentId.data)
        if form.loanDate.data:
            query = query.filter(Loan.loanDate == form.loanDate.data)
        if form.returnDate.data:
            query = query.filter(Loan.returnDate == form.returnDate.data)
        if form.createdBy.data:
            query = query.filter(Loan.createdBy == form.createdBy.data)
        if form.status.data:
            # Converter o valor do formulário para o Enum correspondente
            status_enum = StatusLoan(form.status.data.upper())
            query = query.filter(Loan.status == status_enum)

    per_page = 10
    emprestimosPaginados = query.paginate(page=page, per_page=per_page, error_out=False)

    pagination = Pagination(page=page, total=emprestimosPaginados.total, per_page=per_page, css_framework='bootstrap4')

    return render_template('emprestimos.html', form=form, loans=emprestimosPaginados, pagination=pagination)


@app.route('/palavras_chave')
@login_required
def palavras_chave():
    palavras_chave = KeyWord.query.all()
    return render_template('palavras_chave.html', palavras_chave=palavras_chave)



def splitStringIntoList(string):
    string = string.split(';')
    for i in string:
        i = i.strip()
        i = i.lower()
                
    return string


@app.route('/novo_livro', methods=['GET', 'POST'])
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
        if newBook:
            nBookObj = addFromForm(newBook)
            if nBookObj:
                keyWordsList = splitStringIntoList(form.keyWords.data)
                wordsForRelation = []

                for keyWord in keyWordsList:
                    keyWordExists = KeyWord.query.filter_by(word=keyWord).first()
                    if not keyWordExists:
                        newKeyWord = KeyWord(
                            word=keyWord,
                            creationDate=date.today(),
                            lastUpdate=date.today(),
                            createdBy=current_user.userId,
                            updatedBy=current_user.userId,
                        )
                        addFromForm(newKeyWord)
                        wordsForRelation.append(newKeyWord)
                    else:
                        wordsForRelation.append(keyWordExists)

                for kr in wordsForRelation:
                    newKeyWordBook = KeyWordBook(
                        bookId=nBookObj.bookId,
                        wordId=kr.wordId
                    )
                    addFromForm(newKeyWordBook)

                flash('Livro cadastrado com sucesso!', 'success')
                return redirect(url_for('novo_livro'))
            else:
                flash('Erro ao cadastrar livro!', 'danger')

    return render_template('novo_livro.html', form=form)

@app.route('/novo_aluno', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = StudentForm()
    if form.validate_on_submit():
        new_student = Student(
            studentName=form.studentName.data.lower().strip(),
            studentPhone=form.studentPhone.data.strip(),
            birthDate=form.birthDate.data,
            cpf=form.cpf.data.strip(), 
            rg=form.rg.data.strip(),
            gradeNumber=form.gradeNumber.data.strip(),
            className=form.className.data.lower().strip(),
            guardianName1=form.guardianName1.data.lower().strip(),
            guardianPhone1=form.guardianPhone1.data.strip(),
            guardianName2=form.guardianName2.data.lower().strip(),
            guardianPhone2=form.guardianPhone2.data.strip(),
            notes=form.notes.data.lower().strip(),
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        if new_student:
            if addFromForm(new_student):
                flash('Aluno cadastrado com sucesso!', 'success')
                return redirect(url_for('novo_aluno'))
            else:
                flash('Erro ao cadastrar aluno!', 'danger')
                print(form.errors)
        
    return render_template('novo_aluno.html', form=form)


@app.route('/novo_emprestimo', methods=['GET', 'POST'])
@login_required
def novo_emprestimo():
    form = LoanForm()
    if form.validate_on_submit():
        if validaEmprestimo(form, Loan, Book, StatusLoan):
            new_Loan = Loan(
                amount=form.amount.data,
                loanDate=form.loanDate.data,
                returnDate=form.returnDate.data,
                studentId=form.studentId.data,
                bookId=form.bookId.data,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=current_user.userId,
                updatedBy=current_user.userId,
                status=StatusLoan.ACTIVE,
            )
            if new_Loan:
                if addFromForm(new_Loan):
                    flash('Empréstimo cadastrado com sucesso!', 'success')
                    return redirect(url_for('novo_emprestimo'))
                else:
                    flash('Erro ao cadastrar empréstimo!', 'danger')
                    print(form.errors)
        
    return render_template('novo_emprestimo.html', form=form)


@app.route('/nova_palavra_chave', methods=['GET', 'POST'])
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
        if newKeyWord:
            if addFromForm(newKeyWord):
                flash('Palavra-chave cadastrada com sucesso!', 'success')
                return redirect(url_for('nova_palavra_chave'))
            else:
                flash('Erro ao cadastrar palavra-chave!', 'danger')
                print(form.errors)
    return render_template('nova_palavra_chave.html', form=form)


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_livro(id):
    livro = Book.query.get(id)
    form = BookForm(obj=livro)
    if form.validate_on_submit():
        form.populate_obj(livro)
        # db.session.commit()
        return redirect(url_for('livros'))
    return render_template('editar_livro.html', form=form)


@app.route('/editar_aluno/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aluno(id):
    aluno = Student.query.get(id)
    form = StudentForm(obj=aluno)
    if form.validate_on_submit():
        form.populate_obj(aluno)
        # db.session.commit()
        return redirect(url_for('alunos'))
    return render_template('editar_aluno.html', form=form)


@app.route('/editar_emprestimo/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_emprestimo(id):
    emprestimo = Loan.query.get(id)
    form = LoanForm(obj=emprestimo)
    if form.validate_on_submit():
        form.populate_obj(emprestimo)
        # db.session.commit()
        return redirect(url_for('emprestimos'))
    return render_template('editar_emprestimo.html', form=form)


@app.route('/editar_palavra_chave/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_palavra_chave(id):
    palavra_chave = KeyWord.query.get(id)
    form = KeyWordForm(obj=palavra_chave)
    if form.validate_on_submit():
        form.populate_obj(palavra_chave)
        # db.session.commit()
        return redirect(url_for('palavras_chave'))
    return render_template('editar_palavra_chave.html', form=form)


@app.route('/excluir_livro/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_livro(id):
    livro = Book.query.get(id)
    # db.session.delete(livro)
    # db.session.commit()
    return redirect(url_for('livros'))


@app.route('/excluir_aluno/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_aluno(id):
    aluno = Student.query.get(id)
    # db.session.delete(aluno)
    # db.session.commit()
    return redirect(url_for('alunos'))


@app.route('/excluir_emprestimo/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_emprestimo(id):
    emprestimo = Loan.query.get(id)
    # db.session.delete(emprestimo)
    # db.session.commit()
    return redirect(url_for('emprestimos'))


@app.route('/excluir_palavra_chave/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_palavra_chave(id):
    palavra_chave = KeyWord.query.get(id)
    # db.session.delete(palavra_chave)
    # db.session.commit()
    return redirect(url_for('palavras_chave'))
