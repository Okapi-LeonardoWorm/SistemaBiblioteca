# Rotas de Backup

## Objetivo

Documentar contratos HTTP e validacoes das rotas de backup para manutencao e troubleshooting.

## Fonte de verdade

- app/routes/backups.py

## Permissoes

- Visualizacao: can_view_backup_screen
- Edicao/acao: can_edit_backup_screen

Se o usuario nao tiver permissao, as rotas retornam redirecionamento com flash de acesso negado.

## Endpoints

### GET /backups

- Handler: backup_management
- Objetivo: renderizar tela de gestao de backup com:
  - status de conexao Google
  - credenciais configuradas
  - agendamentos
  - ultimos backups e status de upload

### POST /backups/run-now

- Handler: run_backup_now
- Objetivo: executar backup local imediato e enfileirar upload.

### POST /backups/uploads/process-now

- Handler: process_uploads_now
- Objetivo: processar itens da fila pendentes/falhos elegiveis.

### POST /backups/google/connect

- Handler: google_connect
- Objetivo: iniciar fluxo OAuth2 Google com state em sessao.

### GET /backups/google/callback e GET /callback

- Handler: google_callback
- Objetivo: validar state, receber code OAuth2 e trocar por token.
- Observacao: rota /callback existe por compatibilidade.

### POST /backups/google/disconnect

- Handler: google_disconnect
- Objetivo: remover tokens salvos e desconectar integracao.

### POST /backups/google/credentials

- Handler: save_google_credentials
- Objetivo: salvar parametros OAuth e pasta/scopes.

Validacoes de formulario:

- client_id obrigatorio
- client_secret obrigatorio
- redirect_uri opcional
- folder_id opcional
- scopes opcional (default drive.file)

### POST /backups/schedules/new

- Handler: create_schedule
- Objetivo: criar agendamento.

Validacoes:

- name obrigatorio
- frequency em [daily, weekly]
- runTime no formato HH:MM
- weekDays obrigatorio em frequency weekly

### POST /backups/schedules/<id>/update

- Handler: update_schedule
- Objetivo: editar agendamento existente.
- Reaplica as mesmas validacoes de criacao.

### POST /backups/schedules/<id>/toggle

- Handler: toggle_schedule
- Objetivo: ativar/desativar agendamento.

### POST /backups/schedules/<id>/delete

- Handler: delete_schedule
- Objetivo: excluir agendamento.

## Mensagens de retorno

As rotas usam flash para feedback ao operador, com exemplos:

- sucesso de conexao/desconexao
- sucesso de criacao/edicao/exclusao
- falhas de validacao de formulario
- falhas de integracao OAuth/Drive

## Dependencias de documentacao externa

Sempre que mudar:

- campos do formulario Google
- validacoes de agendamento
- nomes de acoes da tela
- mensagens principais de erro/sucesso

...atualizar docs em docs/externas/operacao-diaria/backup/.
