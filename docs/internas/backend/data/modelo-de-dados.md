# Modelo de Dados e Dominio

## Objetivo

Mapear entidades centrais, relacionamentos e regras de consistencia do dominio.

## Fonte principal

- app/models.py

## Entidades principais

1. User:
   - Identificacao, perfil, dados pessoais e metadados de criacao/atualizacao.
   - Flag deleted para soft delete.
2. Book:
   - Catalogo de livros e quantidade de exemplares.
   - Relacao N:N com palavras-chave via KeyWordBook.
3. Loan:
   - Emprestimo entre usuario e livro com estado em StatusLoan.
   - Relacoes com usuario solicitante, criador e atualizador.
4. KeyWord e KeyWordBook:
   - Taxonomia de busca e associacao com livros.
5. Configuration e ConfigSpec:
   - Configuracao funcional e especificacao de validacao.
6. RBAC:
   - Permission, Role, RolePermission.
7. Auditoria e sessao:
   - AuditLog e UserSession.

## Relacionamentos de destaque

- User 1:N Loan (como borrower).
- User 1:N Loan (como createdBy e updatedBy).
- Book 1:N Loan.
- Book N:N KeyWord via KeyWordBook.
- User 1:N UserSession.

## Enums

StatusLoan:
- ACTIVE
- OVERDUE
- COMPLETED
- LOST
- CANCELLED

## Convencoes de consistencia

- Soft delete aplicado em entidades com campo deleted.
- Campos de trilha temporal e autoria (creationDate, lastUpdate, createdBy, updatedBy).
- Conversao de datas por @validates para entradas em string.

## Pontos de atencao

- Conversao de data distribuida em varias entidades exige padrao consistente em novas models.
- Tabela keyWords usa casing misto; em SQL manual requer cuidado com quoting.
- Campos historicos e alias (username como sinonimo de identificationCode) mantem compatibilidade retroativa.

## Diretriz para novas entidades

- Definir responsabilidade de negocio e chave primaria clara.
- Incluir trilha temporal/autoria quando aplicavel.
- Decidir explicitamente entre hard delete e soft delete.
- Declarar relacionamentos no ORM com backrefs compreensiveis.
- Planejar impacto em auditoria.
