from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, PasswordField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, InputRequired, Length,
                                NumberRange, Optional, Regexp, ValidationError)
from app.models import User
from datetime import datetime, timedelta


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


class BookForm(FlaskForm):
    bookName = StringField('Nome do Livro', validators=[DataRequired()])
    amount = IntegerField('Quantidade', default=1, validators=[
        DataRequired(), NumberRange(min=1)])
    authorName = StringField('Nome do Autor', validators=[DataRequired()])
    publisherName = StringField('Nome da Editora', validators=[DataRequired()])
    publishedDate = DateField(
        'Data de Publicação', format='%Y-%m-%d', validators=[DataRequired()])
    acquisitionDate = DateField('Data de Aquisição',
                                format='%Y-%m-%d', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[Optional()])
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
