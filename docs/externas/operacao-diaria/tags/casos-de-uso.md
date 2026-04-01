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

## UC-TAG-04: Excluir tag (logico)

### Objetivo

Marcar tag como excluida sem remover historico.

### Passo a passo

1. Abra a tag em edicao.
2. Clique em Excluir tag.
3. Confirme.

### Resultado esperado

Tag marcada como excluida e removida da listagem padrao.
