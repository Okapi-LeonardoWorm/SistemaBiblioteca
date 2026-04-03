# Servico Interno do Dashboard

## Objetivo

Explicar como `dashboard_service.py` consolida dados para os blocos do dashboard administrativo.

## Fonte principal

- app/services/dashboard_service.py
- app/routes/apis.py

## Visao geral

O servico agrega informacoes de `Loan`, `Book`, `User`, `KeyWord` e `Configuration`, aplicando:

1. Normalizacao de filtros (serie, turma, tipo de usuario).
2. Janela temporal por periodo/range ou datas explicitas.
3. Sanitizacao de limites numericos.
4. Cache in-memory de curta duracao para blocos mais consultados.

## Funcoes principais

- `get_dashboard_kpis`: KPIs globais de acervo e emprestimos.
- `get_devolucoes_data`: lista operacional com filtros e paginacao.
- `get_devolucoes_filter_options`: opcoes de filtros para UI.
- `get_top_tags`: ranking de tags.
- `get_ultimos_emprestimos`: timeline de emprestimos recentes.
- `get_engajamento`: agregacoes pedagogicas por turma/serie/periodo.
- `get_popularidade`: top livros e distribuicao de tags.
- `get_acervo_data`: itens em risco/perdidos conforme limiar.
- `get_drilldown_details`: detalhamento textual por origem do grafico.

## Cache

- Estrutura: dicionario em memoria do processo.
- Chave: composicao dos parametros relevantes da consulta.
- TTL:
- Curto: 60s
- Medio: 120s

Observacao: cache nao e compartilhado entre processos/workers.

## Configuracao usada

- `DASHBOARD_LOST_THRESHOLD_DAYS` (e aliases) define o limiar de dias para classificar extravio no bloco de saude do acervo.
- Fallback padrao: 30 dias.

## Regras de consistencia

- Sempre filtra usuarios/livros ativos quando aplicavel.
- Ajusta ranges de data invalidos (ex.: start > end).
- Limita `limit`/`per_page` para evitar consulta pesada.
- Diferentes blocos podem usar criterios de status distintos.

## Riscos e atencao

1. Cache local pode exibir pequena defasagem apos atualizacoes imediatas.
2. Mudanca em regras de status pode gerar divergencia entre widgets se nao for alinhada.
3. Filtros combinados amplos podem aumentar custo de query.

## Evolucao recomendada

- Monitorar consultas mais caras e criar indices conforme padrao de filtro.
- Extrair schemas de resposta para validar contrato entre backend e frontend.
- Se crescer volume, avaliar cache centralizado por ambiente.
