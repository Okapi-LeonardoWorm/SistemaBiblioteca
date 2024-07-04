from time import strftime

from flask import Flask, redirect, render_template, session, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)

from app.forms import (AlunoForm, EmprestimoForm, LivroForm, LoginForm,
                       PalavraChaveForm, RegisterForm)
from app.models import Aluno, Emprestimo, Livro, PalavraChave, User

from . import app, db

from flask_sqlalchemy import SQLAlchemy, query


CORS(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.username.data.strip()

        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')

        usertype = "normal"

        creationdate = strftime("%Y-%m-%d")
        lastUpdateDt = strftime("%Y-%m-%d")

        new_user = User(
            username=name,
            password=hashed_password,
            usertype=usertype,
            creationdate=creationdate,
            lastUpdateDt=lastUpdateDt,
            createdBy=current_user.id,
            updatedBy=current_user.id
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Username: {form.username.data}")
        print(f"Password: {form.password.data}")
        user = User.query.filter_by(username=form.username.data).first()
        print("\n\n\n")
        print(user)
        # print(user.username)
        # print(user.usertype)
        # print(type(user.usertype))
        print("\n\n\n")

        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                session['logged_in'] = True
                session['usertype'] = user.usertype
                print("\n\n\n")
                print(session['usertype'])
                print("\n\n\n")
                login_user(user)
                return redirect(url_for('index'))
            else:
                print("Invalid password!")
    return render_template('login.html', form=form)


@app.route('/livros')
@login_required
def livros():
    livros = Livro.query.all()
    return render_template('livros.html', livros=livros)


@app.route('/alunos')
@login_required
def alunos():
    alunos = Aluno.query.all()
    return render_template('alunos.html', alunos=alunos)


@app.route('/emprestimos')
@login_required
def emprestimos():
    emprestimos = Emprestimo.query.all()
    return render_template('emprestimos.html', emprestimos=emprestimos)


@app.route('/palavras_chave')
@login_required
def palavras_chave():
    palavras_chave = PalavraChave.query.all()
    return render_template('palavras_chave.html', palavras_chave=palavras_chave)


@app.route('/novo_livro', methods=['GET', 'POST'])
@login_required
def novo_livro():
    form = LivroForm()
    if form.validate_on_submit():
        livro = Livro(
            nomeLivro=form.nomeLivro.data,
            quantidade=form.quantidade.data,
            nomeAutor=form.nomeAutor.data,
            nomeEditora=form.nomeEditora.data,
            dataPublicacao=form.dataPublicacao.data,
            dtAquisicao=form.dtAquisicao.data,
            descricao=form.descricao.data
        )
        print(
            form.nomeLivro.data,
            form.quantidade.data,
            form.nomeAutor.data,
            form.nomeEditora.data,
            form.dataPublicacao.data,
            form.dtAquisicao.data,
            form.descricao.data
        )
        db.session.add(livro)
        db.session.commit()
        # return redirect(url_for('livros'))
    else:
        print(form.errors)
    return render_template('novo_livro.html', form=form)


@app.route('/novo_aluno', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = AlunoForm()
    if form.validate_on_submit():
        aluno = Aluno(
            nomeAluno=form.nomeAluno.data,
            telefoneAluno=form.telefoneAluno.data,
            dtNascimento=form.dtNascimento.data,
            cpf=form.cpf.data,
            rg=form.rg.data,
            serie=form.serie.data,
            turma=form.turma.data,
            nomeResponsavel1=form.nomeResponsavel1.data,
            telefoneResponsavel1=form.telefoneResponsavel1.data,
            nomeResponsavel2=form.nomeResponsavel2.data,
            telefoneResponsavel2=form.telefoneResponsavel2.data,
            observacao=form.observacao.data
        )
        print(aluno)
        db.session.add(aluno)
        db.session.commit()
        # return redirect(url_for('alunos'))
    else:
        print(form.errors)
        print(
            form.nomeAluno.data,
            form.telefoneAluno.data,
            form.dtNascimento.data,
            form.cpf.data,
            form.rg.data,
            form.serie.data,
            form.turma.data,
            form.nomeResponsavel1.data,
            form.telefoneResponsavel1.data,
            form.nomeResponsavel2.data,
            form.telefoneResponsavel2.data,
            form.observacao.data
        )
    return render_template('novo_aluno.html', form=form)


@app.route('/novo_emprestimo', methods=['GET', 'POST'])
@login_required
def novo_emprestimo():
    form = EmprestimoForm()
    if form.validate_on_submit():
        emprestimo = Emprestimo(
            quantidade=form.quantidade.data,
            dataEmprestimo=form.dataEmprestimo.data,
            dataDevolucao=form.dataDevolucao.data,
            aluno_id=form.aluno_id.data,
            livro_id=form.livro_id.data
        )
        print(emprestimo)
        db.session.add(emprestimo)
        db.session.commit()
        # return redirect(url_for('emprestimos'))
    else:
        print(form.errors)
        print(
            form.quantidade.data,
            form.dataEmprestimo.data,
            form.dataDevolucao.data,
            form.aluno_id.data,
            form.livro_id.data
        )
    return render_template('novo_emprestimo.html', form=form)


@app.route('/nova_palavra_chave', methods=['GET', 'POST'])
@login_required
def nova_palavra_chave():
    form = PalavraChaveForm()
    if form.validate_on_submit():
        palavra_chave = PalavraChave(
            palavra=form.palavra.data,
            livro_id=form.livro_id.data
        )
        db.session.add(palavra_chave)
        db.session.commit()
        return redirect(url_for('palavras_chave'))
    else:
        print(form.errors)
    return render_template('nova_palavra_chave.html', form=form)


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_livro(id):
    livro = Livro.query.get(id)
    form = LivroForm(obj=livro)
    if form.validate_on_submit():
        form.populate_obj(livro)
        db.session.commit()
        return redirect(url_for('livros'))
    return render_template('editar_livro.html', form=form)


@app.route('/editar_aluno/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aluno(id):
    aluno = Aluno.query.get(id)
    form = AlunoForm(obj=aluno)
    if form.validate_on_submit():
        form.populate_obj(aluno)
        db.session.commit()
        return redirect(url_for('alunos'))
    return render_template('editar_aluno.html', form=form)


@app.route('/editar_emprestimo/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_emprestimo(id):
    emprestimo = Emprestimo.query.get(id)
    form = EmprestimoForm(obj=emprestimo)
    if form.validate_on_submit():
        form.populate_obj(emprestimo)
        db.session.commit()
        return redirect(url_for('emprestimos'))
    return render_template('editar_emprestimo.html', form=form)


@app.route('/editar_palavra_chave/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_palavra_chave(id):
    palavra_chave = PalavraChave.query.get(id)
    form = PalavraChaveForm(obj=palavra_chave)
    if form.validate_on_submit():
        form.populate_obj(palavra_chave)
        db.session.commit()
        return redirect(url_for('palavras_chave'))
    return render_template('editar_palavra_chave.html', form=form)


@app.route('/excluir_livro/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_livro(id):
    livro = Livro.query.get(id)
    db.session.delete(livro)
    db.session.commit()
    return redirect(url_for('livros'))


@app.route('/excluir_aluno/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_aluno(id):
    aluno = Aluno.query.get(id)
    db.session.delete(aluno)
    db.session.commit()
    return redirect(url_for('alunos'))


@app.route('/excluir_emprestimo/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_emprestimo(id):
    emprestimo = Emprestimo.query.get(id)
    db.session.delete(emprestimo)
    db.session.commit()
    return redirect(url_for('emprestimos'))


@app.route('/excluir_palavra_chave/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_palavra_chave(id):
    palavra_chave = PalavraChave.query.get(id)
    db.session.delete(palavra_chave)
    db.session.commit()
    return redirect(url_for('palavras_chave'))
