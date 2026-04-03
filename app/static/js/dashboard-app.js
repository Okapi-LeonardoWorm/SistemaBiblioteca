(function () {
    const state = {
        devolucoes: {
            quickFilter: 'today',
            student: '',
            series: [],
            turmas: [],
            page: 1,
            perPage: 10
        },
        related: {
            series: [],
            turmas: [],
            userTypes: []
        },
        recentLimit: 10,
        acervo: {
            daysLost: 30
        },
        pagination: {
            hasNext: false,
            hasPrev: false
        }
    };

    let studentSearchTimer = null;

    function toIsoDate(dateObj) {
        const local = new Date(dateObj.getTime() - dateObj.getTimezoneOffset() * 60000);
        return local.toISOString().slice(0, 10);
    }

    function initEngajamentoDateRange() {
        const initialEl = document.getElementById('filterDataInicial');
        const finalEl = document.getElementById('filterDataFinal');
        if (!initialEl || !finalEl) return;

        if (!finalEl.value) {
            finalEl.value = toIsoDate(new Date());
        }
        if (!initialEl.value) {
            const start = new Date();
            start.setDate(start.getDate() - 30);
            initialEl.value = toIsoDate(start);
        }
    }

    function formatDateBR(isoDate) {
        if (!isoDate) return '-';
        const date = new Date(isoDate);
        if (Number.isNaN(date.getTime())) return isoDate;
        return date.toLocaleDateString('pt-BR');
    }

    function statusBadge(statusUi) {
        if (statusUi === 'atrasado') return '<span class="badge text-bg-danger">Atrasado</span>';
        if (statusUi === 'vence_hoje') return '<span class="badge text-bg-warning">Vence hoje</span>';
        return '<span class="badge text-bg-success">No prazo</span>';
    }

    function setLoading(selectors, loading) {
        selectors.forEach((selector) => {
            const el = document.querySelector(selector);
            if (!el) return;
            el.classList.toggle('is-loading', Boolean(loading));
        });
    }

    async function withLoading(selectors, callback) {
        setLoading(selectors, true);
        try {
            return await callback();
        } finally {
            setLoading(selectors, false);
        }
    }

    async function apiGet(path, params = {}) {
        const url = new URL(path, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach((item) => {
                    if (item !== null && item !== undefined && `${item}` !== '') {
                        url.searchParams.append(key, item);
                    }
                });
                return;
            }
            if (value !== null && value !== undefined && `${value}` !== '') {
                url.searchParams.set(key, value);
            }
        });

        const response = await fetch(url.toString(), {
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Falha ao carregar dados de ${path}`);
        }

        const payload = await response.json();
        if (!payload.success) {
            throw new Error(payload.message || `Erro em ${path}`);
        }
        return payload.data;
    }

    function bindEvents() {
        document.querySelectorAll('.quick-filter').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.quick-filter').forEach((item) => item.classList.remove('active'));
                btn.classList.add('active');
                state.devolucoes.quickFilter = btn.dataset.quickFilter;
                state.devolucoes.page = 1;
                loadDevolucoes();
            });
        });

        const studentFilterEl = document.getElementById('filterStudent');
        if (studentFilterEl) {
            studentFilterEl.addEventListener('input', () => {
                clearTimeout(studentSearchTimer);
                studentSearchTimer = setTimeout(() => {
                    state.devolucoes.student = studentFilterEl.value.trim();
                    state.devolucoes.page = 1;
                    loadDevolucoes();
                }, 350);
            });
        }

        document.getElementById('clearDevolucoesFilters')?.addEventListener('click', () => {
            resetDevolucoesFilters();
            loadDevolucoes();
        });

        const nextButton = document.getElementById('devolucoesNext');
        const prevButton = document.getElementById('devolucoesPrev');
        nextButton?.addEventListener('click', () => {
            if (!state.pagination.hasNext) return;
            state.devolucoes.page += 1;
            loadDevolucoes();
        });
        prevButton?.addEventListener('click', () => {
            if (!state.pagination.hasPrev || state.devolucoes.page <= 1) return;
            state.devolucoes.page -= 1;
            loadDevolucoes();
        });

        ['filterDataInicial', 'filterDataFinal'].forEach((id) => {
            document.getElementById(id)?.addEventListener('change', loadRelatedPanels);
            document.getElementById(id)?.addEventListener('input', loadRelatedPanels);
        });

        document.getElementById('clearRelatedFilters')?.addEventListener('click', () => {
            resetRelatedFilters();
        });

        document.getElementById('recentLimit')?.addEventListener('change', (event) => {
            state.recentLimit = parseInt(event.target.value, 10) || 10;
            loadUltimosEmprestimos();
        });

        document.getElementById('acervoLostDays')?.addEventListener('change', (event) => {
            state.acervo.daysLost = parseInt(event.target.value, 10) || 30;
            loadAcervo();
        });

        bindLoanRowClick('#devolucoesTable tbody');
        bindLoanRowClick('#acervoTable tbody');
    }

    function selectQuickFilterButton(value) {
        document.querySelectorAll('.quick-filter').forEach((item) => {
            item.classList.toggle('active', item.dataset.quickFilter === value);
        });
    }

    function resetDevolucoesFilters() {
        state.devolucoes.quickFilter = 'today';
        state.devolucoes.student = '';
        state.devolucoes.series = [];
        state.devolucoes.turmas = [];
        state.devolucoes.page = 1;

        const studentEl = document.getElementById('filterStudent');
        if (studentEl) studentEl.value = '';

        document.querySelectorAll('input[name="devolucoesSerieOption"]:checked').forEach((checkbox) => {
            checkbox.checked = false;
        });
        document.querySelectorAll('input[name="devolucoesTurmaOption"]:checked').forEach((checkbox) => {
            checkbox.checked = false;
        });

        selectQuickFilterButton('today');
        updateDropdownLabels();
    }

    function updateDropdownLabels() {
        const serieButton = document.getElementById('devolucoesSerieDropdown');
        const turmaButton = document.getElementById('devolucoesTurmaDropdown');
        if (serieButton) {
            serieButton.textContent = state.devolucoes.series.length ? `Série (${state.devolucoes.series.length})` : 'Série';
        }
        if (turmaButton) {
            turmaButton.textContent = state.devolucoes.turmas.length ? `Turma (${state.devolucoes.turmas.length})` : 'Turma';
        }
    }

    function fillMultiSelectDropdownOptions({ menuId, checkboxName, values, placeholder, selectedValues }) {
        const menuEl = document.getElementById(menuId);
        if (!menuEl) return;
        menuEl.innerHTML = '';

        if (!values.length) {
            const emptyState = document.createElement('div');
            emptyState.className = 'devolucoes-dropdown-empty';
            emptyState.textContent = placeholder;
            menuEl.appendChild(emptyState);
            return;
        }

        const allWrapper = document.createElement('label');
        allWrapper.className = 'dropdown-item d-flex align-items-center gap-2';

        const allCheckbox = document.createElement('input');
        allCheckbox.type = 'checkbox';
        allCheckbox.className = 'form-check-input mt-0';
        allCheckbox.name = checkboxName;
        allCheckbox.value = '__all__';
        allCheckbox.checked = values.length > 0 && values.every((value) => selectedValues.includes(String(value)));

        const allText = document.createElement('span');
        allText.className = 'fw-semibold';
        allText.textContent = 'Todos';

        allWrapper.appendChild(allCheckbox);
        allWrapper.appendChild(allText);
        menuEl.appendChild(allWrapper);

        const divider = document.createElement('div');
        divider.className = 'dropdown-divider my-1';
        menuEl.appendChild(divider);

        values.forEach((value) => {
            const wrapper = document.createElement('label');
            wrapper.className = 'dropdown-item d-flex align-items-center gap-2';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input mt-0';
            checkbox.name = checkboxName;
            checkbox.value = String(value);
            checkbox.checked = selectedValues.includes(String(value));

            const text = document.createElement('span');
            text.textContent = String(value);

            wrapper.appendChild(checkbox);
            wrapper.appendChild(text);
            menuEl.appendChild(wrapper);
        });
    }

    function bindMultiSelectDropdownSelection({ menuId, checkboxName, selectedValues, onChange, bindKey }) {
        const menu = document.getElementById(menuId);
        if (!menu) return;

        const boundAttr = bindKey || `bound-${checkboxName}`;
        if (menu.dataset[boundAttr] === '1') return;
        menu.dataset[boundAttr] = '1';

        menu.addEventListener('click', (event) => {
            event.stopPropagation();
        });

        menu.addEventListener('change', (event) => {
            const checkbox = event.target.closest(`input[name="${checkboxName}"]`);
            if (!checkbox) return;

            const allValue = '__all__';
            const allCheckbox = menu.querySelector(`input[name="${checkboxName}"][value="${allValue}"]`);
            const itemCheckboxes = Array.from(menu.querySelectorAll(`input[name="${checkboxName}"]`))
                .filter((el) => el.value !== allValue);

            if (checkbox.value === allValue) {
                itemCheckboxes.forEach((el) => {
                    el.checked = checkbox.checked;
                });
            } else if (allCheckbox) {
                const allChecked = itemCheckboxes.length > 0 && itemCheckboxes.every((el) => el.checked);
                allCheckbox.checked = allChecked;
            }

            const nextValues = itemCheckboxes
                .filter((el) => el.checked)
                .map((el) => el.value);

            selectedValues.splice(0, selectedValues.length, ...nextValues);
            onChange(nextValues);
        });
    }

    async function loadDevolucoesFilterOptions() {
        const data = await apiGet('/api/dashboard/devolucoes/filter-options');
        fillMultiSelectDropdownOptions({
            menuId: 'devolucoesSerieMenu',
            checkboxName: 'devolucoesSerieOption',
            values: data.series || [],
            placeholder: 'Sem séries cadastradas',
            selectedValues: state.devolucoes.series,
        });
        fillMultiSelectDropdownOptions({
            menuId: 'devolucoesTurmaMenu',
            checkboxName: 'devolucoesTurmaOption',
            values: data.turmas || [],
            placeholder: 'Sem turmas cadastradas',
            selectedValues: state.devolucoes.turmas,
        });
        bindMultiSelectDropdownSelection({
            menuId: 'devolucoesSerieMenu',
            checkboxName: 'devolucoesSerieOption',
            selectedValues: state.devolucoes.series,
            bindKey: 'dropdownBound',
            onChange: () => {
                state.devolucoes.page = 1;
                updateDropdownLabels();
                loadDevolucoes();
            }
        });
        bindMultiSelectDropdownSelection({
            menuId: 'devolucoesTurmaMenu',
            checkboxName: 'devolucoesTurmaOption',
            selectedValues: state.devolucoes.turmas,
            bindKey: 'dropdownBound',
            onChange: () => {
                state.devolucoes.page = 1;
                updateDropdownLabels();
                loadDevolucoes();
            }
        });
        updateDropdownLabels();
    }

    function bindLoanRowClick(selector) {
        const tbody = document.querySelector(selector);
        if (!tbody || tbody.dataset.loanRowClickBound === '1') return;

        tbody.dataset.loanRowClickBound = '1';
        tbody.addEventListener('click', (event) => {
            const ignoredTarget = event.target.closest('a, button, input, select, textarea, label');
            if (ignoredTarget) return;

            const row = event.target.closest('tr[data-loan-id]');
            if (!row || !tbody.contains(row)) return;

            const loanId = row.dataset.loanId;
            if (!loanId) return;
            window.ManagementUI?.openLoanModal(loanId);
        });
    }

    function setupLoanModalWorkflow() {
        window.ManagementUI?.initLoanModalWorkflow({
            modalId: 'loanModal',
            saveBtnId: 'saveLoanBtn',
            returnModalId: 'loanReturnModal',
            returnFormId: 'loanReturnForm',
            returnErrorId: 'loanReturnError',
        });
    }

    function currentRelatedFilters() {
        return {
            startDate: document.getElementById('filterDataInicial')?.value || '',
            endDate: document.getElementById('filterDataFinal')?.value || '',
            series: state.related.series,
            turmas: state.related.turmas,
            userTypes: state.related.userTypes
        };
    }

    function resetRelatedFilters() {
        const finalEl = document.getElementById('filterDataFinal');
        const initialEl = document.getElementById('filterDataInicial');

        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 30);

        if (finalEl) finalEl.value = toIsoDate(end);
        if (initialEl) initialEl.value = toIsoDate(start);

        state.related.userTypes = [];
        state.related.series = [];
        state.related.turmas = [];

        document.querySelectorAll('input[name="relatedSerieOption"]').forEach((el) => {
            el.checked = false;
        });
        document.querySelectorAll('input[name="relatedTurmaOption"]').forEach((el) => {
            el.checked = false;
        });
        document.querySelectorAll('input[name="relatedUserTypeOption"]').forEach((el) => {
            el.checked = false;
        });

        updateRelatedDropdownLabels();
        loadRelatedPanels();
    }

    function updateRelatedDropdownLabels() {
        const serieButton = document.getElementById('relatedSerieDropdown');
        const turmaButton = document.getElementById('relatedTurmaDropdown');
        const userTypeButton = document.getElementById('relatedUserTypeDropdown');
        if (serieButton) {
            serieButton.textContent = state.related.series.length ? `Série (${state.related.series.length})` : 'Série';
        }
        if (turmaButton) {
            turmaButton.textContent = state.related.turmas.length ? `Turma (${state.related.turmas.length})` : 'Turma';
        }
        if (userTypeButton) {
            userTypeButton.textContent = state.related.userTypes.length ? `Tipo de usuário (${state.related.userTypes.length})` : 'Tipo de usuário';
        }
    }

    async function loadRelatedFilterOptions() {
        const data = await apiGet('/api/dashboard/devolucoes/filter-options');
        fillMultiSelectDropdownOptions({
            menuId: 'relatedSerieMenu',
            checkboxName: 'relatedSerieOption',
            values: data.series || [],
            placeholder: 'Sem séries cadastradas',
            selectedValues: state.related.series,
        });
        fillMultiSelectDropdownOptions({
            menuId: 'relatedTurmaMenu',
            checkboxName: 'relatedTurmaOption',
            values: data.turmas || [],
            placeholder: 'Sem turmas cadastradas',
            selectedValues: state.related.turmas,
        });
        fillMultiSelectDropdownOptions({
            menuId: 'relatedUserTypeMenu',
            checkboxName: 'relatedUserTypeOption',
            values: data.user_types || [],
            placeholder: 'Sem tipos cadastrados',
            selectedValues: state.related.userTypes,
        });
        bindMultiSelectDropdownSelection({
            menuId: 'relatedSerieMenu',
            checkboxName: 'relatedSerieOption',
            selectedValues: state.related.series,
            bindKey: 'relatedDropdownBound',
            onChange: () => {
                updateRelatedDropdownLabels();
                loadRelatedPanels();
            }
        });
        bindMultiSelectDropdownSelection({
            menuId: 'relatedTurmaMenu',
            checkboxName: 'relatedTurmaOption',
            selectedValues: state.related.turmas,
            bindKey: 'relatedDropdownBound',
            onChange: () => {
                updateRelatedDropdownLabels();
                loadRelatedPanels();
            }
        });
        bindMultiSelectDropdownSelection({
            menuId: 'relatedUserTypeMenu',
            checkboxName: 'relatedUserTypeOption',
            selectedValues: state.related.userTypes,
            bindKey: 'relatedDropdownBound',
            onChange: () => {
                updateRelatedDropdownLabels();
                loadRelatedPanels();
            }
        });
        updateRelatedDropdownLabels();
    }

    async function loadKpis() {
        await withLoading(['#kpiGrid'], async () => {
            const data = await apiGet('/api/dashboard/kpis');
            const map = {
                total_books: data.total_books,
                total_active_loans: data.total_active_loans,
                total_students: data.total_students,
                total_collaborators: data.total_collaborators
            };

            document.querySelectorAll('#kpiGrid [data-kpi]').forEach((card) => {
                const key = card.dataset.kpi;
                const valueEl = card.querySelector('.kpi-value');
                if (valueEl) valueEl.textContent = map[key] ?? '--';
            });
        });
    }

    async function loadDevolucoes() {
        await withLoading(['#devolucoesTable', '#devolutionKpis'], async () => {
            const data = await apiGet('/api/dashboard/devolucoes', {
                quick_filter: state.devolucoes.quickFilter,
                student: state.devolucoes.student,
                serie: state.devolucoes.series,
                turma: state.devolucoes.turmas,
                page: state.devolucoes.page,
                per_page: state.devolucoes.perPage
            });

            const tbody = document.querySelector('#devolucoesTable tbody');
            tbody.innerHTML = '';

            if (!data.items.length) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Nenhum empréstimo encontrado.</td></tr>';
            } else {
                data.items.forEach((item) => {
                    const tr = document.createElement('tr');
                    if (item.loan_id) {
                        tr.dataset.loanId = String(item.loan_id);
                    }
                    tr.innerHTML = `
                        <td>${item.book_name || '-'}</td>
                        <td>
                            <div class="fw-semibold">${item.student_name || '-'}</div>
                            <small class="text-muted">${item.student_code || '-'}</small>
                        </td>
                        <td>${formatDateBR(item.due_date)}</td>
                        <td>${statusBadge(item.status_ui)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            document.querySelectorAll('#devolutionKpis [data-kpi]').forEach((el) => {
                const key = el.dataset.kpi;
                el.textContent = data.kpis[key] ?? '--';
            });
            document.getElementById('todayBadge').textContent = data.kpis.today ?? 0;
            document.getElementById('overdueBadge').textContent = data.kpis.overdue ?? 0;

            state.pagination.hasNext = data.pagination.has_next;
            state.pagination.hasPrev = data.pagination.has_prev;

            const pageInfo = document.getElementById('devolucoesPageInfo');
            pageInfo.textContent = `Página ${data.pagination.page} de ${data.pagination.pages || 1} (${data.pagination.total} registros)`;
        });
    }

    async function loadUltimosEmprestimos() {
        await withLoading(['#recentTimeline'], async () => {
            const data = await apiGet('/api/dashboard/ultimos-emprestimos', { limit: state.recentLimit });
            const list = document.getElementById('recentTimeline');
            list.innerHTML = '';

            if (!data.items.length) {
                list.innerHTML = '<div class="text-muted">Sem registros recentes.</div>';
                return;
            }

            data.items.forEach((item) => {
                const row = document.createElement('article');
                row.className = 'timeline-item';
                row.title = `Aluno: ${item.student_name || '-'} | Tag: ${item.principal_tag || 'Sem tag'}`;
                row.innerHTML = `
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <div class="timeline-book">${item.book_name || '-'}</div>
          <div class="timeline-meta">${item.student_name || '-'} · ${formatDateBR(item.loan_date)}</div>
          <span class="badge text-bg-light border">${item.principal_tag || 'Sem tag'}</span>
        </div>
      `;
                list.appendChild(row);
            });
        });
    }

    async function loadTagsTop() {
        await withLoading(['#tagsTopChart'], async () => {
            const data = await apiGet('/api/dashboard/tags-top', { limit: 10 });
            window.DashboardCharts.renderTagsTop(data.items || []);
        });
    }

    async function loadEngajamento() {
        await withLoading(['#engajamentoTurmaChart', '#engajamentoSerieChart', '#topAlunosList'], async () => {
            const filters = currentRelatedFilters();
            const data = await apiGet('/api/dashboard/engajamento', {
                start_date: filters.startDate,
                end_date: filters.endDate,
                serie: filters.series,
                turma: filters.turmas,
                user_type: filters.userTypes
            });

            window.DashboardCharts.renderEngajamento(data);

            const list = document.getElementById('topAlunosList');
            list.innerHTML = '';
            (data.top_alunos || []).forEach((item) => {
                const li = document.createElement('li');
                li.className = 'top-list-item';
                li.innerHTML = `<span>#${item.rank} ${item.name || '-'} (${item.code || '-'})</span><strong>${item.count}</strong>`;
                list.appendChild(li);
            });
        });
    }

    async function loadPopularidade() {
        await withLoading(['#popularidadeLivrosChart', '#popularidadeTagsChart'], async () => {
            const filters = currentRelatedFilters();
            const data = await apiGet('/api/dashboard/popularidade', {
                start_date: filters.startDate,
                end_date: filters.endDate,
                serie: filters.series,
                turma: filters.turmas,
                user_type: filters.userTypes,
                limit: 10
            });
            window.DashboardCharts.renderPopularidade(data);
        });
    }

    async function loadAcervo() {
        await withLoading(['#acervoTable'], async () => {
            const data = await apiGet('/api/dashboard/acervo', {
                days_lost: state.acervo.daysLost,
                limit: 20
            });

            document.getElementById('acervoLostCount').textContent = data.lost_count;
            const tbody = document.querySelector('#acervoTable tbody');
            tbody.innerHTML = '';

            if (!data.items.length) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Nenhum item para reposição.</td></tr>';
                return;
            }

            data.items.forEach((item) => {
                const tr = document.createElement('tr');
                if (item.loan_id) {
                    tr.dataset.loanId = String(item.loan_id);
                }
                tr.innerHTML = `
        <td>${item.book_name || '-'}</td>
        <td>
          <div>${item.last_user_name || '-'}</div>
          <small class="text-muted">${item.last_user_code || '-'}</small>
        </td>
        <td>${formatDateBR(item.loan_date)}</td>
        <td><span class="badge text-bg-danger">${item.days_overdue} dias</span></td>
      `;
                tbody.appendChild(tr);
            });
        });
    }

    async function loadRelatedPanels() {
        await Promise.all([loadEngajamento(), loadPopularidade()]);
    }

    async function bootstrap() {
        initEngajamentoDateRange();
        setupLoanModalWorkflow();
        bindEvents();
        try {
            await loadDevolucoesFilterOptions();
            await loadRelatedFilterOptions();
            await Promise.all([
                loadKpis(),
                loadDevolucoes(),
                loadUltimosEmprestimos(),
                loadTagsTop(),
                loadEngajamento(),
                loadPopularidade(),
                loadAcervo()
            ]);
        } catch (error) {
            console.error(error);
        }
    }

    document.addEventListener('DOMContentLoaded', bootstrap);
})();
