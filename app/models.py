from flask_login import UserMixin

from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    usertype = db.Column(db.String(80), nullable=False)
    # Time format: dd/mm/yyyy|hh:mm:ss
    creationdate = db.Column(db.String(80), nullable=False)
    lastUpdateDt = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)



class Livro(db.Model):
    __tablename__ = 'livros'
    
    idLivro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nomeLivro = db.Column(db.String, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    nomeAutor = db.Column(db.String, nullable=False)
    nomeEditora = db.Column(db.String, nullable=False)
    dataPublicacao = db.Column(db.Date, nullable=False)
    dtAquisicao = db.Column(db.Date, nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    creationDt = db.Column(db.Date, nullable=False)
    lastUpdateDt = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Aluno(db.Model):
    __tablename__ = 'alunos'

    idAluno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nomeAluno = db.Column(db.String, nullable=False)
    telefoneAluno = db.Column(db.String, nullable=True)
    dtNascimento = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    rg = db.Column(db.String(10), nullable=True)
    serie = db.Column(db.Integer, nullable=False)
    turma = db.Column(db.String, nullable=True)
    nomeResponsavel1 = db.Column(db.String, nullable=True)
    telefoneResponsavel1 = db.Column(db.String, nullable=True)
    nomeResponsavel2 = db.Column(db.String, nullable=True)
    telefoneResponsavel2 = db.Column(db.String, nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    creationDt = db.Column(db.Date, nullable=False)
    lastUpdateDt = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class PalavraChave(db.Model):
    __tablename__ = 'palavrasChave'

    idPalavra = db.Column(db.Integer, primary_key=True, autoincrement=True)
    palavra = db.Column(db.String, nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.idLivro'), nullable=False)
    livro = db.relationship('Livro', backref=db.backref('palavras_chave', lazy=True))
    creationDt = db.Column(db.Date, nullable=False)
    lastUpdateDt = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Emprestimo(db.Model):
    __tablename__ = 'emprestimos'

    idEmprestimo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantidade = db.Column(db.Integer, nullable=False)
    dataEmprestimo = db.Column(db.Date, nullable=False)
    dataDevolucao = db.Column(db.Date, nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.idAluno'), nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.idLivro'), nullable=False)
    aluno = db.relationship('Aluno', backref=db.backref('emprestimos', lazy=True))
    livro = db.relationship('Livro', backref=db.backref('emprestimos', lazy=True))
    creationDt = db.Column(db.Date, nullable=False)
    lastUpdateDt = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    