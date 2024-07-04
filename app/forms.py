from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, PasswordField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, InputRequired, Length,
                                NumberRange, Optional, Regexp, ValidationError)
from models import User


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if not existing_user_username:
            raise ValidationError("Username does not exist!")


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20), Regexp(
        "^[a-z]+$", message="Username must contain only lowercase letters")], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "Username already exists! Please try another one.")


class LivroForm(FlaskForm):
    nomeLivro = StringField('Nome do Livro', validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', default=1, validators=[
                              DataRequired(), NumberRange(min=1)])
    nomeAutor = StringField('Nome do Autor', validators=[DataRequired()])
    nomeEditora = StringField('Nome da Editora', validators=[DataRequired()])
    dataPublicacao = DateField(
        'Data de Publicação', format='%Y-%m-%d', validators=[DataRequired()])
    dtAquisicao = DateField('Data de Aquisição',
                            format='%Y-%m-%d', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class AlunoForm(FlaskForm):
    nomeAluno = StringField('Nome do Aluno', validators=[DataRequired()])
    telefoneAluno = StringField('Telefone do Aluno', validators=[Optional(), Length(
        max=12), Regexp(r'^\d+$', message="Telefone deve conter apenas números")])
    dtNascimento = DateField('Data de Nascimento',
                             format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional(), Length(
        min=11, max=11), Regexp(r'^\d+$', message="CPF deve conter apenas números")])
    rg = StringField('RG', validators=[Optional(), Length(min=9, max=10), Regexp(
        r'^\d+$', message="RG deve conter apenas números")])
    serie = StringField('Série', validators=[DataRequired()])
    turma = StringField('Turma', validators=[Optional()])
    nomeResponsavel1 = StringField(
        'Nome do Responsável 1', validators=[Optional()])
    telefoneResponsavel1 = StringField(
        'Telefone do Responsável 1', validators=[Optional()])
    nomeResponsavel2 = StringField(
        'Nome do Responsável 2', validators=[Optional()])
    telefoneResponsavel2 = StringField(
        'Telefone do Responsável 2', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class EmprestimoForm(FlaskForm):
    quantidade = IntegerField('Quantidade', validators=[
                              DataRequired(), NumberRange(min=1)])
    dataEmprestimo = DateField(
        'Data de Empréstimo', format='%Y-%m-%d', validators=[DataRequired()])
    dataDevolucao = DateField(
        'Data de Devolução', format='%Y-%m-%d', validators=[DataRequired()])
    aluno_id = IntegerField('ID do Aluno', validators=[
                            DataRequired(), NumberRange(min=1)])
    livro_id = IntegerField('ID do Livro', validators=[
                            DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Cadastrar')


class PalavraChaveForm(FlaskForm):
    palavra = StringField('Palavra', validators=[DataRequired()])
    livro_id = IntegerField('ID do Livro', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')
