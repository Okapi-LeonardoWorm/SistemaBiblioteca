# Rotas de API Interna (apis)

## Objetivo

Documentar o blueprint apis, usado por componentes de interface para busca assistida de usuarios e livros.

## Fonte principal

- app/routes/apis.py
- app/utils/date_utils.py
- app/utils/loan_utils.py

## Endpoints

1. GET /api/users/search
   - Parametros:
     - q: termo de busca (obrigatorio)
     - limit: limite de resultados (default 10)
   - Retorno: lista de usuarios ativos com atributos de identificacao e perfil.
2. GET /api/books/search
   - Parametros:
     - q: termo de busca (obrigatorio)
     - limit: limite de resultados (default 10)
     - loanDate: data de inicio para disponibilidade (opcional)
     - returnDate: data fim para disponibilidade (opcional)
   - Retorno: lista de livros ativos com disponibilidade calculada para o periodo.
3. GET /api/users/<user_id>/loan-history
    - Parametros:
       - q: busca por nome do livro (opcional)
       - statuses: lista de status do emprestimo (opcional, repetivel)
    - Retorno: historico de emprestimos do usuario para consumo em modal de edicao.
4. GET /api/books/<book_id>/loan-history
    - Parametros:
       - q: busca por nome ou codigo do usuario (opcional)
       - statuses: lista de status do emprestimo (opcional, repetivel)
    - Retorno: historico de emprestimos do livro para consumo em modal de edicao.
5. GET /api/keywords/<keyword_id>/book-history
    - Parametros:
       - q: busca por nome do livro ou nome do autor (opcional)
    - Retorno: listagem de livros associados a uma tag para consumo em modal de edicao.

## Contrato de resposta

- Resposta no formato JSON com chave results.
- Se q vazio, retorna results vazio (sem erro).
- Campos derivados:
  - users.search inclui age calculada.
  - books.search inclui available e lista de keywords.
- Endpoints de historico retornam:
   - success: boolean
   - summary:
      - total_borrowed
      - total_returned
   - status_options: lista com name e label do enum StatusLoan
   - items: lista de emprestimos serializados
      - user-history: loanId, bookName, loanDate, returnDate, statusName, statusLabel
      - book-history: loanId, userCode, userName, loanDate, returnDate, statusName, statusLabel
- Endpoint de livros por tag retorna:
   - success: boolean
   - summary:
      - total_books
   - items: lista de livros serializados
      - keyword-book-history: bookId, bookName, authorName

## Controle de acesso

- Todos os endpoints exigem login_required.

## Regras de negocio relevantes

- Apenas registros nao deletados sao retornados.
- limit e convertido para inteiro com fallback seguro.
- available usa available_copies_for_range com status ACTIVE dos emprestimos.
- Endpoints de historico validam user_id/book_id e retornam 404 se nao encontrados.
- Endpoint de livros por tag valida keyword_id e retorna 404 se nao encontrado.
- Filtro de statuses aceita apenas valores existentes em StatusLoan.
- total_borrowed dos historicos desconsidera emprestimos CANCELLED.
- total_returned considera status COMPLETED.
- Endpoint de livros por tag considera apenas livros ativos (Book.deleted = False).

## Riscos e pontos de atencao

1. Limite sem teto explicito:
   - considerar hard cap para evitar queries caras.
2. Busca textual ampla:
   - usar indices apropriados nas colunas consultadas.
3. Exposicao de campos:
   - revisar periodicamente campos retornados para minimizar superficie de dados.

## Troubleshooting

1. API retorna vazio com dados existentes:
   - verificar filtro deleted e valor de q.
2. Disponibilidade incoerente:
   - verificar parse de loanDate/returnDate e status de emprestimos ativos.
3. Latencia em autocomplete:
   - revisar indices, tamanho de limit e padrao de ilike.
4. Historico vazio com dados aparentes:
   - verificar filtro de status selecionado e termo de busca q.
5. Divergencia no dashboard do historico:
   - lembrar que retirados nao contabiliza CANCELLED e devolvidos contabiliza COMPLETED.
6. Livros esperados nao aparecem no historico da tag:
   - verificar se o livro esta ativo e se a busca q nao esta filtrando indevidamente por livro/autor.

## Diretriz de evolucao

- Versionar endpoint quando houver mudanca de contrato.
- Definir schema de resposta com validacao automatizada se APIs crescerem.
