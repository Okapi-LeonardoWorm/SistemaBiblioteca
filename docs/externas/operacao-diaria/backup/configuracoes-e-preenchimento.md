# Configuracoes e Preenchimento - Backup

## Objetivo

Explicar quais configuracoes sao necessarias para o backup funcionar e como preencher os campos da tela.

## Configuracoes principais

### OAuth e Drive

- BACKUP_GOOGLE_OAUTH_CLIENT_ID
  - Obrigatoria para conectar Google.
- BACKUP_GOOGLE_OAUTH_CLIENT_SECRET
  - Obrigatoria para conectar Google.
- BACKUP_GOOGLE_OAUTH_REDIRECT_URI
  - URL de callback OAuth.
- BACKUP_GOOGLE_OAUTH_SCOPES
  - Escopo recomendado: https://www.googleapis.com/auth/drive.file
- BACKUP_GOOGLE_DRIVE_FOLDER_ID
  - Opcional; se vazio, sistema resolve automaticamente.
- BACKUP_GOOGLE_DRIVE_FOLDER_NAME
  - Nome da pasta gerenciada (default: Backups_Sistema_Biblioteca).
- BACKUP_GOOGLE_DRIVE_AUTO_CREATE_FOLDER
  - Ativa auto criacao de pasta (default: 1).
- BACKUP_GOOGLE_DRIVE_FOLDER_RECOVERY_MODE
  - auto_replace_invalid ou strict.

### Retry de upload

- BACKUP_RETRY_BASE_MINUTES (default 10)
- BACKUP_RETRY_MAX_MINUTES (default 1440)

## Exemplo completo (credenciais + agendamento)

### Credenciais Google

- Client ID: 1234567890-abc123def456.apps.googleusercontent.com
- Client Secret: GOCSPX-ExemploSecret123
- Redirect URI: http://localhost:5000/backups/google/callback
- Drive Folder ID: (vazio)
- Scopes: https://www.googleapis.com/auth/drive.file

### Agendamento

- Nome: Backup_Noturno
- Frequencia: weekly
- Horario: 22:00
- Dias semana: 1,2,3,4,5
- Timezone: America/Sao_Paulo
- Ativo: marcado

## Recomendacao operacional

- Ambiente comum: usar auto_replace_invalid para reduzir parada operacional.
- Ambiente com controle rigoroso: usar strict e gerenciar folder_id manualmente.

## Checklist rapido

1. Credenciais salvas.
2. Conexao Google ativa.
3. Pasta gerenciada exibida.
4. Backup manual executado com sucesso.
5. Upload com status uploaded.
