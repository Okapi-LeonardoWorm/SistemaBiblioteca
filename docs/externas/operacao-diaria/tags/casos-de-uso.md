# Casos de Uso - Tags

## UC-TAG-01: Cadastrar tag unica

### Objetivo

Criar uma nova tag para classificacao de livros.

### Quando usar

Quando uma nova categoria de organizacao for necessaria.

### Passo a passo

1. Acesse Gerenciar Tags.
2. Clique em Nova Tag.
3. Digite a tag.
4. Clique em Salvar.

### Como preencher o campo

- Tag: obrigatorio.
- Evite duplicar termos com o mesmo significado.

### Erros comuns e como resolver

- Tag vazia: preencher com texto valido.
- Tag ja existente: usar outro nome ou revisar se realmente precisa criar.

### Resultado esperado

Tag criada e visivel na lista.

## UC-TAG-02: Cadastrar varias tags de uma vez

### Objetivo

Criar multiplas tags em uma unica acao.

### Passo a passo

1. Abra Nova Tag.
2. Informe varias tags separadas por virgula ou ponto e virgula.
3. Clique em Salvar.

### Exemplo

Ficcao, Aventura; Classico

### Resultado esperado

Sistema cria as novas tags e ignora as que ja existiam.

## UC-TAG-03: Editar tag

### Objetivo

Ajustar nome de uma tag existente.

### Passo a passo

1. Clique na tag na lista.
2. Altere o nome.
3. Clique em Salvar.

### Erros comuns e como resolver

- Novo nome ja existe: escolher nome diferente.

### Resultado esperado

Tag atualizada com sucesso.

### Livros no modal de edicao

- Na edicao de tag, use a aba Livros para consultar quais livros utilizam aquela tag.
- O dashboard mostra apenas:
	- Quantidade de livros
- Filtro disponivel:
	- Busca por nome do livro ou nome do autor
- Colunas exibidas:
	- Livro
	- Autor
- Ao clicar em uma linha, o sistema abre o modal de edicao do livro correspondente.

## UC-TAG-04: Excluir tag (logico)

### Objetivo

Marcar tag como excluida sem remover historico.

### Passo a passo

1. Abra a tag em edicao.
2. Clique em Excluir tag.
3. Confirme.

### Resultado esperado

Tag marcada como excluida e removida da listagem padrao.

## UC-TAG-05: Recuperacao de tag

### Objetivo

Orientar como proceder quando uma tag excluida precisa voltar a uso.

### Regra atual

Nao ha fluxo de reativacao de tag disponivel na tela operacional.

### Orientacao

1. Verifique se a tag realmente foi excluida por engano.
2. Se precisar reutilizar rapidamente, crie nova tag com nome equivalente (seguindo padrao de nomenclatura da equipe).
3. Para recuperar a tag original excluida, registrar solicitacao administrativa para tratamento no sistema.

### Resultado esperado

Equipe operacional sabe exatamente como agir mesmo sem botao de reativacao de tag.
