# Blueprints e Endpoints

## Objetivo

Documentar a organizacao de interface HTTP por blueprint e orientar evolucao segura de rotas.

## Fonte principal

- app/routes/__init__.py
- app/routes/*.py

## Blueprints registrados

- auth
- navigation
- books
- loans
- keywords
- users
- configs
- apis
- audit_logs
- admin_sessions

## Responsabilidades por dominio

1. auth:
   - login, logout, registro e rotas de autenticacao.
2. navigation:
   - navegacao principal e dashboard.
3. books:
   - CRUD e busca de livros.
4. loans:
   - operacoes de emprestimo, retorno e cancelamento.
5. keywords:
   - gestao de palavras-chave.
6. users:
   - gestao de usuarios e validacoes de identificacao.
7. configs:
   - configuracoes funcionais do sistema.
8. apis:
   - endpoints de consulta para integracoes/client-side.
9. audit_logs:
   - consulta de trilha de auditoria.
10. admin_sessions:
   - administracao de sessoes ativas.

## Aliases legados

O sistema mantem mapeamento de endpoints antigos main.* para endpoints atuais por blueprint.

Objetivo: preservar compatibilidade retroativa em templates, links e integracoes antigas.

## Padrao recomendado para nova rota

1. Definir responsabilidade no blueprint correto.
2. Aplicar login_required e regras de permissao conforme necessidade.
3. Validar entrada e normalizar dados de filtro/ordenacao.
4. Encapsular logica complexa em services/utils.
5. Garantir tratamento de erros com status apropriado e feedback claro.
6. Atualizar documentacao de dominio impactado.

## Riscos comuns

- Criar rota fora do dominio funcional correto.
- Acoplar regra de negocio extensa no handler HTTP.
- Romper alias legado ao renomear endpoint sem migracao.

## Checklist de revisao de endpoint

- O endpoint esta no blueprint correto?
- A autenticacao/autorizacao esta consistente?
- A resposta HTTP e coerente (template/json/status)?
- O impacto em auditoria foi considerado?
