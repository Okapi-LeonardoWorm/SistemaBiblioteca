from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, PasswordField, StringField,
                     SubmitField, RadioField, SelectField, TextAreaField)
from wtforms.validators import (DataRequired, InputRequired, Length,
                                NumberRange, Optional, Regexp, ValidationError)
from .models import User
from datetime import datetime, timedelta
from .models import StatusLoan


# Forms to create and validate the data that will be inserted in the database
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=20, message="Seu nome de usuário deve conter entre 3 e 20 caracteres"),  Regexp(r'^[a-z_]+$', message="O nome de usuário pode conter apenas letras minúsculas e sublinhados(Underline), não pode conter espaços.")], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20, message="A senha deve conter entre 4 e 20 caracteres")], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=4, max=80)])
    userType = SelectField('Tipo de Cadastro', validators=[DataRequired()])
    userPhone = StringField('Telefone', validators=[Optional()])
    birthDate = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[Optional()])
    rg = StringField('RG', validators=[Optional()])
    # Student specific
    gradeNumber = IntegerField('Série/Ano', validators=[Optional()])
    className = StringField('Turma', validators=[Optional()])
    guardianName1 = StringField('Nome do Responsável 1', validators=[Optional()])
    guardianPhone1 = StringField('Telefone do Responsável 1', validators=[Optional()])
    guardianName2 = StringField('Nome do Responsável 2', validators=[Optional()])
    guardianPhone2 = StringField('Telefone do Responsável 2', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField("Registrar")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')


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
    userType = SelectField('Tipo de Usuário', choices=[
        ('aluno', 'Aluno'),
        ('colaborador', 'Colaborador'),
        ('bibliotecario', 'Bibliotecário'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    identificationCode = StringField('Código de Identificação', validators=[DataRequired(), Length(min=3, max=150)])
    userCompleteName = StringField('Nome completo', validators=[DataRequired(), Length(min=3, max=100)])
    password = PasswordField('Senha', validators=[Optional(), Length(min=4, max=80)])
    creationDate = DateField('Data de Criação', format='%Y-%m-%d', validators=[Optional()])
    lastUpdate = DateField('Última Atualização', format='%Y-%m-%d', validators=[Optional()])
    createdBy = IntegerField('Criado Por', validators=[Optional()])
    updatedBy = IntegerField('Atualizado Por', validators=[Optional()])
    userPhone = StringField('Telefone do Usuário', validators=[Optional()])
    birthDate = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[Optional()])
    cpf = StringField('CPF', validators=[Optional()])
    rg = StringField('RG', validators=[Optional()])
    gradeNumber = IntegerField('Número da Série', validators=[Optional()])
    className = StringField('Nome da Turma', validators=[Optional()])
    guardianName1 = StringField('Nome do Responsável 1', validators=[Optional()])
    guardianPhone1 = StringField('Telefone do Responsável 1', validators=[Optional()])
    guardianName2 = StringField('Nome do Responsável 2', validators=[Optional()])
    guardianPhone2 = StringField('Telefone do Responsável 2', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Usuário')

    def validate_identificationCode(self, identificationCode):
        existing = User.query.filter_by(identificationCode=identificationCode.data).first()
        # Permite manter o mesmo código ao editar o próprio registro
        if existing:
            current_id = getattr(self, 'instance_id', None)
            if not current_id or existing.userId != current_id:
                raise ValidationError('Código de identificação já existe. Por favor, escolha outro.')

    def __init__(self, *args, **kwargs):
        # Permite passar mode='create'|'edit' para ajustar validações dinâmicas
        self.mode = kwargs.pop('mode', 'create')
        # Permite passar o id da instância para validações (edição)
        self.instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)
        # birthDate obrigatório na criação, opcional na edição
        if self.mode == 'create':
            self.birthDate.validators = [DataRequired(message='Data de Nascimento é obrigatória')]
        else:
            self.birthDate.validators = [Optional()]