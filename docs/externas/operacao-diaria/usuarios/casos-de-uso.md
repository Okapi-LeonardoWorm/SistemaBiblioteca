# Casos de Uso - Usuarios

## UC-USU-01: Cadastrar usuario

### Objetivo

Criar um novo usuario para acesso e operacao no sistema.

### Quando usar

Quando uma pessoa precisa passar a usar o sistema (aluno, colaborador, bibliotecario ou admin).

### Pre-requisitos

- Estar logado.
- Acessar a tela Gerenciar Usuarios.

### Passo a passo

1. Clique em Novo Usuario.
2. Preencha os campos obrigatorios.
3. Revise os dados.
4. Clique em Salvar.

### Como preencher os campos

- Tipo de Usuario: selecione perfil correto (aluno, colaborador, bibliotecario, admin).
- Codigo de Identificacao: obrigatorio; sera usado como login; minimo de 3 caracteres.
- Nome completo: obrigatorio.
- Senha: opcional no formulario de usuarios; se vazio, o sistema define senha padrao.
- Data de Nascimento: obrigatoria ao criar.
- Telefone: opcional; informe com DDD; 10 ou 11 digitos.
- CPF: opcional; 11 digitos.
- RG: opcional; entre 7 e 14 digitos.
- Serie e Turma: preencher para aluno.
- Responsaveis e telefones: preencher para aluno quando aplicavel.
- Observacoes: opcional.
- PCD: marque quando aplicavel.

### Erros comuns e como resolver

- Codigo de identificacao ja existe: use outro codigo unico.
- Data de nascimento vazia: preencher antes de salvar.
- Telefone invalido: informar DDD + numero com 10 ou 11 digitos.
- CPF invalido: informar 11 digitos.

### Resultado esperado

Usuario criado com sucesso e visivel na lista.

## UC-USU-02: Editar usuario

### Objetivo

Atualizar dados de um usuario ja existente.

### Quando usar

Quando houver mudanca de dados cadastrais, perfil ou informacoes complementares.

### Pre-requisitos

- Usuario deve existir na lista.

### Passo a passo

1. Na lista, clique sobre o usuario.
2. Edite os campos necessarios.
3. Para manter senha atual, deixe campo senha em branco.
4. Clique em Salvar.

### Historico de emprestimos no modal

- Na edicao de usuario, use a aba Historico para consultar retiradas e devolucoes.
- O mini dashboard mostra:
  - Livros retirados
  - Livros devolvidos
- Filtros disponiveis:
  - Dropdown de status com opcao Todos e selecao multipla
  - Busca por nome do livro
- Ao clicar em uma linha do historico, o sistema abre o modal de edicao do emprestimo correspondente.

### Como preencher os campos

- Mesmas regras do cadastro.
- Data de nascimento pode ficar opcional na edicao.
- Senha so muda se voce preencher o campo.

### Erros comuns e como resolver

- Codigo de identificacao duplicado: troque para um valor unico.
- Erros de formato em telefone/CPF/RG: ajustar para o padrao aceito.

### Resultado esperado

Dados atualizados e refletidos na tabela.

## UC-USU-03: Excluir usuario (logico)

### Objetivo

Retirar usuario da operacao sem apagar historico.

### Quando usar

Quando o usuario nao deve mais usar o sistema, mas o historico deve ser preservado.

### Pre-requisitos

- Abrir usuario em modo edicao.

### Passo a passo

1. Abra o usuario.
2. Clique em Excluir usuario.
3. Confirme a acao.

### Erros comuns e como resolver

- Botao nao aparece: verifique se esta editando um registro existente.

### Resultado esperado

Usuario marcado como excluido.

## UC-USU-04: Reativar usuario

### Objetivo

Recolocar em operacao um usuario marcado como excluido.

### Quando usar

Quando um usuario volta a precisar de acesso.

### Pre-requisitos

- Exibir usuarios excluidos nos filtros (Incluir excluidos).

### Passo a passo

1. Na tela de usuarios, marque Incluir excluidos.
2. Abra o usuario marcado como excluido.
3. Clique em Reativar usuario.
4. Confirme a acao.

### Erros comuns e como resolver

- Usuario nao encontrado na lista: aplicar filtro Incluir excluidos.

### Resultado esperado

Usuario volta ao estado ativo e aparece normalmente na listagem padrao.

## UC-USU-05: Importar usuarios em massa

### Objetivo

Cadastrar varios usuarios em uma unica operacao por arquivo.

### Quando usar

Quando houver grande volume de usuarios para cadastrar.

### Pre-requisitos

- Estar logado com perfil autorizado.
- Acessar Gerenciar Usuarios.

### Passo a passo

1. Na tela de usuarios, abra Acoes > Importar usuarios em massa.
2. Selecione o tipo de usuario para o lote.
3. Baixe o modelo (CSV ou XLSX).
4. Preencha o arquivo conforme as colunas obrigatorias do tipo selecionado.
5. Envie o arquivo na tela de upload.
6. Acompanhe o progresso.
7. Ao final, revise o resultado e baixe a planilha de erros, se existir.

### Erros comuns e como resolver

- Tipo de usuario invalido: voltar e escolher um tipo permitido.
- Formato invalido: usar apenas CSV ou XLSX.
- Campos obrigatorios faltando: corrigir o arquivo conforme o modelo.

### Resultado esperado

Usuarios validos importados e inconsistencias registradas para correcao.
