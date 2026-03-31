from datetime import datetime

from app import db
from app.models import User # Importar o modelo User

# verifica se a quantidade de livros solicitada é maior que 0
def v1(form):
    if form.amount.data <= 0:
        # print(f"form: {form.amount.data}")
        return False
    
    return True

# Verifica se a data de devolução é maior que a data de empréstimo
def v2(form):
    if form.returnDate.data > form.loanDate.data:
        # print(f"form: {form.returnDate.data} form: {form.loanDate.data}")
        return True
    
    return False

# Verifica quantos livros estarão disponíveis na data do empréstimo
def v3(form, activeBookLoans, book):
    # Inicializa a quantidade disponível como a quantidade total de livros
    availableBooks = book.amount
    # Itera sobre todos os empréstimos ativos
    for loan in activeBookLoans:
        loan_start = loan.loanDate.date() if hasattr(loan.loanDate, 'date') else loan.loanDate
        loan_end = loan.returnDate.date() if hasattr(loan.returnDate, 'date') else loan.returnDate
        
        # Verifica se as datas de empréstimo solicitadas coincidem com as datas dos empréstimos existentes
        # if form.loanDate.data <= loan.returnDate and form.returnDate.data >= loan.loanDate: # Logica do GitHub Copilot
        # if form.returnDate.data > loan.loanDate >= form.loanDate.data or form.loanDate.data <= loan.returnDate < form.returnDate.data: # Minha lógica
        
        if form.loanDate.data < loan_end and form.returnDate.data > loan_start: # Logica do GPT
            availableBooks -= loan.amount
    
    # Verifica se a quantidade de livros disponíveis é suficiente para a quantidade de livros solicitada no empréstimo
    if form.amount.data <= availableBooks:
        return True

    return False

# Nova função de validação para verificar se o userId existe
def v4(form):
    user = db.session.get(User, form.userId.data)
    return user is not None and not getattr(user, 'deleted', False)

def validaEmprestimo(form, Loan, Book, StatusLoan):
    # Pega cadastro do livro
    book = db.session.get(Book, form.bookId.data)

    if book and not getattr(book, 'deleted', False):
        # Pesquisa todos os empréstimos ativos do livro
        activeBookLoans = Loan.query.filter_by(bookId=form.bookId.data, status=StatusLoan.ACTIVE).all()

        validacoes = [
            v1(form),
            v2(form),
            v3(form, activeBookLoans, book),
            v4(form) # Adicionar a nova validação de usuário
        ]

        # Se todos os testes passarem, retorna True, senão, retorna False 
        return all(validacoes)

    # Se não encontrar o livro, retorna False
    return False
