from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import func

from app import db
from app.models import Book, KeyWord, KeyWordBook, Loan, StatusLoan, User

bp = Blueprint('navigation', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.userType != 'admin':
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('navigation.menu'))

    # KPIs
    total_books = db.session.query(func.sum(Book.amount)).scalar() or 0
    total_loans_active = Loan.query.filter_by(status=StatusLoan.ACTIVE).count()
    total_students = User.query.filter(func.lower(User.userType).in_(['aluno', 'student'])).count()
    total_staff = User.query.filter(
        func.lower(User.userType).in_(['colaborador', 'bibliotecario', 'bibliotecário', 'staff'])
    ).count()
    overdue_loans_count = Loan.query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE).count()

    # Loan filtering
    loan_filter = request.args.get('filter', 'today')
    page = request.args.get(get_page_parameter(), 1, type=int)
    per_page = int(request.args.get('per_page', 10))
    
    loans_query = Loan.query.filter(Loan.status == StatusLoan.ACTIVE)
    if loan_filter == 'today':
        loans_query = loans_query.filter(Loan.returnDate == date.today())
    elif loan_filter == 'week':
        end_of_week = date.today() + timedelta(days=7 - date.today().weekday())
        loans_query = loans_query.filter(Loan.returnDate >= date.today(), Loan.returnDate <= end_of_week)
    elif loan_filter == 'overdue':
        loans_query = loans_query.filter(Loan.returnDate < date.today(), Loan.status == StatusLoan.ACTIVE)
    
    loans_pagination = loans_query.order_by(Loan.returnDate.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # Últimos empréstimos (para exibir quantidade retirada em cada empréstimo)
    recent_books_page = request.args.get('recent_books_page', 1, type=int)
    recent_books_per_page = int(request.args.get('recent_books_per_page', 10))
    recent_loans_query = Loan.query.order_by(Loan.loanDate.desc(), Loan.loanId.desc())

    recent_loans_pagination = recent_loans_query.paginate(page=recent_books_page, per_page=recent_books_per_page, error_out=False)

    recent_books_info = []
    for loan in recent_loans_pagination.items:
        if loan.book:
            recent_books_info.append({'book': loan.book, 'amount': loan.amount})

    # Distribuição de palavras-chave por ocorrências na tabela de relacionamento KeyWordBooks
    keyword_rows = db.session.query(
        KeyWord.word,
        func.count(KeyWordBook.wordId).label('usage_count')
    ).join(
        KeyWordBook, KeyWord.wordId == KeyWordBook.wordId
    ).group_by(
        KeyWord.wordId, KeyWord.word
    ).order_by(
        func.count(KeyWordBook.wordId).desc(), KeyWord.word.asc()
    ).all()

    keyword_top10 = [
        {
            'word': row.word,
            'count': row.usage_count,
        }
        for row in keyword_rows[:10]
    ]

    return render_template('dashboard.html',
                           total_books=total_books,
                           total_loans_active=total_loans_active,
                           total_students=total_students,
                           total_staff=total_staff,
                           overdue_loans_count=overdue_loans_count,
                           loans=loans_pagination,
                           loan_filter=loan_filter,
                           recent_books=recent_books_info,
                           recent_books_pagination=recent_loans_pagination,
                           keyword_top10=keyword_top10)


@bp.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

