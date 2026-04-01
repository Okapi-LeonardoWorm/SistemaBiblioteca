# Rotas de Livros (books)

## Objetivo

Documentar o blueprint books, cobrindo CRUD logico, filtros de listagem e importacao em lote de livros.

## Fonte principal

- app/routes/books.py
- app/models.py (Book, KeyWord)
- app/services/book_bulk_create_service.py
- app/services/bulk_jobs.py

## Endpoints principais

1. GET /livros
   - Listagem paginada com busca, filtros avancados e ordenacao.
   - Suporta include_deleted para visualizar soft deleted.
2. GET /livros/form e GET /livros/form/<book_id>
   - Renderiza formulario parcial para criacao/edicao.
3. POST /livros/new
   - Cria livro e associa palavras-chave.
4. POST /livros/edit/<book_id>
   - Edita livro, detecta alteracoes e sincroniza keywords.
5. POST /excluir_livro/<id>
   - Soft delete (book.deleted = True).
6. POST /reativar_livro/<id>
   - Reativacao de registro soft deleted.

## Importacao em lote

1. GET /livros/import/bulk
   - Entrada do fluxo, redireciona para upload.
2. GET, POST /livros/import/bulk/upload
   - Valida permissao, formato de arquivo e dispara job em thread.
3. GET /livros/import/bulk/template
   - Download de modelo CSV/XLSX.
4. GET /livros/import/bulk/progress/<job_id>
5. GET /livros/import/bulk/status/<job_id>
6. GET /livros/import/bulk/result/<job_id>
7. GET /livros/import/bulk/errors/<job_id>

## Regras de negocio relevantes

- Datas de publicacao/aquisicao podem ser modo ano ou data completa.
- Keywords sao normalizadas por parse_normalized_tags.
- update evita commit quando nenhuma alteracao real e detectada.
- jobs de importacao usam controle de ownership e permissao por perfil.

## Controle de acesso

- Todo blueprint protegido com login_required.
- Importacao em lote exige permissao via can_manage_user_bulk_import.

## Riscos e pontos de atencao

1. Nome da funcao de permissao:
   - books usa can_manage_user_bulk_import para livros; validar intencao semantica para manutencao.
2. Thread em processo web:
   - Em deploy multi-worker, monitorar consistencia de jobs em memoria.
3. Filtro por datas em string:
   - Garantir consistencia de parse conforme tipo de coluna no banco.

## Troubleshooting

1. Resultado duplicado em listagem:
   - Verificar join de keywords e uso de distinct.
2. Job nao encontrado:
   - Verificar ownerUserId/permissao e persistencia em memoria apos restart.
3. Upload rejeitado:
   - Verificar extensao detectada e colunas obrigatorias do template.

## Diretriz de evolucao

- Extrair trechos de filtro e ordenacao para componente reutilizavel caso reaproveitado em outros dominios.
- Se houver escala horizontal, migrar estado de job para backend compartilhado.
