# Backref de Historicos e Listagens Relacionadas (Frontend)

## Objetivo

Documentar o padrao reutilizavel de historicos e listagens relacionadas usado nos modais de Usuarios, Livros e Tags, com filtros consistentes e abertura de modais de edicao reutilizados.

## Fonte principal

- app/static/js/management.js
- app/templates/users.html
- app/templates/livros.html
- app/templates/_user_form.html
- app/templates/_book_form.html
- app/templates/palavras_chave.html
- app/templates/_keyword_form.html

## Componentes principais

1. initLoanModalWorkflow(options)
   - Inicializa o modal reutilizado de emprestimo (carregamento de formulario, salvar, retorno, cancelamento).
2. openLoanModal(loanId, options)
   - Abre modal de emprestimo para um item de historico, fechando modal pai quando necessario.
3. initBookModalWorkflow(options)
   - Inicializa modal reutilizado de livro (carregamento de formulario, salvar, soft delete/reativacao).
4. openBookModal(bookId, options)
   - Abre modal de livro para item de listagem relacionada, fechando modal pai quando necessario.
5. initUserLoanHistoryBackref(options)
   - Historico no modal de usuario.
6. initBookLoanHistoryBackref(options)
   - Historico no modal de livro.
7. initKeywordBookBackref(options)
   - Listagem de livros relacionados a tag no modal de tags.

## Contrato de integracao (HTML)

Cada painel de historico deve conter os elementos com data-attributes abaixo:

- data-history-summary="borrowed"
- data-history-summary="returned"
- data-history-search
- data-history-status-menu
- data-history-status-label
- data-history-rows
- data-history-empty

Sem esse contrato, o inicializador retorna sem montar eventos.

Para a listagem de livros por tag, o contrato esperado e:

- data-keyword-books-total
- data-keyword-book-search
- data-keyword-book-rows
- data-keyword-book-empty

## Filtros e comportamento

- Dropdown de status:
  - opcao Todos
  - selecao multipla por status
- Busca textual com debounce (300ms)
- Requisicoes para APIs internas:
  - /api/users/<id>/loan-history
  - /api/books/<id>/loan-history
   - /api/keywords/<id>/book-history

Na listagem de tags nao ha dropdown de status; apenas busca textual por livro e autor.

## Renderizacao e UX

- Linhas do historico sao clicaveis e abrem o modal de emprestimo existente.
- Linhas da listagem de livros por tag sao clicaveis e abrem o modal de livro existente.
- Datas sao formatadas em pt-BR.
- Status usa badge por classe:
  - ACTIVE -> sucesso
  - OVERDUE -> perigo
  - demais -> secundario
- Campos longos usam truncamento com fade-hover-text + data-full.
- Tooltip de hover e reinicializado apos render dinamica.

## Reuso para novas telas

Para criar historico ou listagem relacionada em outra entidade:

1. Criar endpoint com contrato equivalente (summary, status_options, items).
2. Reutilizar o workflow/modal adequado (emprestimo ou livro).
3. Criar inicializador especifico com o mesmo contrato de data-attributes.
4. Manter filtros e comportamento de listagem consistentes.

## Riscos e pontos de atencao

1. Duplicacao de logica em initUserLoanHistoryBackref e initBookLoanHistoryBackref:
   - avaliar extracao de nucleo comum quando houver terceiro historico.
2. Tooltips em conteudo dinamico:
   - sempre chamar initDelayedHoverTooltips apos atualizar linhas.
3. Alteracao de contrato da API:
   - sincronizar documentacao e inicializadores no mesmo ciclo.
