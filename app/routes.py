from flask import render_template, redirect, url_for
from . import app, db
from app.models import Livro, Aluno, Emprestimo, PalavraChave
from app.forms import LivroForm, AlunoForm, EmprestimoForm, PalavraChaveForm
from flask_cors import CORS


CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/livros')
def livros():
    livros = Livro.query.all()
    return render_template('livros.html', livros=livros)


@app.route('/alunos')
def alunos():
    alunos = Aluno.query.all()
    return render_template('alunos.html', alunos=alunos)


@app.route('/emprestimos')
def emprestimos():
    emprestimos = Emprestimo.query.all()
    return render_template('emprestimos.html', emprestimos=emprestimos)


@app.route('/palavras_chave')
def palavras_chave():
    palavras_chave = PalavraChave.query.all()
    return render_template('palavras_chave.html', palavras_chave=palavras_chave)


@app.route('/novo_livro', methods=['GET', 'POST'])
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
        db.session.add(livro)
        db.session.commit()
        return redirect(url_for('livros'))
    return render_template('novo_livro.html', form=form)


@app.route('/novo_aluno', methods=['GET', 'POST'])
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
        db.session.add(aluno)
        db.session.commit()
        return redirect(url_for('alunos'))
    return render_template('novo_aluno.html', form=form)


@app.route('/novo_emprestimo', methods=['GET', 'POST'])
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
        db.session.add(emprestimo)
        db.session.commit()
        return redirect(url_for('emprestimos'))
    return render_template('novo_emprestimo.html', form=form)


@app.route('/nova_palavra_chave', methods=['GET', 'POST'])
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
    return render_template('nova_palavra_chave.html', form=form)


@app.route('/editar_livro/<int:id>', methods=['GET', 'POST'])
def editar_livro(id):
    livro = Livro.query.get(id)
    form = LivroForm(obj=livro)
    if form.validate_on_submit():
        form.populate_obj(livro)
        db.session.commit()
        return redirect(url_for('livros'))
    return render_template('editar_livro.html', form=form)


@app.route('/editar_aluno/<int:id>', methods=['GET', 'POST'])
def editar_aluno(id):
    aluno = Aluno.query.get(id)
    form = AlunoForm(obj=aluno)
    if form.validate_on_submit():
        form.populate_obj(aluno)
        db.session.commit()
        return redirect(url_for('alunos'))
    return render_template('editar_aluno.html', form=form)


@app.route('/editar_emprestimo/<int:id>', methods=['GET', 'POST'])
def editar_emprestimo(id):
    emprestimo = Emprestimo.query.get(id)
    form = EmprestimoForm(obj=emprestimo)
    if form.validate_on_submit():
        form.populate_obj(emprestimo)
        db.session.commit()
        return redirect(url_for('emprestimos'))
    return render_template('editar_emprestimo.html', form=form)


@app.route('/editar_palavra_chave/<int:id>', methods=['GET', 'POST'])
def editar_palavra_chave(id):
    palavra_chave = PalavraChave.query.get(id)
    form = PalavraChaveForm(obj=palavra_chave)
    if form.validate_on_submit():
        form.populate_obj(palavra_chave)
        db.session.commit()
        return redirect(url_for('palavras_chave'))
    return render_template('editar_palavra_chave.html', form=form)


@app.route('/excluir_livro/<int:id>', methods=['GET', 'POST'])
def excluir_livro(id):
    livro = Livro.query.get(id)
    db.session.delete(livro)
    db.session.commit()
    return redirect(url_for('livros'))


@app.route('/excluir_aluno/<int:id>', methods=['GET', 'POST'])
def excluir_aluno(id):
    aluno = Aluno.query.get(id)
    db.session.delete(aluno)
    db.session.commit()
    return redirect(url_for('alunos'))


@app.route('/excluir_emprestimo/<int:id>', methods=['GET', 'POST'])
def excluir_emprestimo(id):
    emprestimo = Emprestimo.query.get(id)
    db.session.delete(emprestimo)
    db.session.commit()
    return redirect(url_for('emprestimos'))


@app.route('/excluir_palavra_chave/<int:id>', methods=['GET', 'POST'])
def excluir_palavra_chave(id):
    palavra_chave = PalavraChave.query.get(id)
    db.session.delete(palavra_chave)
    db.session.commit()
    return redirect(url_for('palavras_chave'))

