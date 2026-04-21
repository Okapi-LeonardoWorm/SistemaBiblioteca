# Troubleshooting de Backup

## Objetivo

Resolver falhas comuns de backup e upload no Google Drive.

## Falhas e acoes

### Erro: Google Drive nao conectado

Acao:

1. Verifique Client ID e Client Secret.
2. Salve credenciais novamente.
3. Clique em Conectar Google.
4. Reprocese a fila.

### Erro: Falha ao obter token Google

Acao:

1. Desconecte Google.
2. Conecte novamente.
3. Verifique Redirect URI no Google Cloud e no sistema.

### Erro: Falha ao resolver pasta de backup no Google Drive

Acao:

1. Verifique se a pasta existe e nao esta na lixeira.
2. Verifique permissao da conta conectada.
3. Se usar folder_id manual, confirme se e de pasta (nao de arquivo).
4. Reprocese a fila.

### Erro: Arquivo local indisponivel para upload

Acao:

1. Execute novo backup manual.
2. Verifique se houve sucesso no backup local.
3. Reprocese a fila.

### Erro: Falha no envio ao Google Drive

Acao:

1. Verifique conectividade e permissao no Drive.
2. Aguarde proxima tentativa automatica.
3. Se necessario, use Processar Fila Drive Agora.

## Roteiro rapido de recuperacao

1. Confirmar conexao Google (badge Conectado).
2. Confirmar pasta gerenciada e modo de recuperacao.
3. Executar backup manual.
4. Processar fila.
5. Confirmar status uploaded e ID Remoto.
