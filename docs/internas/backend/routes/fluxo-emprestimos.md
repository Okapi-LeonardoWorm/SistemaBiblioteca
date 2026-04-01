# Fluxo de Emprestimos

## Objetivo

Detalhar o fluxo de emprestimos como referencia para manutencao, depuracao e evolucao funcional.

## Fonte principal

- app/routes/loans.py
- app/models.py
- app/utils/loan_utils.py
- app/validaEmprestimo.py

## Cenarios cobertos

- Listagem com filtros simples e avancados.
- Ordenacao e paginacao.
- Inclusao e edicao de emprestimo.
- Cancelamento de emprestimo.
- Informacao de retorno e exclusao.

## Fluxo de listagem

1. Endpoint inicia query em Loan.
2. Determina joins necessarios conforme filtros e ordenacao.
3. Aplica politica de include_deleted para usuario/livro.
4. Aplica busca textual e filtros por categoria:
   - emprestimo
   - usuario
   - livro
5. Aplica distinct quando join em palavras-chave pode duplicar linhas.
6. Aplica ordenacao dinamica com fallback em data do emprestimo.
7. Pagina resultado e renderiza template com contexto completo.

## Regras importantes

- Filtros de data usam parse e intervalos com inicio/fim de dia quando necessario.
- Status de emprestimo respeita enum StatusLoan.
- Limite de cancelamento e parametrizado por configuracao de sistema.

## Decisoes de implementacao relevantes

- Join condicional melhora performance em comparacao com join sempre ativo.
- Distinct e ativado apenas quando necessario (join N:N com keywords).
- Base params preserva estado de filtro/ordenacao na navegacao.

## Troubleshooting direcionado

1. Resultado duplicado na listagem:
   - Verificar filtros de tags e aplicacao de distinct.
2. Filtro sem efeito:
   - Verificar parse de entrada (datas e inteiros).
3. Ordenacao inconsistente:
   - Verificar sort_by/sort_dir e mapa de colunas permitidas.
4. Cancelamento negado indevidamente:
   - Verificar status atual do emprestimo e configuracao de tempo limite.

## Diretriz de evolucao

- Novas regras de negocio de emprestimo devem ser extraidas para services quando ultrapassarem complexidade de orquestracao HTTP.
- Evitar duplicacao de logica de filtro entre rotas; mover funcoes reutilizaveis para camada utilitaria dedicada.
