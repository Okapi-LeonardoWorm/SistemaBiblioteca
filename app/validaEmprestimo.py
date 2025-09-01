from datetime import datetime

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
    print("availableBooks INI: ", availableBooks)
    # Itera sobre todos os empréstimos ativos
    for loan in activeBookLoans:
        # Verifica se as datas de empréstimo solicitadas coincidem com as datas dos empréstimos existentes
        # if form.loanDate.data <= loan.returnDate and form.returnDate.data >= loan.loanDate: # Logica do GitHub Copilot
        # if form.returnDate.data > loan.loanDate >= form.loanDate.data or form.loanDate.data <= loan.returnDate < form.returnDate.data: # Minha lógica
        if form.loanDate.data < loan.returnDate and form.returnDate.data > loan.loanDate: # Logica do GPT
            availableBooks -= loan.amount
    print("availableBooks: END", availableBooks)
    
    # Verifica se a quantidade de livros disponíveis é suficiente para a quantidade de livros solicitada no empréstimo
    if form.amount.data <= availableBooks:
        print("availableBooks: IF", form.amount.data <= availableBooks)
        return True

    return False

# Nova função de validação para verificar se o userId existe
def v4(form):
    user = User.query.get(form.userId.data)
    return user is not None

def validaEmprestimo(form, Loan, Book, StatusLoan):
    # Pega cadastro do livro
    book = Book.query.get(form.bookId.data)

    if book:
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
