from flask_login import UserMixin
from sqlalchemy import Enum 
import enum

from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    userType = db.Column(db.String(80), nullable=False)
    # Time format: dd/mm/yyyy|hh:mm:ss
    creationDate = db.Column(db.Date, nullable=False)
    lastUpdate = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)

    def get_id(self):
        return self.userId



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
    creationDate = db.Column(db.Date, nullable=False)
    lastUpdate = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    
     # Relacionamento com keywords
    keywords = db.relationship('KeyWord', secondary='KeyWordBooks', backref='books')


class Student(db.Model):
    __tablename__ = 'students'

    studentId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    studentName = db.Column(db.String, nullable=False)
    studentPhone = db.Column(db.String, nullable=True)
    birthDate = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    rg = db.Column(db.String(10), nullable=True)
    gradeNumber = db.Column(db.Integer, nullable=False)
    className = db.Column(db.String, nullable=True)
    guardianName1 = db.Column(db.String, nullable=True)
    guardianPhone1 = db.Column(db.String, nullable=True)
    guardianName2 = db.Column(db.String, nullable=True)
    guardianPhone2 = db.Column(db.String, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    creationDate = db.Column(db.Date, nullable=False)
    lastUpdate = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)


class KeyWord(db.Model):
    __tablename__ = 'keyWords'

    wordId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String, unique=True, nullable=False)
    creationDate = db.Column(db.Date, nullable=False)
    lastUpdate = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)


class StatusLoan(enum.Enum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    LOST = "lost"
    # BGN_TODAY = "bgn today"
    # END_TODAY = "end today"


class Loan(db.Model):
    __tablename__ = 'loans'

    LoanId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Integer, nullable=False)
    loanDate = db.Column(db.Date, nullable=False)
    returnDate = db.Column(db.Date, nullable=False)
    studentId = db.Column(db.Integer, db.ForeignKey('students.studentId'), nullable=False)
    bookId = db.Column(db.Integer, db.ForeignKey('books.bookId'), nullable=False)
    student = db.relationship('Student', backref=db.backref('loans', lazy=True))
    book = db.relationship('Book', backref=db.backref('loans', lazy=True))
    creationDate = db.Column(db.Date, nullable=False)
    lastUpdate = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    status = db.Column(Enum(StatusLoan), nullable=False)

class KeyWordBook(db.Model):
    __tablename__ = 'KeyWordBooks'

    bookId = db.Column(db.Integer, db.ForeignKey('books.bookId'), primary_key=True, nullable=False)
    wordId = db.Column(db.Integer, db.ForeignKey('keyWords.wordId'), primary_key=True, nullable=False)

    def __init__(self, bookId, wordId):
        self.bookId = bookId
        self.wordId = wordId