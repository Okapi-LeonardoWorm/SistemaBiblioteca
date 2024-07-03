from app import db


class Livro(db.Model):
    __tablename__ = 'livro'

    idLivro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nomeLivro = db.Column(db.String, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    nomeAutor = db.Column(db.String, nullable=False)
    nomeEditora = db.Column(db.String, nullable=False)
    dataPublicacao = db.Column(db.Date, nullable=False)
    dtAquisicao = db.Column(db.Date, nullable=True)
    descricao = db.Column(db.Text, nullable=True)


class Aluno(db.Model):
    __tablename__ = 'aluno'

    idAluno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nomeAluno = db.Column(db.String, nullable=False)
    telefoneAluno = db.Column(db.String, nullable=True)
    dtNascimento = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    rg = db.Column(db.String(10), nullable=True)
    serieTurma = db.Column(db.String, nullable=False)
    nomeResponsavel1 = db.Column(db.String, nullable=True)
    telefoneResponsavel1 = db.Column(db.String, nullable=True)
    nomeResponsavel2 = db.Column(db.String, nullable=True)
    telefoneResponsavel2 = db.Column(db.String, nullable=True)
    observacao = db.Column(db.Text, nullable=True)


class PalavraChave(db.Model):
    __tablename__ = 'palavraChave'

    idPalavra = db.Column(db.Integer, primary_key=True, autoincrement=True)
    palavra = db.Column(db.String, nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.idLivro'), nullable=False)
    livro = db.relationship('Livro', backref=db.backref('palavras_chave', lazy=True))


class Emprestimo(db.Model):
    __tablename__ = 'emprestimo'

    idEmprestimo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantidade = db.Column(db.Integer, nullable=False)
    dataEmprestimo = db.Column(db.Date, nullable=False)
    dataDevolucao = db.Column(db.Date, nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.idAluno'), nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.idLivro'), nullable=False)
    aluno = db.relationship('Aluno', backref=db.backref('emprestimos', lazy=True))
    livro = db.relationship('Livro', backref=db.backref('emprestimos', lazy=True))
    