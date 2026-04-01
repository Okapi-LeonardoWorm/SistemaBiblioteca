# Rotas de API Interna (apis)

## Objetivo

Documentar o blueprint apis, usado por componentes de interface para busca assistida de usuarios e livros.

## Fonte principal

- app/routes/apis.py
- app/utils/date_utils.py
- app/utils/loan_utils.py

## Endpoints

1. GET /api/users/search
   - Parametros:
     - q: termo de busca (obrigatorio)
     - limit: limite de resultados (default 10)
   - Retorno: lista de usuarios ativos com atributos de identificacao e perfil.
2. GET /api/books/search
   - Parametros:
     - q: termo de busca (obrigatorio)
     - limit: limite de resultados (default 10)
     - loanDate: data de inicio para disponibilidade (opcional)
     - returnDate: data fim para disponibilidade (opcional)
   - Retorno: lista de livros ativos com disponibilidade calculada para o periodo.

## Contrato de resposta

- Resposta no formato JSON com chave results.
- Se q vazio, retorna results vazio (sem erro).
- Campos derivados:
  - users.search inclui age calculada.
  - books.search inclui available e lista de keywords.

## Controle de acesso

- Todos os endpoints exigem login_required.

## Regras de negocio relevantes

- Apenas registros nao deletados sao retornados.
- limit e convertido para inteiro com fallback seguro.
- available usa available_copies_for_range com status ACTIVE dos emprestimos.

## Riscos e pontos de atencao

1. Limite sem teto explicito:
   - considerar hard cap para evitar queries caras.
2. Busca textual ampla:
   - usar indices apropriados nas colunas consultadas.
3. Exposicao de campos:
   - revisar periodicamente campos retornados para minimizar superficie de dados.

## Troubleshooting

1. API retorna vazio com dados existentes:
   - verificar filtro deleted e valor de q.
2. Disponibilidade incoerente:
   - verificar parse de loanDate/returnDate e status de emprestimos ativos.
3. Latencia em autocomplete:
   - revisar indices, tamanho de limit e padrao de ilike.

## Diretriz de evolucao

- Versionar endpoint quando houver mudanca de contrato.
- Definir schema de resposta com validacao automatizada se APIs crescerem.
