# Casos de Uso - Livros

## UC-LIV-01: Cadastrar livro

### Objetivo

Adicionar um novo livro ao catalogo.

### Quando usar

Quando um novo titulo entra no acervo.

### Pre-requisitos

- Estar na tela Gerenciar Livros.

### Passo a passo

1. Clique em Novo Livro.
2. Preencha titulo, quantidade e demais campos.
3. Clique em Salvar.

### Como preencher os campos

- Nome do Livro: obrigatorio.
- Quantidade: obrigatorio; minimo 1.
- Autor e Editora: opcionais.
- Publicacao: escolha Ano ou Data.
  - Ano: informe ano com 4 digitos.
  - Data: selecione a data.
- Aquisicao: escolha Ano ou Data.
- Tags: opcional; separar por virgula (,) ou ponto e virgula (;).
- Descricao: opcional.

### Erros comuns e como resolver

- Quantidade invalida: usar valor inteiro maior ou igual a 1.
- Ano fora de padrao: informar ano com 4 digitos.
- Tags mal formatadas: separar corretamente por virgula ou ponto e virgula.

### Resultado esperado

Livro criado e exibido na listagem.

## UC-LIV-02: Editar livro

### Objetivo

Atualizar dados de livro existente.

### Passo a passo

1. Clique no livro na tabela.
2. Altere os campos necessarios.
3. Clique em Salvar.

### Entradas alternativas para abrir a edicao

- Alem da tela Gerenciar Livros, a edicao tambem pode ser aberta por:
  - Aba Livros no modal de edicao de Tags

### Regras importantes

- Se nada for alterado, o sistema pode informar que nao houve alteracao.
- Tags podem ser adicionadas ou removidas no mesmo formulario.

### Resultado esperado

Livro atualizado com sucesso.

### Historico de emprestimos no modal

- Na edicao de livro, use a aba Historico para consultar todos os emprestimos daquele livro.
- O mini dashboard mostra:
  - Retiradas
  - Devolucoes
- Filtros disponiveis:
  - Dropdown de status com opcao Todos e selecao multipla
  - Busca por nome ou codigo do usuario
- Colunas da listagem:
  - Codigo do usuario
  - Nome completo
  - Data de emprestimo
  - Data de retorno
  - Status
- Ao clicar em uma linha do historico, o sistema abre o modal de edicao do emprestimo correspondente.

## UC-LIV-03: Excluir livro (logico)

### Objetivo

Retirar livro da operacao sem apagar o historico.

### Passo a passo

1. Abra o livro em edicao.
2. Clique em Excluir livro.
3. Confirme a acao.

### Resultado esperado

Livro marcado como excluido.

## UC-LIV-04: Reativar livro

### Objetivo

Reativar livro que foi marcado como excluido.

### Passo a passo

1. Marque Incluir excluidos nos filtros.
2. Abra o livro excluido.
3. Clique em Reativar livro.
4. Confirme.

### Resultado esperado

Livro volta ao estado ativo.

## UC-LIV-05: Importar livros em massa

### Objetivo

Cadastrar varios livros de uma vez por arquivo.

### Quando usar

Quando houver grande volume de cadastros.

### Passo a passo

1. Na tela de livros, abra Acoes > Importar livros em massa.
2. Baixe o modelo (CSV ou XLSX).
3. Preencha o arquivo seguindo as colunas obrigatorias.
4. Envie o arquivo na tela de upload.
5. Acompanhe progresso.
6. Se houver erro, baixe a planilha de erros e corrija.

### Erros comuns e como resolver

- Formato invalido: usar apenas CSV ou XLSX.
- Coluna obrigatoria ausente: preencher conforme modelo.

### Resultado esperado

Livros validos importados, com relatorio de inconsistencias quando houver.
