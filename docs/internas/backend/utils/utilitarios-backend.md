# Utilitarios de Backend

## Objetivo

Consolidar o papel da camada utilitaria e orientar uso correto para evitar duplicacoes e acoplamento indevido.

## Fonte principal

- app/utils/
- app/utils/loan_utils.py

## Modulos utilitarios mapeados

- auth_utils.py: Responsável por todo o controle centralizado e dinâmico de autorização/permissões de usuários baseado em níveis (veja os detalhes de sua arquitetura [neste guia de permissões](../core/permissoes.md)).
- config_utils.py
- date_utils.py
- loan_utils.py
- session_utils.py
- text_utils.py
- bulk_import/ (suporte a importacao)

## Exemplo de regra utilitaria critica

available_copies_for_range(book, start_date, end_date) em loan_utils.py:

- Calcula disponibilidade de exemplares para um intervalo.
- Considera apenas emprestimos com status ACTIVE.
- Usa soma agregada no banco para evitar processamento ineficiente em memoria.

## Criterios para criar utilitario

- Regra reutilizada em mais de um ponto do sistema.
- Regra sem dependencias diretas de protocolo HTTP.
- Regra que melhora legibilidade e reduz duplicacao em rotas/servicos.

## Anti-padroes a evitar

- Colocar regra de negocio complexa sem testes na camada utilitaria.
- Duplicar funcao semelhante em multiplos arquivos utilitarios.
- Criar utilitarios que dependem fortemente de contexto de template/rota.

## Diretriz de organizacao

- Manter utilitarios por assunto e com nomes explicitos.
- Priorizar funcoes puras quando possivel.
- Documentar pre-condicoes e tipo esperado de parametros.

## Checklist de manutencao

- Existe sobreposicao entre utilitarios?
- Existe funcao utilitaria sem uso real?
- Regras de data/parse continuam consistentes entre modulos?
