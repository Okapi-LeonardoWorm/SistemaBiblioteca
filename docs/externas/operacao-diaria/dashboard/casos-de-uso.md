# Casos de Uso - Dashboard Administrativo

Publico alvo: administrador.

## UC-DB-01: Acompanhar indicadores gerais

### Objetivo (UC-DB-01)

Visualizar rapidamente o estado da biblioteca (acervo, emprestimos e perfis de usuarios).

### Pre-requisitos (UC-DB-01)

- Estar logado como admin.

### Passo a passo (UC-DB-01)

1. Acesse o Dashboard Administrativo.
2. Consulte os cards de KPI no topo.
3. Verifique o painel de devolucoes para prioridades do dia.

### Resultado esperado (UC-DB-01)

Visao consolidada dos principais numeros de operacao.

## UC-DB-02: Priorizar devolucoes

### Objetivo (UC-DB-02)

Filtrar e priorizar alunos/livros com devolucao para hoje, semana ou atrasada.

### Passo a passo (UC-DB-02)

1. No bloco de devolucoes, selecione um filtro rapido (Hoje, Esta semana, Todos, Atrasados).
2. Opcionalmente aplique filtros de serie e turma.
3. Use busca por aluno (nome ou codigo).
4. Navegue nas paginas da tabela.

### Resultado esperado (UC-DB-02)

Lista operacional com os casos mais urgentes e respectivos status.

## UC-DB-03: Ler engajamento e popularidade

### Objetivo (UC-DB-03)

Entender padroes de leitura por turma/serie e livros/tags mais emprestados.

### Passo a passo (UC-DB-03)

1. Defina periodo (datas) e filtros escolares (serie/turma/tipo de usuario).
2. Consulte graficos de engajamento e ranking de alunos.
3. Consulte blocos de popularidade do acervo.
4. Use o drilldown (quando disponivel) para detalhes de um ponto do grafico.

### Resultado esperado (UC-DB-03)

Insights para decisao pedagogica e planejamento de acervo.

## UC-DB-04: Monitorar saude do acervo

### Objetivo (UC-DB-04)

Identificar emprestimos em risco de extravio/perda por atraso prolongado.

### Passo a passo (UC-DB-04)

1. No bloco Saude do Acervo, ajuste dias para extravio quando necessario.
2. Revise a contagem e a lista de itens com atraso elevado.
3. Acione tratamento operacional dos casos criticos.

### Resultado esperado (UC-DB-04)

Casos de risco identificados com prioridade de acao.

## Erros comuns e como resolver

- Nao consigo abrir dashboard:
  - Verificar se o perfil e admin.

- Dados parecem desatualizados por alguns instantes:
  - Atualizar a pagina e revisar filtros; alguns blocos usam cache de curta duracao.

- Nao encontro um aluno/livro esperado:
  - Revisar filtros ativos de data, serie, turma e tipo de usuario.
