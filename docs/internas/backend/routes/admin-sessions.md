# Rotas de Administracao de Sessoes (admin_sessions)

## Objetivo

Documentar o blueprint admin_sessions, responsavel por listar e revogar sessoes ativas no servidor.

## Fonte principal

- app/routes/admin_sessions.py
- app/models.py (UserSession)

## Endpoints

1. GET /admin/sessions
   - Requer login e perfil admin.
   - Lista sessoes ordenadas por ultima atividade.
   - Identifica token da sessao atual para UX administrativa.
2. POST /admin/sessions/revoke/<session_id>
   - Requer login e perfil admin.
   - Revoga sessao especifica via delete em UserSession.

## Regras de acesso

- Acesso exclusivo para current_user.userType == admin.
- Usuario sem privilegio e redirecionado com mensagem de erro.

## Comportamento operacional

- Revogacao remove registro de sessao no banco.
- Sessao revogada deixa de ser valida na verificacao de timeout/atividade.
- Mensagens de feedback sao exibidas para sucesso e sessao inexistente.

## Riscos e pontos de atencao

1. Bloqueio de sessao propria:
   - Fluxo permite revogar qualquer token; considerar restricao adicional se necessario.
2. Escalabilidade:
   - Listagem carrega todas as sessoes; avaliar paginacao em alto volume.

## Troubleshooting

1. Admin nao consegue acessar:
   - Verificar userType armazenado para conta logada.
2. Sessao nao e revogada:
   - Verificar existencia de session_id na tabela UserSession.
3. Sessao continua ativa apos revogacao:
   - Validar integracao com check_session_timeout e sincronizacao de token na sessao cliente.

## Diretriz de evolucao

- Adicionar auditoria explicita de revogacao administrativa se necessario para compliance.
- Introduzir filtros e paginacao quando o volume de sessoes crescer.
