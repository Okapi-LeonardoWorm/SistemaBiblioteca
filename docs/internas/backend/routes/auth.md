# Rotas de Autenticacao e Sessao (auth)

## Objetivo

Documentar contratos e comportamento do blueprint auth, incluindo login, logout, registro e controle de timeout de sessao.

## Fonte principal

- app/routes/auth.py
- app/models.py (User, UserSession)
- app/utils/session_utils.py

## Endpoints

1. GET / e GET /index
   - Requer login.
   - Redireciona admin para dashboard e demais usuarios para menu.
2. GET /login, POST /login
   - Nao requer login.
   - Valida credenciais por identificationCode + senha.
   - Cria sessao em flask session e registro em UserSession.
3. GET /logout
   - Requer login.
   - Registra LOGOUT, remove sessao persistida e limpa sessao local.
4. GET /register, POST /register
   - Cadastro de usuario.
   - Choices de userType variam por perfil do usuario autenticado.

## Regras de seguranca e sessao

- Hook before_app_request aplica check_session_timeout para todas as requisicoes.
- login_user(user) integra autenticacao com Flask-Login apos validacao de credenciais.
- session_token (UUID) e persistido em UserSession para gestao administrativa de sessoes.
- Em logout, token atual e removido de UserSession quando presente.

## Registro de auditoria

- LOGIN e LOGOUT sao registrados via log_manual_event.
- Falhas de auditoria nao interrompem fluxo de autenticacao.

## Riscos e pontos de atencao

1. Fallback de senha em texto puro:
   - Existe fallback para comparacao direta em ValueError (cenarios legados/testes).
   - Risco operacional se permanecer em ambiente produtivo.
2. Register aberto:
   - Endpoint de registro e publico; controle de choices reduz privilegios, mas politica de onboarding deve ser definida.
3. Silenciamento de excecoes:
   - Alguns blocos except sem logging dificultam diagnostico.

## Troubleshooting

1. Login valida formulario mas nao autentica:
   - Verificar identificationCode normalizado e hash de senha armazenado.
2. Sessao expira inesperadamente:
   - Verificar check_session_timeout e parametros de tempo de sessao.
3. Usuario continua ativo apos logout:
   - Verificar persistencia/remocao em UserSession e limpeza de session_token.

## Diretriz de evolucao

- Centralizar politica de autenticao (lockout, tentativas, MFA) em camada dedicada se introduzida.
- Evitar adicionar regra de negocio de dominio em auth.
- Qualquer mudanca de fluxo de sessao deve atualizar documentacao de admin_sessions e auditoria.
