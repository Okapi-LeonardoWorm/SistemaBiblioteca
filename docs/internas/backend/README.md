# Backend - Documentacao Interna

## Escopo

Documenta a arquitetura e o funcionamento interno do backend Flask do Sistema Biblioteca.

## Dominios

- core/: bootstrap da aplicacao, configuracao e ciclo de execucao.
- data/: modelos, relacionamentos, auditoria e consistencia de dados.
- routes/: blueprints, contratos HTTP e fluxos de negocio.
- services/: servicos internos e processamento em lote.
- utils/: utilitarios compartilhados e regras de uso.

## Ordem recomendada de leitura

1. core/arquitetura-geral.md
2. core/inicializacao-app.md
3. core/configuracao-ambientes.md
4. data/modelo-de-dados.md
5. data/auditoria-e-rastreabilidade.md
6. data/migracao-login-codigo-ou-email.md
7. routes/blueprints-e-endpoints.md
8. routes/navigation.md
9. routes/auth.md
10. routes/dashboard-apis.md
11. routes/books.md
12. routes/keywords.md
13. routes/users.md
14. routes/configs.md
15. routes/admin-sessions.md
16. routes/apis.md
17. routes/audit-logs.md
18. routes/fluxo-emprestimos.md
19. services/processamento-em-lote.md
20. services/dashboard-service.md
21. utils/utilitarios-backend.md

## Fonte de verdade

A documentacao deve refletir o comportamento real do codigo. Ao evoluir backend, atualizar os documentos impactados no mesmo ciclo de entrega.
