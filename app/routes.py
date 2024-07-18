# from time import strftime
from datetime import date

from flask import Flask, redirect, render_template, session, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)

from app.forms import (StudentForm, LoanForm, BookForm, LoginForm,
                       KeyWordForm, RegisterForm)
from app.models import Student, Loan, Book, KeyWord, User, StatusLoan

from . import app
from .dbExecute import addFromForm
from .validaEmprestimo import validaEmprestimo

from flask_sqlalchemy import SQLAlchemy, query


CORS(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userId):
    return User.query.get(int(userId))


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
            addFromForm(new_user)
        return redirect(url_for('login'))

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
                session['userType'] = user.userType
                login_user(user)
                return redirect(url_for('index'))
            else:
                print("Invalid password!")
    else:
        print("Err:>", form.errors)
    return render_template('login.html', form=form)


@app.route('/livros')
@login_required
def livros():
    livros = Book.query.all()
    return render_template('livros.html', livros=livros)


@app.route('/alunos')
@login_required
def alunos():
    alunos = Student.query.all()
    return render_template('alunos.html', alunos=alunos)


@app.route('/emprestimos')
@login_required
def emprestimos():
    emprestimos = Loan.query.all()
    return render_template('emprestimos.html', emprestimos=emprestimos)


@app.route('/palavras_chave')
@login_required
def palavras_chave():
    palavras_chave = KeyWord.query.all()
    return render_template('palavras_chave.html', palavras_chave=palavras_chave)


@app.route('/novo_livro', methods=['GET', 'POST'])
@login_required
def novo_livro():
    form = BookForm()
    if form.validate_on_submit():
        new_book = Book(
            bookName=form.bookName.data,
            amount=form.amount.data,
            authorName=form.authorName.data,
            publisherName=form.publisherName.data,
            publishedDate=form.publishedDate.data,
            acquisitionDate=form.acquisitionDate.data,
            description=form.description.data,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        if new_book:
            addFromForm(new_book)
        # return redirect(url_for('livros'))
    else:
        print(form.errors)
    return render_template('novo_livro.html', form=form)


@app.route('/novo_aluno', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = StudentForm()
    if form.validate_on_submit():
        new_student = Student(
            studentName=form.studentName.data,
            studentPhone=form.studentPhone.data,
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
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        print(new_student)
        if new_student:
            addFromForm(new_student)
        # return redirect(url_for('alunos'))
    else:
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
                addFromForm(new_Loan)
            # return redirect(url_for('emprestimos'))
    else:
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
            addFromForm(newKeyWord)
        # return redirect(url_for('palavras_chave'))
    else:
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
