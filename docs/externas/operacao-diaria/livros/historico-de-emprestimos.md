# Historico de Emprestimos no Livro

## Objetivo

Consultar em detalhes os emprestimos de um livro e abrir rapidamente a edicao de um emprestimo especifico.

## Quando usar

- Para verificar quem retirou o livro e em qual periodo.
- Para localizar um emprestimo especifico sem navegar pela listagem geral de emprestimos.

## Pre-requisitos

- Estar logado.
- Abrir um livro existente em modo edicao.

## Passo a passo

1. Acesse Gerenciar Livros.
2. Abra o livro desejado.
3. No modal, selecione a aba Historico.
4. Veja o mini dashboard:
   - Retiradas
   - Devolucoes
5. Use os filtros:
   - Status (Todos ou selecao multipla)
   - Busca por nome ou codigo do usuario
6. Clique em uma linha para abrir o modal de edicao do emprestimo.

## Colunas exibidas

- Codigo do usuario
- Nome completo
- Data de emprestimo
- Data de retorno
- Status do emprestimo

## Erros comuns e como resolver

1. Historico vazio para livro com movimentacao:
   - limpe filtros de status e busca.
2. Nao encontro o usuario:
   - tente buscar por codigo e por parte do nome.
3. Codigo ou nome cortado com ...:
   - passe o mouse sobre o texto para ver o valor completo.

## Resultado esperado

Historico carregado com as colunas corretas, filtros funcionando e abertura da edicao do emprestimo ao clicar na linha.
