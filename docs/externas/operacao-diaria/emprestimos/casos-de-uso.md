# Casos de Uso - Emprestimos

## UC-EMP-01: Cadastrar emprestimo

### Objetivo

Registrar um novo emprestimo de livro para usuario.

### Quando usar

Quando um livro for retirado por um usuario.

### Pre-requisitos

- Estar em Gerenciar Emprestimos.
- Definir periodo do emprestimo (data de emprestimo e data de devolucao).

### Passo a passo

1. Clique em Novo Emprestimo.
2. Informe Data de Emprestimo e Data de Devolucao.
3. Busque e selecione o Usuario.
4. Busque e selecione o Livro.
5. Informe Quantidade.
6. Preencha Observacao inicial (opcional).
7. Clique em Salvar.

### Como preencher os campos

- Data de Emprestimo: obrigatorio.
- Data de Devolucao: obrigatorio; nao pode ser anterior a data de emprestimo.
- Usuario: selecionar pela busca por nome ou codigo.
- Livro: selecionar pela busca por nome/autor/editora.
- Quantidade: minimo 1 e respeita disponibilidade no periodo.
- Observacao inicial: opcional.

### Erros comuns e como resolver

- Nao consigo selecionar usuario/livro: preencher primeiro as datas.
- Livro indisponivel: ajustar periodo ou quantidade.
- Data de devolucao invalida: informar data igual ou posterior a de emprestimo.

### Resultado esperado

Emprestimo criado com status ativo.

## UC-EMP-02: Editar emprestimo

### Objetivo

Atualizar dados permitidos de um emprestimo.

### Quando usar

Quando for necessario ajustar devolucao prevista ou observacoes permitidas.

### Passo a passo

1. Clique no emprestimo na lista.
2. Altere os campos permitidos.
3. Clique em Salvar.

### Entradas alternativas para abrir a edicao

- Alem da tela Gerenciar Emprestimos, a edicao tambem pode ser aberta pelos historicos:
   - Aba Historico no modal de edicao de usuario
   - Aba Historico no modal de edicao de livro

### Regras importantes

- Livro, usuario, quantidade e data inicial nao sao alterados nesta edicao.
- Data de devolucao pode ser alterada, respeitando regra de data.
- Observacoes podem ter restricao de edicao conforme status e politica do sistema.

### Erros comuns e como resolver

- Alteracao bloqueada em observacao: verificar se emprestimo esta ativo/finalizado e se edicao e permitida.
- Data invalida: corrigir para data valida.

### Resultado esperado

Emprestimo atualizado com sucesso.

## UC-EMP-03: Cancelar emprestimo

### Objetivo

Cancelar emprestimo ativo dentro da regra de tempo permitida.

### Quando usar

Quando o emprestimo foi criado por engano ou precisa ser anulado rapidamente.

### Passo a passo

1. Abra o emprestimo.
2. Em Acoes, clique em Cancelar (quando disponivel).
3. Confirme.

### Regras importantes

- Somente emprestimo ativo pode ser cancelado.
- Existe limite de tempo para cancelamento definido no sistema.

### Erros comuns e como resolver

- Opcao Cancelar nao aparece: prazo pode ter expirado ou status nao e ativo.
- Cancelamento negado: revisar tempo limite e status.

### Resultado esperado

Emprestimo marcado como cancelado.

## UC-EMP-04: Informar retorno

### Objetivo

Finalizar emprestimo com retorno do livro ou registro de perda.

### Quando usar

Quando livro retorna ou quando houve perda.

### Passo a passo

1. Abra o emprestimo.
2. Em Acoes, clique em Informar retorno.
3. Informe Data de retorno.
4. Selecione Situacao:
   - Concluido
   - Livro perdido
5. Preencha Observacao final (opcional).
6. Confirme retorno.

### Regras importantes

- Emprestimo finalizado nao pode ser finalizado novamente.
- Data de retorno nao pode ser anterior a data de emprestimo.
- Se situacao for Livro perdido, o estoque do livro sera reduzido.

### Erros comuns e como resolver

- Status invalido: selecionar apenas Concluido ou Livro perdido.
- Estoque insuficiente para perda: revisar quantidade do emprestimo e estoque atual.

### Resultado esperado

Emprestimo finalizado com status correto e historico preservado.

## UC-EMP-05: Exclusao de emprestimo

### Objetivo

Esclarecer politica atual do sistema para exclusao.

### Regra atual

A exclusao de emprestimos esta desativada no sistema.

### Orientacao

Use os fluxos de Cancelar ou Informar retorno para encerrar o ciclo corretamente.
