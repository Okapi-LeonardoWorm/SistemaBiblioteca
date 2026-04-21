# Backup Service

## Objetivo

Documentar a arquitetura e o comportamento do modulo de backup, incluindo execucao local, fila de upload para Google Drive e recuperacao automatica de pasta.

## Fontes de verdade no codigo

- app/services/backup_service.py
- app/routes/backups.py
- app/templates/backups.html
- populate_configs.py

## Visao geral do fluxo (offline-first)

1. Executar backup local:
   - Funcao: create_local_backup_now
   - Gera dump, compacta em zip, calcula hash, grava BackupRun com status success ou failed.
2. Enfileirar upload:
   - Cria registro em BackupUpload com status pending.
3. Processar fila:
   - Funcao: process_pending_drive_uploads_once
   - Seleciona itens pendentes/falhos elegiveis, tenta upload e atualiza status.
4. Reprocessar automaticamente:
   - Em falha, incrementa retryCount, define nextRetryAt e salva lastError.

## Integracao Google OAuth

### Montagem da URL de autorizacao

- Funcao: build_google_oauth_authorize_url
- Requer configuracoes:
  - BACKUP_GOOGLE_OAUTH_CLIENT_ID
  - BACKUP_GOOGLE_OAUTH_CLIENT_SECRET
  - BACKUP_GOOGLE_OAUTH_REDIRECT_URI (pode usar callback automatico se vazio na tela)
  - BACKUP_GOOGLE_OAUTH_SCOPES

### Troca do codigo por token

- Funcao: exchange_google_oauth_code
- Salva access token/refresh token em OAuthCredential (criptografado).
- Faz provisionamento oportunista de pasta via ensure_google_drive_backup_folder_id.
- Se provisionamento falhar nesse ponto, o envio tenta novamente durante o processamento da fila.

## Gerenciamento de pasta no Google Drive

### Configuracoes relacionadas

- BACKUP_GOOGLE_DRIVE_FOLDER_ID
- BACKUP_GOOGLE_DRIVE_FOLDER_NAME (default: Backups_Sistema_Biblioteca)
- BACKUP_GOOGLE_DRIVE_AUTO_CREATE_FOLDER (default: 1)
- BACKUP_GOOGLE_DRIVE_FOLDER_RECOVERY_MODE (auto_replace_invalid|strict)

### Funcao principal

- ensure_google_drive_backup_folder_id(access_token, actor_user_id)

Comportamento:

1. Se folder_id configurado e valido, reutiliza.
2. Se invalido:
   - strict: lanca erro e interrompe.
   - auto_replace_invalid: tenta buscar pasta por nome e criar se necessario.
3. Atualiza BACKUP_GOOGLE_DRIVE_FOLDER_ID com o valor resolvido.

## Retry e falhas de upload

- Funcao: next_retry_delay_minutes
- Politica: backoff exponencial com teto configuravel.
- Campos usados:
  - BACKUP_RETRY_BASE_MINUTES (default 10)
  - BACKUP_RETRY_MAX_MINUTES (default 1440)

Em qualquer falha de envio:

- status -> failed
- retryCount += 1
- nextRetryAt -> agora + atraso calculado
- lastError -> mensagem detalhada

## Erros operacionais frequentes

- Google Drive nao conectado.
- Falha ao obter token Google.
- Falha ao resolver pasta de backup no Google Drive.
- Arquivo local indisponivel para upload.
- Falha no envio ao Google Drive.

## API publica exportada pelo modulo de servicos

- create_local_backup_now
- process_pending_drive_uploads_once
- process_due_schedules_once
- exchange_google_oauth_code
- disconnect_google_oauth
- ensure_google_drive_backup_folder_id
- upsert_backup_config_value

## Observacoes de manutencao

- A documentacao externa para operador deve refletir os mesmos nomes de status exibidos na tela.
- Mudanca em mensagens de erro exige revisao em docs/externas/operacao-diaria/backup/troubleshooting.md.
- Mudanca em configuracoes BACKUP_* exige revisao em docs/externas/operacao-diaria/backup/configuracoes-e-preenchimento.md.
