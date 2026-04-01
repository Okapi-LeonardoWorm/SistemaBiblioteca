# Processamento em Lote

## Objetivo

Documentar o mecanismo de jobs em memoria para operacoes de importacao em lote e seu contrato tecnico.

## Fonte principal

- app/services/bulk_jobs.py
- app/services/book_bulk_create_service.py
- app/services/user_bulk_create_service.py

## Componentes base

1. create_job(owner_user_id, kind, metadata):
   - Cria identificador unico e estado inicial do job.
2. update_job(job_id, **fields):
   - Atualiza status, progresso, resumo e metadados do job.
3. add_job_message(job_id, message):
   - Acrescenta mensagens de acompanhamento.
4. get_job(job_id):
   - Recupera estado atual.

## Estrutura de estado do job

- jobId
- ownerUserId
- kind
- status
- progress
- createdAt
- updatedAt
- metadata
- summary:
  - totalRows
  - processedRows
  - successRows
  - errorRows
- errorReportPath
- messages

## Controle de concorrencia

- Dicionario global em memoria protegido por Lock de thread.
- Adequado para processo unico.
- Em escalas multi-processo/multi-instancia, requer backend compartilhado (ex.: Redis, banco ou fila).

## Riscos e limites

- Estado em memoria e perdido ao reiniciar processo.
- Nao oferece historico duravel por padrao.
- Nao adequado para alta concorrencia distribuida.

## Boas praticas de evolucao

- Definir padrao fechado de status (queued, running, completed, failed).
- Garantir idempotencia de operacoes de importacao.
- Persistir relatorios de erro quando houver impacto operacional.
- Planejar migracao para armazenamento compartilhado se houver necessidade de escalabilidade horizontal.
