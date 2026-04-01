# Auditoria e Rastreabilidade

## Objetivo

Explicar como o sistema gera trilha de auditoria automaticamente e como registrar eventos manuais.

## Fonte principal

- app/audit.py
- app/models.py (entidade AuditLog)
- app/__init__.py (registro de listeners)

## Mecanismo automatico

Listeners SQLAlchemy sao registrados para modelos (exceto AuditLog):

- after_insert -> acao CREATE
- after_update -> acao UPDATE
- after_delete -> acao DELETE

Cada evento tenta registrar:

- timestamp
- user_id (quando disponivel)
- action
- target_type
- target_id
- changes (JSON serializado)

## Reducao de ruido

Para evitar logs tecnicos sem valor de negocio, campos de trilha como lastUpdate, updatedBy, creationDate e createdBy sao ignorados em diffs de alteracao.

## Registro manual

A funcao log_manual_event permite registrar eventos que nao derivam diretamente do ciclo ORM (ex.: LOGIN, operacoes sistemicas).

## Limitacoes conhecidas

- Falhas na serializacao convertem para string como fallback.
- Se ocorrer erro no commit de log manual, ha rollback local com mensagem de erro.
- Eventos sem alteracao efetiva podem ser ignorados em updates.

## Investigacao de inconsistencias

1. Confirmar se listeners foram registrados na inicializacao.
2. Verificar se o modelo possui __tablename__ e herda db.Model.
3. Verificar se a mudanca realmente alterou valor de atributo.
4. Confirmar contexto de usuario autenticado para preencher user_id.

## Boas praticas para evolucao

- Evitar registrar informacao sensivel em changes.
- Manter padrao de action e target_type previsivel para analise posterior.
- Atualizar esta documentacao quando novos tipos de evento manual forem introduzidos.
