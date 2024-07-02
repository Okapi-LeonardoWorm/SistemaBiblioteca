from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class LivroForm(FlaskForm):
    nomeLivro = StringField('Nome do Livro', validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    nomeAutor = StringField('Nome do Autor', validators=[DataRequired()])
    nomeEditora = StringField('Nome da Editora', validators=[DataRequired()])
    dataPublicacao = DateField('Data de Publicação', format='%Y-%m-%d', validators=[DataRequired()])
    dtAquisicao = DateField('Data de Aquisição', format='%Y-%m-%d', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


class AlunoForm(FlaskForm):
    nomeAluno = StringField('Nome do Aluno', validators=[DataRequired()])
    telefoneAluno = StringField('Telefone do Aluno')
    dtNascimento = DateField('Data de Nascimento', format='%d/%m/%Y', validators=[DataRequired()])
    cpf = StringField('CPF')
    rg = StringField('RG')
    serie = IntegerField('Série', validators=[DataRequired()])
    turma = StringField('Turma')
    nomeResponsavel1 = StringField('Nome do Responsável 1')
    telefoneResponsavel1 = StringField('Telefone do Responsável 1')
    nomeResponsavel2 = StringField('Nome do Responsável 2')
    telefoneResponsavel2 = StringField('Telefone do Responsável 2')
    observacao = TextAreaField('Observação')
    submit = SubmitField('Cadastrar')


class EmprestimoForm(FlaskForm):
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    dataEmprestimo = DateField('Data de Empréstimo', format='%d/%m/%Y', validators=[DataRequired()])
    dataDevolucao = DateField('Data de Devolução', format='%d/%m/%Y', validators=[DataRequired()])
    aluno_id = IntegerField('ID do Aluno', validators=[DataRequired()])
    livro_id = IntegerField('ID do Livro', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


class PalavraChaveForm(FlaskForm):
    palavra = StringField('Palavra', validators=[DataRequired()])
    livro_id = IntegerField('ID do Livro', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

