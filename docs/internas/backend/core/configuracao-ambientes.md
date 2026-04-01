# Configuracao por Ambiente

## Objetivo

Descrever parametros de configuracao que impactam seguranca, comportamento de sessao, conexao com banco e testes.

## Fonte principal

- config.py

## Classes de configuracao

- Config: base para execucao normal.
- TestingConfig: especializacao para testes automatizados.

## Chaves relevantes

1. SECRET_KEY:
   - Utilizada em assinaturas e seguranca da sessao.
2. PERMANENT_SESSION_LIFETIME:
   - Tempo de vida da sessao (12 horas no padrao atual).
3. SESSION_COOKIE_HTTPONLY / SESSION_COOKIE_SECURE / SESSION_COOKIE_SAMESITE:
   - Politicas de cookie com impacto direto em seguranca.
4. SESSION_TYPE / SESSION_USE_SIGNER / SESSION_KEY_PREFIX:
   - Parametros da sessao server-side.
5. SQLALCHEMY_DATABASE_URI:
   - URI de banco para ambiente principal.
6. WTF_CSRF_ENABLED / WTF_CSRF_METHODS:
   - Protecao CSRF para metodos mutaveis.

## Diferencas de TestingConfig

- TESTING = True
- SESSION_TYPE = filesystem
- Banco dedicado para teste
- CSRF desabilitado
- SERVER_NAME e PREFERRED_URL_SCHEME definidos para estabilidade de testes

## Boas praticas operacionais

- Nao manter SECRET_KEY real no codigo; usar variavel de ambiente.
- Ativar SESSION_COOKIE_SECURE em ambiente HTTPS.
- Separar claramente banco de producao e banco de teste.
- Revisar impacto de CSRF antes de alterar metodos protegidos.

## Matriz rapida de risco

1. COOKIE_SECURE em False em producao:
   - Risco: transmissao insegura de cookie de sessao.
2. Banco compartilhado entre ambiente normal e teste:
   - Risco: contaminacao de dados.
3. SECRET_KEY fraca:
   - Risco: comprometimento de sessao.

## Checklist de mudanca de configuracao

- Mudanca foi aplicada no ambiente correto?
- Existe impacto em testes automatizados?
- Existe impacto em fluxo de login/sessao?
- Existe impacto em integridade de dados?
