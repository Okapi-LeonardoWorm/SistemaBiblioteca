# Backref de Historico de Emprestimos (Frontend)

## Objetivo

Documentar o padrao reutilizavel de historico de emprestimos usado nos modais de Usuarios e Livros, com filtros consistentes e abertura do mesmo modal de edicao de emprestimo.

## Fonte principal

- app/static/js/management.js
- app/templates/users.html
- app/templates/livros.html
- app/templates/_user_form.html
- app/templates/_book_form.html

## Componentes principais

1. initLoanModalWorkflow(options)
   - Inicializa o modal reutilizado de emprestimo (carregamento de formulario, salvar, retorno, cancelamento).
2. openLoanModal(loanId, options)
   - Abre modal de emprestimo para um item de historico, fechando modal pai quando necessario.
3. initUserLoanHistoryBackref(options)
   - Historico no modal de usuario.
4. initBookLoanHistoryBackref(options)
   - Historico no modal de livro.

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

## Filtros e comportamento

- Dropdown de status:
  - opcao Todos
  - selecao multipla por status
- Busca textual com debounce (300ms)
- Requisicoes para APIs internas:
  - /api/users/<id>/loan-history
  - /api/books/<id>/loan-history

## Renderizacao e UX

- Linhas do historico sao clicaveis e abrem o modal de emprestimo existente.
- Datas sao formatadas em pt-BR.
- Status usa badge por classe:
  - ACTIVE -> sucesso
  - OVERDUE -> perigo
  - demais -> secundario
- Campos longos usam truncamento com fade-hover-text + data-full.
- Tooltip de hover e reinicializado apos render dinamica.

## Reuso para novas telas

Para criar historico relacionado em outra entidade:

1. Criar endpoint com contrato equivalente (summary, status_options, items).
2. Reutilizar initLoanModalWorkflow e openLoanModal.
3. Criar inicializador especifico com o mesmo contrato de data-attributes.
4. Manter filtros e comportamento de listagem consistentes.

## Riscos e pontos de atencao

1. Duplicacao de logica em initUserLoanHistoryBackref e initBookLoanHistoryBackref:
   - avaliar extracao de nucleo comum quando houver terceiro historico.
2. Tooltips em conteudo dinamico:
   - sempre chamar initDelayedHoverTooltips apos atualizar linhas.
3. Alteracao de contrato da API:
   - sincronizar documentacao e inicializadores no mesmo ciclo.
