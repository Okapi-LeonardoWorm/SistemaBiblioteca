# Migracao de Login por Codigo ou Email

## Objetivo

Registrar o racional tecnico e o impacto operacional da migracao que consolidou o login por codigo ou email com comparacao case-insensitive.

## Fonte principal

- migrations/versions/7c9e2d1f4a6b_normalize_identification_code_for_login.py
- app/routes/auth.py
- app/forms.py
- app/routes/users.py
- app/services/user_bulk_create_service.py

## Escopo da migracao

A revisao `7c9e2d1f4a6b` faz:

1. Normalizacao de `users.identificationCode` para minusculas.
2. Resolucao de conflitos legados de caixa (ex.: `ALUNO001` vs `aluno001`).
3. Garantia de compatibilidade com tamanho de ate 150 caracteres.

## Estrategia de resolucao de conflito

Quando dois registros colidem apos normalizacao para minusculas, a migracao:

1. Calcula um valor final unico por usuario.
2. Aplica atualizacao em duas fases para evitar violacao de unique no meio do processo:
   - Fase 1: move para um valor temporario unico.
   - Fase 2: aplica o valor final normalizado.
3. Se necessario, anexa sufixo `__<userId>` ao identificador final para manter unicidade.

Exemplo:

- Antes: `ALUNO001` (userId 10) e `aluno001` (userId 18)
- Depois: `aluno001` (userId 10) e `aluno001__18` (userId 18)

## Impacto esperado

- Login passa a aceitar codigo ou email sem diferenciar maiusculas/minusculas.
- Um subconjunto de usuarios legados pode ter tido o identificador alterado para manter unicidade.
- Fluxos de criacao, edicao e importacao passam a persistir identificador em minusculas.

## Checklist pos-migracao

1. Confirmar revisao atual em `alembic_version`.
2. Auditar usuarios com sufixo de resolucao (`__<userId>`).
3. Comunicar equipe operacional sobre possiveis ajustes de credencial afetada.
4. Validar login em cenarios:
   - codigo simples
   - email
   - variacao de caixa

## Troubleshooting

1. Falha por conflito de unique durante migracao:
   - Validar se a revisao aplicada e a versao final com estrategia em duas fases.
2. Usuario relata que nao consegue logar com identificador antigo:
   - Verificar se houve sufixo de resolucao por conflito legado.
3. Resultado de login inconsistente entre ambientes:
   - Confirmar que todos os ambientes executaram a mesma revisao de migracao.
