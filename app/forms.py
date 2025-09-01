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
        max=12), Regexp(r'^d+$', message="Telefone deve conter apenas números")])
    birthDate = DateField('Data de Nascimento',
                          format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional(), Length(
        min=11, max=11), Regexp(r'^d+$', message="CPF deve conter apenas números")])
    rg = StringField('RG', validators=[Optional(), Length(min=9, max=10), Regexp(
        r'^d+$', message="RG deve conter apenas números")])
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
    userId = IntegerField('ID do Usuário', validators=[
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
    bookName = StringField('Nome do Livro', validators=[Optional()])
    publisherName = StringField('Nome da Editora', validators=[Optional()])
    authorName = StringField('Nome do autor', validators=[Optional()])
    studentId = IntegerField('ID do Aluno', validators=[Optional()])
    studentName = StringField('Nome do Aluno', validators=[Optional()])
    userId = IntegerField('ID do Usuário', validators=[Optional()])
    username = StringField('Nome do Usuário', validators=[Optional()])
    loanDate = DateField('Data de Empréstimo',
                         format='%Y-%m-%d', validators=[Optional()])
    returnDate = DateField('Data de Devolução',
                           format='%Y-%m-%d', validators=[Optional()])
    createdBy = StringField('Criado por', validators=[Optional()])
    # Definir as opções de status a partir do Enum StatusLoan
    status_choices = [(status.name, status.value.capitalize()) for status in StatusLoan]
    status = SelectField('Status', choices=status_choices, validators=[Optional()])
    submit = SubmitField('Buscar')
    

class UserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=4, max=80)])
    userType = StringField('Tipo de Usuário', validators=[DataRequired(), Length(max=80)])
    creationDate = DateField('Data de Criação', format='%Y-%m-%d', validators=[DataRequired()])
    lastUpdate = DateField('Última Atualização', format='%Y-%m-%d', validators=[DataRequired()])
    createdBy = IntegerField('Criado Por', validators=[DataRequired()])
    updatedBy = IntegerField('Atualizado Por', validators=[DataRequired()])
    userPhone = StringField('Telefone do Usuário', validators=[Optional()])
    birthDate = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional()])
    rg = StringField('RG', validators=[Optional()])
    gradeNumber = IntegerField('Número da Série', validators=[DataRequired()])
    className = StringField('Nome da Turma', validators=[Optional()])
    guardianName1 = StringField('Nome do Responsável 1', validators=[Optional()])
    guardianPhone1 = StringField('Telefone do Responsável 1', validators=[Optional()])
    guardianName2 = StringField('Nome do Responsável 2', validators=[Optional()])
    guardianPhone2 = StringField('Telefone do Responsável 2', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Usuário')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('Nome de usuário já existe. Por favor, escolha um nome diferente.')
