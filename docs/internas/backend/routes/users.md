# Rotas de Usuarios (users)

## Objetivo

Documentar o blueprint users para administracao de usuarios, ciclo de vida (soft delete/reativacao) e importacao em massa.

## Fonte principal

- app/routes/users.py
- app/models.py (User)
- app/services/user_bulk_create_service.py
- app/services/bulk_jobs.py

## Endpoints principais

1. GET /users
   - Listagem paginada com busca, filtros e ordenacao.
2. GET /users/form e GET /users/form/<user_id>
   - Formulario parcial de criacao/edicao.
   - Em modo edicao, exibe aba Historico com dashboard e listagem de emprestimos do usuario.
3. POST /users/new
   - Cria usuario com hash de senha.
4. POST /users/edit/<user_id>
   - Atualiza usuario e senha opcional.
5. GET /users/check-identification
   - Verifica existencia de identificationCode (suporte a validacao frontend).
6. POST /users/delete/<user_id>
   - Soft delete.
7. POST /users/reactivate/<user_id>
   - Reativacao de usuario.

## Importacao em massa

1. GET, POST /users/import/bulk
   - Selecao de tipo de usuario para importacao.
2. GET, POST /users/import/bulk/upload
   - Upload e disparo de job.
3. GET /users/import/bulk/template
   - Download do modelo CSV/XLSX por tipo de usuario.
4. GET /users/import/bulk/progress/<job_id>
5. GET /users/import/bulk/status/<job_id>
6. GET /users/import/bulk/result/<job_id>
7. GET /users/import/bulk/errors/<job_id>

## Regras de negocio relevantes

- Tipos permitidos para importacao em massa:
  - aluno
  - colaborador
  - bibliotecario
  - admin
- Campos obrigatorios mudam por tipo de usuario.
- Senha em criacao manual usa hash e fallback default quando ausente.
- Soft delete preserva historico e integridade de referencias.
- No historico do modal de usuario:
   - filtro por status e busca por nome do livro sao aplicados via API interna;
   - item clicavel abre o modal de edicao de emprestimo existente;
   - contagem de retirados desconsidera emprestimos CANCELLED.

## Controle de acesso

- Rotas protegidas por login_required.
- Importacao em massa protegida por can_manage_user_bulk_import.
- Ownership de job e validado para consulta de status/resultado.

## Riscos e pontos de atencao

1. endpoint check-identification:
   - Exposto a usuarios autenticados; considerar rate-limit se necessario.
2. soft delete:
   - Impacta consultas e filtros em outros dominios (ex.: emprestimos).
3. importacao em massa:
   - Dependencia de armazenamento local para arquivos e relatorio de erros.

## Troubleshooting

1. Erro de validacao recorrente na importacao:
   - Revisar colunas do modelo baixado e tipo selecionado.
2. Usuario aparentemente sumiu:
   - Confirmar se foi marcado como deleted e usar include_deleted.
3. Atualizacao de senha nao aplicada:
   - Verificar se campo password foi enviado no form de edicao.

## Diretriz de evolucao

- Consolidar politicas de senha em servico unico quando houver requisitos de seguranca adicionais.
- Manter compatibilidade de identificationCode como identificador principal de login.
- Reutilizar o padrao de backref de historico para novas telas, evitando duplicacao de modais de emprestimo.
