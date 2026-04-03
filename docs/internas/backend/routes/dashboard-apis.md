# APIs do Dashboard Administrativo

## Objetivo

Documentar os contratos HTTP dos endpoints usados pela tela `dashboard.html`.

## Fonte principal

- app/routes/apis.py
- app/services/dashboard_service.py
- app/templates/dashboard.html

## Controle de acesso

- Todos os endpoints exigem `login_required`.
- O acesso funcional ao dashboard e restrito a admin na rota de tela (`/dashboard`).

## Endpoints

### GET /api/dashboard/kpis

- Retorno: totais de livros, emprestimos ativos, alunos, colaboradores e atrasos.

### GET /api/dashboard/devolucoes

- Parametros:
  - `quick_filter`: today, week, overdue, all (default: today)
  - `student`: filtro por nome/codigo do aluno
  - `serie`: repetivel
  - `turma`: repetivel
  - `page`: paginacao
  - `per_page`: paginacao
- Retorno: itens + kpis operacionais + metadados de paginacao.

### GET /api/dashboard/devolucoes/filter-options

- Retorno: opcoes de serie, turma e tipo de usuario para filtros.

### GET /api/dashboard/tags-top

- Parametros: `limit` (default 10; com limite maximo no servico)
- Retorno: tags com contagem e percentual.

### GET /api/dashboard/ultimos-emprestimos

- Parametros: `limit` (default 10)
- Retorno: timeline recente de emprestimos com tag principal do livro.

### GET /api/dashboard/engajamento

- Parametros:
  - `period`, `start_date`, `end_date`
  - `serie`, `turma` (single e repetivel)
  - `user_type` (single e repetivel)
  - `periodo`
  - `top_limit`
- Retorno: series para graficos por turma/serie/periodo e ranking de alunos.

### GET /api/dashboard/popularidade

- Parametros:
  - `start_date`, `end_date`, `range`
  - `serie`, `turma` (single e repetivel)
  - `user_type` (single e repetivel)
  - `periodo`
  - `limit`
- Retorno: top livros e distribuicao por tags.

### GET /api/dashboard/acervo

- Parametros: `days_lost`, `limit`
- Retorno: itens em risco/perdidos, contagem total e limiar aplicado.

### GET /api/dashboard/drilldown

- Parametros:
  - `source`, `label`, `key`
  - `period`, `range`
  - `serie`, `turma`, `periodo`
  - `limit`
- Retorno: lista textual de detalhamento conforme origem do grafico.

## Padrao de resposta

- Envelope JSON padrao:
  - `success`: boolean
  - `data`: payload principal

## Regras relevantes

- Filtros por serie/turma/user_type sao normalizados no servico.
- Datas invalidas usam fallback seguro.
- Algumas consultas usam cache in-memory com TTL curto/medio.
- Limites numericos sao sanitizados com teto para evitar cargas excessivas.

## Troubleshooting

- Dashboard sem dados:
  - Verificar sessao autenticada e papel admin para acesso da tela.
  - Validar parametros de filtro e janela de datas.

- Totais diferentes entre blocos:
  - Conferir regras de status de cada bloco (ex.: atrasados vs ativos).

- Drilldown vazio:
  - Validar `source`/`key` enviados pela UI e filtros ativos.
