from datetime import datetime


# verifica se a quantidade de livros solicitada é maior que 0
def v1(form):
    if form.amount.data <= 0:
        # print(f"\nform: {form.amount.data}\n")
        return False
    
    return True


# Verifica se a data de devolução é maior que a data de empréstimo
def v2(form):
    if form.returnDate.data > form.loanDate.data:
        # print(f"\nform: {form.returnDate.data}\n form: {form.loanDate.data}\n")
        return True
    
    return False


# Verifica quantos livros estarão disponíveis na data do empréstimo
def v3(form, activeBookLoans, book):
    # Inicializa a quantidade disponível como a quantidade total de livros
    availableBooks = book.amount

    # Itera sobre todos os empréstimos ativos
    for loan in activeBookLoans:
        # Verifica se as datas de empréstimo solicitadas coincidem com as datas dos empréstimos existentes
        # if form.loanDate.data <= loan.returnDate and form.returnDate.data >= loan.loanDate:
        if form.loanDate.data < loan.returnDate:
            availableBooks -= 1
    
    # Verifica se a quantidade de livros disponíveis é suficiente para a quantidade de livros solicitada no empréstimo
    if form.amount.data <= availableBooks:
        # print(f"\nform: {form.amount.data}\n qtLivrosDisp: {availableBooks}\n empatvs: {len(activeBookLoans)}\n")
        return True

    return False


def validaEmprestimo(form, Loan, Book, StatusLoan):
    # Pega cadastro do livro
    book = Book.query.get(form.bookId.data)

    if book:
        # Pesquisa todos os empréstimos ativos do livro
        activeBookLoans = Loan.query.filter_by(bookId=form.bookId.data, status=StatusLoan.ACTIVE).all()

        validacoes = [
            v1(form),
            v2(form),
            v3(form, activeBookLoans, book)
        ]

        # Se todos os testes passarem, retorna True, senão, retorna False 
        return all(validacoes)

    # Se não encontrar o livro, retorna False
    return False