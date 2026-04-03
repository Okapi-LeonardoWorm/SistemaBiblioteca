# Rotas de Configuracoes (configs)

## Objetivo

Documentar gestao de configuracoes de sistema e especificacoes de validacao via blueprint configs.

## Fonte principal

- app/routes/configs.py
- app/models.py (Configuration, ConfigSpec)
- app/utils/config_utils.py

## Endpoints

1. GET /configuracoes
   - Lista configuracoes com busca e paginacao.
   - Carrega specs associadas por chave.
2. GET /configuracoes/form e GET /configuracoes/form/<config_id>
   - Formulario de criacao/edicao com dados de spec.
3. POST /configuracoes/new
   - Cria Configuration + ConfigSpec com validacao de valor.
4. POST /configuracoes/edit/<config_id>
   - Atualiza valor e spec da mesma chave.

## Controle de acesso

- Todas as rotas exigem login_required.
- Acesso administrativo obrigatorio via is_admin_user.

## Regras de consistencia

- key e imutavel na edicao.
- value e validado contra spec (tipo, limites, allowed values e required).
- creation/last update e autoria sao atualizados em Configuration e ConfigSpec.
- A chave `DASHBOARD_LOST_THRESHOLD_DAYS` e usada pelo dashboard para definir dias de atraso considerados extravio.

## Riscos e pontos de atencao

1. Mudancas em configuracao impactam runtime:
   - Chaves como limites de negocio podem alterar comportamento sem deploy.
2. Erro de validacao de value:
   - Depende de spec atual; revisar valueType e constraints.
3. Duplicidade de chave:
   - Bloqueada na criacao; fluxo de alteracao deve usar edicao.

## Troubleshooting

1. Acesso negado em configuracoes:
   - Verificar userType/admin e helper is_admin_user.
2. Valor nao persiste:
   - Verificar validate_config_value e normalizacao retornada.
3. Formulario sem spec esperada:
   - Confirmar existencia de ConfigSpec vinculada a key.

## Diretriz de evolucao

- Tratar configuracoes sensiveis com auditoria adicional quando necessario.
- Evitar adicionar chaves sem definir claramente contrato de tipo e dominio de valores.
