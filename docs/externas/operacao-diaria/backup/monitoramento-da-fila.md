# Monitoramento da Fila de Upload

## Objetivo

Explicar como acompanhar os envios para Google Drive e interpretar tentativas/erros.

## Onde acompanhar

Tela: Gestao de Backup > tabela Ultimos Backups.

## Colunas importantes

- Upload Drive: status do envio (pending, uploading, uploaded, failed).
- Tentativas: quantidade de tentativas realizadas.
- Proxima Tentativa: quando o sistema tentara novamente.
- ID Remoto: id do arquivo criado no Google Drive.
- Erro Upload: mensagem detalhada da ultima falha.

## Significado dos status

- pending: aguardando processamento.
- uploading: envio em andamento.
- uploaded: envio concluido.
- failed: tentativa falhou, aguardando novo ciclo.

## Acao manual

Botao: Processar Fila Drive Agora

Quando usar:

- apos corrigir credenciais
- apos reconectar Google
- apos ajuste de pasta/permissao

## Validacao de sucesso

1. Status uploaded.
2. ID Remoto preenchido.
3. Erro Upload vazio.
