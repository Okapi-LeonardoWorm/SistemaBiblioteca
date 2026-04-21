# Setup Google Drive para Backup

## Objetivo

Configurar a integracao com Google Drive para envio automatico dos backups.

## Pre-requisitos

- Perfil administrador no sistema.
- Acesso ao projeto no Google Cloud Console.

## Links necessarios

- Google Cloud Console: https://console.cloud.google.com/
- Tela de consentimento OAuth: https://console.cloud.google.com/apis/credentials/consent
- Credenciais OAuth (Client ID/Secret): https://console.cloud.google.com/apis/credentials

## Passo a passo

1. No Google Cloud, selecione o projeto usado pelo sistema.
2. Configure a tela de consentimento OAuth (se ainda nao existir).
3. Crie credenciais OAuth Client ID (tipo Web application).
4. Em Authorized redirect URIs, informe a URL de callback do sistema.
5. Copie Client ID e Client Secret.
6. No sistema, abra a tela Gestao de Backup.
7. Preencha os campos Google Drive e clique em Salvar Credenciais Google.
8. Clique em Conectar Google.
9. Autorize o acesso na conta Google.

## Como preencher os campos

- Client ID: valor gerado no Google Cloud.
- Client Secret: valor gerado no Google Cloud.
- Redirect URI: URL de callback do sistema.
  - Se deixar vazio, o sistema tenta callback automatico.
- Drive Folder ID: opcional.
  - Se vazio, o sistema busca/cria pasta automaticamente com o nome configurado.
- Scopes: manter padrao https://www.googleapis.com/auth/drive.file, salvo necessidade especifica.

## Exemplo de preenchimento

- Client ID: 1234567890-abc123def456.apps.googleusercontent.com
- Client Secret: GOCSPX-ExemploSecret123
- Redirect URI: http://localhost:5000/backups/google/callback
- Drive Folder ID: (vazio)
- Scopes: https://www.googleapis.com/auth/drive.file

## Como validar

1. Verificar badge Conectado na tela.
2. Verificar badge Pronto para conectar ativo.
3. Executar um backup manual e processar fila.
4. Confirmar que ID Remoto foi preenchido na tabela.
