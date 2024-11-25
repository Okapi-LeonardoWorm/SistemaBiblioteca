from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, PasswordField, StringField,
                     SubmitField, RadioField, SelectField, TextAreaField)
from wtforms.validators import (DataRequired, InputRequired, Length,
                                NumberRange, Optional, Regexp, ValidationError)
from app.models import User
from datetime import datetime, timedelta
from app.models import StatusLoan


# Forms to create and validate the data that will be inserted in the database
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=20, message="Seu nome de usuário deve conter entre 3 e 20 caracteres"),  Regexp(r'^[a-z_]+$', message="O nome de usuário pode conter apenas letras minúsculas e sublinhados(Underline), não pode conter espaços.")], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20, message="A senha deve conter entre 4 e 20 caracteres")], render_kw={"placeholder": "Password"})

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


class BookForm(FlaskForm):
    bookName = StringField('Nome do Livro', validators=[DataRequired()])
    amount = IntegerField('Quantidade', default=1, validators=[
        DataRequired(), NumberRange(min=1)])
    authorName = StringField('Nome do Autor', validators=[Optional()])
    publisherName = StringField('Nome da Editora', validators=[Optional()])
    publishedDate = DateField(
        'Data de Publicação', format='%Y-%m-%d', validators=[Optional()])
    acquisitionDate = DateField('Data de Aquisição',
                                format='%Y-%m-%d', validators=[Optional()])
    description = TextAreaField('Descrição', validators=[Optional()])
    keyWords = StringField('Palavras-chave', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class StudentForm(FlaskForm):
    studentName = StringField('Nome do Aluno', validators=[DataRequired()])
    studentPhone = StringField('Telefone do Aluno', validators=[Optional(), Length(
        max=12), Regexp(r'^\d+$', message="Telefone deve conter apenas números")])
    birthDate = DateField('Data de Nascimento',
                          format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional(), Length(
        min=11, max=11), Regexp(r'^\d+$', message="CPF deve conter apenas números")])
    rg = StringField('RG', validators=[Optional(), Length(min=9, max=10), Regexp(
        r'^\d+$', message="RG deve conter apenas números")])
    gradeNumber = StringField('Série', validators=[DataRequired()])
    className = StringField('Turma', validators=[Optional()])
    guardianName1 = StringField(
        'Nome do Responsável 1', validators=[Optional()])
    guardianPhone1 = StringField(
        'Telefone do Responsável 1', validators=[Optional()])
    guardianName2 = StringField(
        'Nome do Responsável 2', validators=[Optional()])
    guardianPhone2 = StringField(
        'Telefone do Responsável 2', validators=[Optional()])
    notes = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Cadastrar')


class KeyWordForm(FlaskForm):
    word = StringField('Palavra', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


class LoanForm(FlaskForm):
    amount = IntegerField('Quantidade', default=1, validators=[
        DataRequired(), NumberRange(min=1)])
    loanDate = DateField(
        'Data de Empréstimo', default=datetime.today, format='%Y-%m-%d', validators=[DataRequired()])
    returnDate = DateField(
        'Data de Devolução',
        default=(datetime.today() + timedelta(days=7)), format='%Y-%m-%d', validators=[DataRequired()])
    studentId = IntegerField('ID do Aluno', validators=[
        DataRequired(), NumberRange(min=1)])
    bookId = IntegerField('ID do Livro', validators=[
        DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Cadastrar')


class KeyWordBookForm(FlaskForm):
    bookId = IntegerField('ID do Livro', validators=[DataRequired()])
    wordId = StringField('ID da Palavra', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


# Search forms
class SearchBooksForm(FlaskForm):
    bookId = IntegerField('ID', validators=[Optional()])
    bookName = StringField('Nome do Livro', validators=[Optional()])
    authorName = StringField('Nome do Autor', validators=[Optional()])
    publisherName = StringField('Nome da Editora', validators=[Optional()])
    publishedDate = DateField('Data de Publicação',
                              format='%Y-%m-%d', validators=[Optional()])
    acquisitionDate = DateField('Data de Aquisição',
                                format='%Y-%m-%d', validators=[Optional()])
    keywords = StringField('Palavras-chave', validators=[Optional()])
    submit = SubmitField('Buscar')
    

class SearchLoansForm(FlaskForm):
    loanId = IntegerField('ID do Empréstimo', validators=[Optional()])
    bookId = IntegerField('ID do Livro', validators=[Optional()])
    studentId = IntegerField('ID do Aluno', validators=[Optional()])
    userId = IntegerField('ID do Usuário', validators=[Optional()])
    loanDate = DateField('Data de Empréstimo',
                         format='%Y-%m-%d', validators=[Optional()])
    returnDate = DateField('Data de Devolução',
                           format='%Y-%m-%d', validators=[Optional()])
    createdBy = StringField('Criado por', validators=[Optional()])
    # Definir as opções de status a partir do Enum StatusLoan
    status_choices = [(status.name, status.value.capitalize()) for status in StatusLoan]
    status = SelectField('Status', choices=status_choices, validators=[Optional()])
    submit = SubmitField('Buscar')
    