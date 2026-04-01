# Inicializacao da Aplicacao

## Objetivo

Detalhar como o backend e inicializado, quais componentes sao registrados e em que ordem.

## Fonte principal

- app/__init__.py
- app/routes/__init__.py
- run.py

## Sequencia de bootstrap

1. createApp(config_name) cria instancia Flask.
2. Configuracao e carregada a partir de Config ou TestingConfig.
3. Extensoes sao inicializadas:
   - db
   - bcrypt
   - login_manager
   - migrate
   - bootstrap
   - CORS
   - sessao server-side (Session)
4. LoginManager define login_view para auth.login.
5. user_loader e registrado para resolver usuario por userId.
6. context_processor injeta dados globais de sessao e helper de CSRF.
7. Em app_context:
   - modelos/formularios sao importados
   - listeners de auditoria sao registrados
   - blueprints sao registrados
8. Aplicacao pronta para servir requisicoes.

## Registro de blueprints

A funcao register_blueprints(app) registra os blueprints em lista ordenada e, em seguida, cria aliases legados de endpoints para compatibilidade retroativa.

Implicacao tecnica: renomear endpoints sem atualizar aliases pode quebrar fluxos antigos, testes e redirecionamentos.

## Contexto global de templates

O context_processor injeta:

- username
- userType
- userId
- csrf_token helper com fallback em cenarios de teste/falha
- render_user_identifier helper para identificacao visual de usuario PCD

## Alias de app factory

O modulo exporta create_app = createApp para compatibilidade com ferramentas e CLIs que esperam a convencao create_app.

## Riscos e sintomas comuns

1. Falha em sessao server-side:
   - Sintoma: erros envolvendo tabela/session storage.
   - Verificar: SESSION_TYPE, SESSION_SQLALCHEMY e inicializacao do db.
2. Falha no user_loader:
   - Sintoma: usuario nao autenticado apos login.
   - Verificar: tipo do identificador e integridade do registro de usuario.
3. Rotas ausentes:
   - Sintoma: 404 em endpoint esperado.
   - Verificar: blueprint registrado e nome do endpoint alvo.

## Checklist para evoluir bootstrap

- Preservar ordem de inicializacao de extensoes criticas.
- Evitar logica de dominio dentro da app factory.
- Atualizar esta documentacao ao adicionar/remover extensoes.
