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
6. routes/blueprints-e-endpoints.md
7. routes/auth.md
8. routes/books.md
9. routes/users.md
10. routes/configs.md
11. routes/admin-sessions.md
12. routes/apis.md
13. routes/audit-logs.md
14. routes/fluxo-emprestimos.md
15. services/processamento-em-lote.md
16. utils/utilitarios-backend.md

## Fonte de verdade

A documentacao deve refletir o comportamento real do codigo. Ao evoluir backend, atualizar os documentos impactados no mesmo ciclo de entrega.
