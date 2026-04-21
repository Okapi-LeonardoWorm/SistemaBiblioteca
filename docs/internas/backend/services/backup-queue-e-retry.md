# Backup Queue e Retry

## Objetivo

Descrever o comportamento da fila de upload para Google Drive, estados, politica de retry e criterios de processamento.

## Modelo principal

Entidade: BackupUpload

Campos operacionais relevantes:

- status
- retryCount
- nextRetryAt
- lastError
- remoteFileId
- uploadedAt

## Estados da fila

- pending: item aguardando processamento.
- uploading: envio em andamento.
- uploaded: envio concluido com sucesso.
- failed: envio falhou, aguardando proxima tentativa.

## Selecao de itens para processamento

Funcao: process_pending_drive_uploads_once(limit)

Criterios:

1. provider == google_drive
2. status em [pending, failed]
3. nextRetryAt vazio ou menor/igual ao horario atual
4. ordenacao por creationDate asc
5. limite por parametro limit

## Politica de retry

Funcao: next_retry_delay_minutes(retry_count)

- Formula base: base_minutes * (2 ** retry_count)
- Limites:
  - base minimo = 1
  - maximo >= base
- Valor final limitado por BACKUP_RETRY_MAX_MINUTES

Configuracoes:

- BACKUP_RETRY_BASE_MINUTES (default 10)
- BACKUP_RETRY_MAX_MINUTES (default 1440)

## Centralizacao de falhas

Funcao: _mark_upload_failed(item, message)

Acoes:

1. status = failed
2. retryCount incrementado
3. nextRetryAt recalculado
4. lastError atualizado
5. commit imediato

## Falhas por etapa

- Sem credencial Google:
  - marca todos os itens selecionados como failed.
- Falha ao obter token:
  - marca todos os itens selecionados como failed.
- Falha ao resolver pasta:
  - marca todos os itens selecionados como failed.
- Falha por arquivo local inexistente:
  - marca item individual como failed.
- Falha no upload HTTP:
  - marca item individual como failed.

## Observabilidade na tela

A tela de backup mostra por item:

- Upload Drive (status)
- Tentativas (retryCount)
- Proxima Tentativa (nextRetryAt)
- ID Remoto (remoteFileId)
- Erro Upload (lastError)

## Diretrizes de evolucao

- Preservar semantica dos estados para nao quebrar orientacoes externas.
- Qualquer alteracao na politica de retry deve atualizar docs externas e testes unitarios.
- Em mudancas de mensagens de erro, revisar troubleshooting externo.
