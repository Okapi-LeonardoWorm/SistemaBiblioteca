# Recovery Mode da Pasta no Drive

## Objetivo

Explicar como o sistema reage quando o folder_id salvo esta invalido.

## Configuracao

Chave: BACKUP_GOOGLE_DRIVE_FOLDER_RECOVERY_MODE

Valores:

- auto_replace_invalid
- strict

## Modo auto_replace_invalid

Comportamento:

1. Detecta folder_id invalido.
2. Tenta localizar pasta por nome (BACKUP_GOOGLE_DRIVE_FOLDER_NAME).
3. Se nao achar, cria pasta automaticamente (se auto create ativo).
4. Atualiza folder_id salvo.

Quando usar:

- operacao diaria comum
- ambientes com menor equipe tecnica
- prioridade em continuidade

## Modo strict

Comportamento:

- Se folder_id estiver invalido, falha e nao substitui automaticamente.

Quando usar:

- ambientes com controle rigido
- exigencia de pasta fixa auditada

## Recomendacao pratica

- Producao operacional: auto_replace_invalid.
- Cenarios de compliance estrito: strict com monitoramento frequente.
