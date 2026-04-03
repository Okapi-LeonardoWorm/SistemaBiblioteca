# Rotas de Navegacao (navigation)

## Objetivo

Documentar o blueprint navigation, responsavel pelas telas de entrada operacional apos autenticacao.

## Fonte principal

- app/routes/navigation.py
- app/templates/menu.html
- app/templates/dashboard.html
- app/routes/apis.py

## Endpoints

1. GET /dashboard
   - Requer login.
   - Acesso restrito a administrador.
   - Exibe indicadores, listagens de emprestimos e visoes resumidas para acompanhamento.
2. GET /menu
   - Requer login.
   - Exibe menu principal de navegacao para operacao do sistema.

## Regras de acesso

- dashboard exige perfil admin.
- usuario sem permissao para dashboard e redirecionado para menu com aviso.

## Comportamento funcional

- dashboard apresenta KPIs e filtros por periodo para acompanhamento de emprestimos.
- dashboard consome dados via endpoints /api/dashboard/* (detalhes em routes/dashboard-apis.md).
- menu funciona como hub de navegacao para as areas operacionais.

## Riscos e pontos de atencao

1. Falha de permissao no dashboard:
   - validar perfil do usuario autenticado.
2. Informacoes de painel divergentes:
   - revisar filtros ativos e periodo selecionado.

## Diretriz de evolucao

- Manter dashboard como visao de acompanhamento e nao como concentrador de regras de negocio.
- Preservar menu como ponto de entrada simples e orientado a tarefas.
- Toda mudanca de bloco/indicador no dashboard deve atualizar tambem a documentacao externa operacional.
