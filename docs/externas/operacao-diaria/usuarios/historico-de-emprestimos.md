# Historico de Emprestimos no Usuario

## Objetivo

Consultar em detalhes o historico de retiradas de um usuario e acessar rapidamente a edicao de um emprestimo especifico.

## Quando usar

- Para validar o historico de uso de um usuario.
- Para localizar um emprestimo especifico sem abrir primeiro a tela de emprestimos.

## Pre-requisitos

- Estar logado.
- Abrir um usuario existente em modo edicao.

## Passo a passo

1. Acesse Gerenciar Usuarios.
2. Abra o usuario desejado.
3. No modal, selecione a aba Historico.
4. Veja o mini dashboard:
   - Livros retirados
   - Livros devolvidos
5. Use os filtros:
   - Status (Todos ou selecao multipla)
   - Busca por nome do livro
6. Clique em uma linha para abrir o modal de edicao do emprestimo.

## Como interpretar a listagem

- Livro: nome do livro.
- Data retirada: data de inicio do emprestimo.
- Data devolucao: data de retorno registrada.
- Status: situacao atual do emprestimo.

## Erros comuns e como resolver

1. Historico vazio para usuario com movimentacao:
   - limpe os filtros de status e de busca.
2. Nao encontro pelo nome do livro:
   - use parte do titulo e revise acentos/ortografia.
3. Nome do livro cortado com ...:
   - passe o mouse sobre o texto para ver o nome completo.

## Resultado esperado

Historico carregado com filtros aplicados e possibilidade de abrir a edicao do emprestimo diretamente pela linha.
