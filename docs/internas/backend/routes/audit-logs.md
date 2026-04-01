# Rotas de Auditoria (audit_logs)

## Objetivo

Documentar o blueprint audit_logs para consulta administrativa da trilha de auditoria.

## Fonte principal

- app/routes/audit_logs.py
- app/models.py (AuditLog, User)
- app/utils/auth_utils.py

## Endpoint

1. GET /audit_logs
   - Requer login e perfil admin.
   - Lista logs de auditoria com filtros e paginacao.

## Filtros suportados

- action
- target_type
- user_id (id numerico ou trecho de identificationCode)
- start_date (YYYY-MM-DD)
- end_date (YYYY-MM-DD)

## Comportamento de consulta

- Usa joinedload para carregar usuario associado em conjunto com logs.
- Ordenacao padrao: timestamp decrescente.
- Paginacao: 20 itens por pagina.
- end_date e ajustado para fim do dia (23:59:59).

## Regras de acesso

- Acesso exclusivo para usuarios administrativos via is_admin_user.

## Riscos e pontos de atencao

1. Consulta ampla sem filtros:
   - Pode gerar custo alto em bases volumosas.
2. Filtro user_id textual:
   - Resolve apenas primeiro usuario que casa com termo; comportamento deve ser conhecido.
3. Datas invalidas:
   - Sao ignoradas silenciosamente, podendo confundir usuario operador.

## Troubleshooting

1. Nenhum log aparece:
   - Verificar permissao admin e existencia de registros em AuditLog.
2. Filtro por usuario nao retorna esperado:
   - Testar com user_id numerico para eliminar ambiguidade de identificacao.
3. Janela de data parece incompleta:
   - Confirmar formato YYYY-MM-DD e timezone de gravacao dos eventos.

## Diretriz de evolucao

- Adicionar validacao e feedback explicito para filtros invalidos.
- Considerar filtros adicionais por target_id e por intervalo de horario.
- Avaliar exportacao para analise forense quando requerido.
