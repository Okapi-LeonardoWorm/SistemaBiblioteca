# Rotas de Palavras-chave (keywords)

## Objetivo

Documentar o blueprint keywords para gerenciamento de tags usadas na classificacao de livros.

## Fonte principal

- app/routes/keywords.py
- app/templates/palavras_chave.html
- app/templates/_keyword_form.html

## Endpoints

1. GET /palavras_chave
   - Requer login.
   - Lista tags ativas com busca e paginacao.
2. GET /palavras_chave/form e GET /palavras_chave/form/<keyword_id>
   - Requer login.
   - Renderiza formulario de criacao/edicao de tag.
3. POST /palavras_chave/new
   - Requer login.
   - Cria uma ou varias tags em unica submissao.
4. POST /palavras_chave/edit/<keyword_id>
   - Requer login.
   - Atualiza nome da tag com validacao de duplicidade.
5. POST /excluir_palavra_chave/<id>
   - Requer login.
   - Aplica exclusao logica da tag.

## Regras de negocio relevantes

- Entrada multipla aceita separacao por virgula e ponto e virgula.
- Tags sao normalizadas antes de salvar.
- Tags duplicadas sao ignoradas na criacao multipla.
- Exclusao e logica, preservando historico e referencias.

## Riscos e pontos de atencao

1. Duplicidade semantica de tags:
   - orientar padrao de nomenclatura para evitar variacoes equivalentes.
2. Exclusao logica sem reativacao dedicada:
   - recuperar requer procedimento administrativo especifico.

## Troubleshooting

1. Tag nao aparece apos salvar:
   - verificar se foi ignorada por ja existir.
2. Erro ao editar:
   - verificar se o novo nome conflita com tag existente.
3. Tag ausente na listagem:
   - pode estar marcada como excluida.

## Diretriz de evolucao

- Definir politica de governanca de vocabulario para reduzir redundancia.
- Avaliar fluxo dedicado de reativacao se a operacao exigir recuperacao frequente.
