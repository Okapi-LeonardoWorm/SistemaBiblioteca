from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Regexp, Length


class LivroForm(FlaskForm):
    nomeLivro = StringField('Nome do Livro', validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', default=1, validators=[DataRequired(), NumberRange(min=1)])
    nomeAutor = StringField('Nome do Autor', validators=[DataRequired()])
    nomeEditora = StringField('Nome da Editora', validators=[DataRequired()])
    dataPublicacao = DateField('Data de Publicação', format='%Y-%m-%d', validators=[DataRequired()])
    dtAquisicao = DateField('Data de Aquisição', format='%Y-%m-%d', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class AlunoForm(FlaskForm):
    nomeAluno = StringField('Nome do Aluno', validators=[DataRequired()])
    telefoneAluno = StringField('Telefone do Aluno', validators=[Optional(), Length(max=12), Regexp(r'^\d+$', message="Telefone deve conter apenas números")])
    dtNascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional(), Length(min=11,max=11), Regexp(r'^\d+$', message="CPF deve conter apenas números")])
    rg = StringField('RG', validators=[Optional(), Length(min=9,max=10), Regexp(r'^\d+$', message="RG deve conter apenas números")])
    serieTurma = StringField('Série/Turma', validators=[DataRequired()])
    nomeResponsavel1 = StringField('Nome do Responsável 1', validators=[Optional()])
    telefoneResponsavel1 = StringField('Telefone do Responsável 1', validators=[Optional()])
    nomeResponsavel2 = StringField('Nome do Responsável 2', validators=[Optional()])
    telefoneResponsavel2 = StringField('Telefone do Responsável 2', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class EmprestimoForm(FlaskForm):
    quantidade = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    dataEmprestimo = DateField('Data de Empréstimo', format='%Y-%m-%d', validators=[DataRequired()])
    dataDevolucao = DateField('Data de Devolução', format='%Y-%m-%d', validators=[DataRequired()])
    aluno_id = IntegerField('ID do Aluno', validators=[DataRequired(), NumberRange(min=1)])
    livro_id = IntegerField('ID do Livro', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Cadastrar')


class PalavraChaveForm(FlaskForm):
    palavra = StringField('Palavra', validators=[DataRequired()])
    livro_id = IntegerField('ID do Livro', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')
