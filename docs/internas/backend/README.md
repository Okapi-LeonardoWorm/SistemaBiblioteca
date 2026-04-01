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
7. routes/navigation.md
8. routes/auth.md
9. routes/books.md
10. routes/keywords.md
11. routes/users.md
12. routes/configs.md
13. routes/admin-sessions.md
14. routes/apis.md
15. routes/audit-logs.md
16. routes/fluxo-emprestimos.md
17. services/processamento-em-lote.md
18. utils/utilitarios-backend.md

## Fonte de verdade

A documentacao deve refletir o comportamento real do codigo. Ao evoluir backend, atualizar os documentos impactados no mesmo ciclo de entrega.
