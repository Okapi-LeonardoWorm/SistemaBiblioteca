# Arquitetura Geral do Backend

## Objetivo

Descrever a arquitetura logica do backend para guiar manutencao, extensao e troubleshooting.

## Stack principal

- Flask como framework web.
- SQLAlchemy ORM para persistencia.
- Flask-Migrate para evolucao de schema.
- Flask-Login para autenticacao de sessao.
- Flask-Session com sessao server-side.
- Gevent WSGI server no ponto de execucao principal.

## Estrutura por camadas

1. Entrada e composicao:
   - app/__init__.py: app factory, extensoes e registro de blueprints.
   - run.py: servidor WSGI e logging basico.
2. Interface HTTP:
   - app/routes/: blueprints por dominio funcional.
3. Regras e orquestracao:
   - app/services/: casos de uso mais especializados (ex.: jobs de importacao).
4. Dominio e dados:
   - app/models.py: entidades, enums e relacionamentos.
5. Utilitarios transversais:
   - app/utils/: funcoes reutilizaveis para validacao, data, auth e configuracao.
6. Governanca:
   - app/audit.py: trilha de auditoria automatica e manual.

## Principios de desenho observados

- Segregacao por responsabilidade usando blueprints.
- App factory para configuracao por ambiente e testabilidade.
- Reuso via camada utils em regras transversais.
- Auditoria acoplada ao ciclo ORM para rastreabilidade.

## Fluxo de requisicao em alto nivel

1. Requisicao chega a uma rota de um blueprint.
2. Decorators de autenticacao/autorizacao aplicam controle de acesso.
3. Rota valida entrada e consulta modelos/utilitarios/servicos.
4. SQLAlchemy executa operacoes de leitura/escrita.
5. Listeners de auditoria registram alteracoes de entidades.
6. Rota retorna HTML, JSON ou redirecionamento.

## Pontos de atencao arquitetural

- Sessao server-side depende de banco e configuracao correta de SESSION_SQLALCHEMY.
- Aliases legados de endpoint mantem retrocompatibilidade e precisam ser preservados em refactors.
- Parte da logica de negocio ainda reside em rotas; novas evolucoes devem priorizar extracao progressiva para services.
- Fluxo de backup e offline-first: cria artefato local primeiro e envia ao Google Drive por fila/retry em segundo momento.

## Arquitetura de backup (resumo)

- Rota de acao manual e configuracao em app/routes/backups.py.
- Orquestracao principal em app/services/backup_service.py.
- Persistencia operacional em BackupRun, BackupSchedule, BackupUpload e OAuthCredential.
- Tela de observabilidade com status da fila, tentativas e erros em app/templates/backups.html.

## Referencias de codigo

- app/__init__.py
- app/routes/__init__.py
- app/models.py
- app/audit.py
- run.py
