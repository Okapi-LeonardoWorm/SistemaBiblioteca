(function () {
    const state = {
        devolucoes: {
            quickFilter: 'today',
            student: '',
            page: 1,
            perPage: 10
        },
        related: {
            period: 'all',
            serie: '',
            turma: '',
            periodoEscolar: ''
        },
        popularidadeRange: 'anual',
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

        ['filterPeriodoTempo', 'filterSerie', 'filterTurma', 'filterPeriodoEscolar'].forEach((id) => {
            document.getElementById(id)?.addEventListener('change', loadRelatedPanels);
            document.getElementById(id)?.addEventListener('input', loadRelatedPanels);
        });

        document.getElementById('popularidadeRange')?.addEventListener('change', (event) => {
            state.popularidadeRange = event.target.value;
            loadPopularidade();
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
            period: document.getElementById('filterPeriodoTempo')?.value || 'all',
            serie: document.getElementById('filterSerie')?.value || '',
            turma: document.getElementById('filterTurma')?.value || '',
            periodo: document.getElementById('filterPeriodoEscolar')?.value || ''
        };
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
        await withLoading(['#engajamentoTurmaChart', '#engajamentoSerieChart', '#engajamentoPeriodoChart', '#topAlunosList'], async () => {
            const filters = currentRelatedFilters();
            const data = await apiGet('/api/dashboard/engajamento', {
                period: filters.period,
                serie: filters.serie,
                turma: filters.turma,
                periodo: filters.periodo
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
                range: state.popularidadeRange,
                serie: filters.serie,
                turma: filters.turma,
                periodo: filters.periodo,
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
        setupLoanModalWorkflow();
        bindEvents();
        try {
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
