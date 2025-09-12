from flask_login import UserMixin
from sqlalchemy import Enum, UniqueConstraint
from sqlalchemy.orm import validates, synonym
from datetime import date, datetime
import enum

from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    identificationCode = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    userCompleteName = db.Column(db.String(100), nullable=True)
    userType = db.Column(db.String(80), nullable=False)
    # Time format: dd/mm/yyyy|hh:mm:ss
    creationDate = db.Column(db.Date, nullable=False, default=date.today)
    lastUpdate = db.Column(db.Date, nullable=False, default=date.today)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=True)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=True)

    # Novos campos para unificar com Alunos
    userPhone = db.Column(db.String, nullable=True)
    birthDate = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    rg = db.Column(db.String(10), nullable=True)
    gradeNumber = db.Column(db.Integer, nullable=True)
    className = db.Column(db.String, nullable=True)
    guardianName1 = db.Column(db.String, nullable=True)
    guardianPhone1 = db.Column(db.String, nullable=True)
    guardianName2 = db.Column(db.String, nullable=True)
    guardianPhone2 = db.Column(db.String, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Backward-compat attribute so code/tests using `username` still work
    username = synonym('identificationCode')

    def get_id(self):
        return self.userId

    @validates('birthDate', 'creationDate', 'lastUpdate')
    def _convert_dates(self, key, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                # Tenta outros formatos se necessário, mas mantém valor se falhar
                return value
        if isinstance(value, datetime):
            return value.date()
        return value



class Book(db.Model):
    __tablename__ = 'books'
    
    bookId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookName = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    authorName = db.Column(db.String, nullable=True)
    publisherName = db.Column(db.String, nullable=True)
    publishedDate = db.Column(db.Date, nullable=True)
    acquisitionDate = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    creationDate = db.Column(db.Date, nullable=False, default=date.today)
    lastUpdate = db.Column(db.Date, nullable=False, default=date.today)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    
    # Relacionamento com keywords
    keywords = db.relationship('KeyWord', secondary='KeyWordBooks', backref='books')

    @validates('publishedDate', 'acquisitionDate', 'creationDate', 'lastUpdate')
    def _convert_dates(self, key, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.date()
        return value



class KeyWord(db.Model):
    __tablename__ = 'keyWords'

    wordId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String, unique=True, nullable=False)
    creationDate = db.Column(db.Date, nullable=False, default=date.today)
    lastUpdate = db.Column(db.Date, nullable=False, default=date.today)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)


class StatusLoan(enum.Enum):
    ACTIVE = "Ativo"
    OVERDUE = "Atrasado"
    COMPLETED = "Concluído"
    LOST = "Perdido"
    # BGN_TODAY = "bgn today"
    # END_TODAY = "end today"


class Loan(db.Model):
    __tablename__ = 'loans'

    loanId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Integer, nullable=False)
    loanDate = db.Column(db.Date, nullable=False)
    returnDate = db.Column(db.Date, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False) # Alterado para userId
    bookId = db.Column(db.Integer, db.ForeignKey('books.bookId'), nullable=False)
    creationDate = db.Column(db.Date, nullable=False, default=date.today)
    lastUpdate = db.Column(db.Date, nullable=False, default=date.today)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    status = db.Column(Enum(StatusLoan), nullable=False)
    
    user = db.relationship('User', foreign_keys=[userId], backref=db.backref('loans', lazy='dynamic')) 
    created_user = db.relationship('User', foreign_keys=[createdBy], backref=db.backref('loans_created', lazy='dynamic'))
    updated_user = db.relationship('User', foreign_keys=[updatedBy], backref=db.backref('loans_updated', lazy='dynamic'))
    book = db.relationship('Book', foreign_keys=[bookId], backref=db.backref('loans', lazy='dynamic'))

    @validates('loanDate', 'returnDate', 'creationDate', 'lastUpdate')
    def _convert_dates(self, key, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.date()
        return value


class KeyWordBook(db.Model):
    __tablename__ = 'KeyWordBooks'

    bookId = db.Column(db.Integer, db.ForeignKey('books.bookId'), primary_key=True, nullable=False)
    wordId = db.Column(db.Integer, db.ForeignKey('keyWords.wordId'), primary_key=True, nullable=False)

    def __init__(self, bookId, wordId):
        self.bookId = bookId
        self.wordId = wordId


# New RBAC models for detailed permissions
class Permission(db.Model):
    __tablename__ = 'permissions'

    permissionId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(100), unique=True, nullable=False)  # e.g., 'books.view'
    description = db.Column(db.String(255), nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'

    roleId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'aluno', 'colaborador', 'bibliotecario', 'admin'
    description = db.Column(db.String(255), nullable=True)


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        UniqueConstraint('roleId', 'permissionId', name='uq_role_permission'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roleId = db.Column(db.Integer, db.ForeignKey('roles.roleId'), nullable=False)
    permissionId = db.Column(db.Integer, db.ForeignKey('permissions.permissionId'), nullable=False)
