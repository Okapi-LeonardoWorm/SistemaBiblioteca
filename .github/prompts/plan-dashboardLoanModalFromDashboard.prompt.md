## Plan: Reativar Edição de Empréstimo no Dashboard

Vamos devolver essa funcionalidade sem mexer no visual: manter o layout do dashboard igual e apenas reativar a interação de clique nas linhas dos painéis 1 e 7 para abrir o modal padrão de edição de empréstimo.

**Estratégia recomendada**
1. Reusar o fluxo já existente em [app/static/js/management.js](app/static/js/management.js), especialmente `initLoanModalWorkflow` e `openLoanModal`.
2. Evitar criar novo modal customizado para dashboard.
3. Adicionar somente comportamento (JS + modais ocultos), sem alterar estrutura visual dos painéis.

**Steps**
1. Validar contrato dos endpoints do dashboard para garantir `loan_id` em itens de devoluções e acervo.
2. Tornar linhas das duas tabelas explicitamente clicáveis por atributo (`data-loan-id`) durante renderização dinâmica no JS.
3. Incluir no template do dashboard os modais reutilizados de empréstimo (`loanModal` e `loanReturnModal`) no fim da página, sem alterar grid/cards/seções.
4. Inicializar no dashboard o workflow compartilhado: `window.ManagementUI?.initLoanModalWorkflow(...)`.
5. Adicionar listener de clique nas linhas dos painéis 1 e 7 para chamar `window.ManagementUI?.openLoanModal(loanId)`.
6. Garantir que isso não conflite com o drill-down dos gráficos (escopo de clique só nas linhas das tabelas).
7. Tratar casos sem `loan_id`, estado loading e prevenção de duplo-bind.
8. Atualizar testes para validar que payloads continuam contendo `loan_id` e que contratos não quebraram.

**Relevant files**
- [app/templates/dashboard.html](app/templates/dashboard.html)
- [app/static/js/dashboard-app.js](app/static/js/dashboard-app.js)
- [app/static/js/management.js](app/static/js/management.js)
- [app/services/dashboard_service.py](app/services/dashboard_service.py)
- [app/routes/apis.py](app/routes/apis.py)
- [tests/unit/test_dashboard_api.py](tests/unit/test_dashboard_api.py)

**Verification**
1. Clicar numa linha de [app/templates/dashboard.html](app/templates/dashboard.html) no painel 1 abre modal “Editar Empréstimo”.
2. Clicar numa linha do painel 7 abre o mesmo modal.
3. “Informar retorno” no modal funciona também quando aberto pelo dashboard.
4. Remova o Drill-down de gráficos dos charts e mantenha apenas a funcionalidade de detalhes quando acontece um hover sobre o chart.
5. Layout visual do dashboard permanece inalterado.
6. Testes de API do dashboard continuam verdes.

Se você aprovar esse plano, o próximo passo é executar a implementação exatamente nessa ordem.
