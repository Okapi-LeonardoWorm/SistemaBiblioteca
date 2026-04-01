window.ManagementUI = window.ManagementUI || {};

(function (namespace) {
    let hoverTimer = null;
    let hoverTooltipEl = null;
    let hoverTargetEl = null;

    function clearDelayedHoverTooltips() {
        if (hoverTimer) {
            clearTimeout(hoverTimer);
            hoverTimer = null;
        }
        if (hoverTooltipEl) {
            hoverTooltipEl.remove();
            hoverTooltipEl = null;
        }
        hoverTargetEl = null;
    }

    function showDelayedTooltip(targetEl) {
        const fullText = (targetEl?.getAttribute('data-full') || targetEl?.textContent || '').trim();
        if (!fullText) {
            return;
        }

        const rect = targetEl.getBoundingClientRect();
        const tooltip = document.createElement('div');
        tooltip.className = 'delayed-hover-tooltip';
        tooltip.textContent = fullText;
        tooltip.style.left = `${window.scrollX + rect.left}px`;
        tooltip.style.top = `${window.scrollY + rect.top}px`;
        document.body.appendChild(tooltip);
        hoverTooltipEl = tooltip;
    }

    function bindTooltipOnElement(el, delayMs) {
        if (!el || el.dataset.tooltipBound === '1') {
            return;
        }

        el.dataset.tooltipBound = '1';
        el.addEventListener('mouseenter', function () {
            clearDelayedHoverTooltips();
            hoverTargetEl = el;
            hoverTimer = setTimeout(function () {
                if (hoverTargetEl === el) {
                    showDelayedTooltip(el);
                }
            }, delayMs);
        });

        el.addEventListener('mouseleave', function () {
            if (hoverTargetEl === el) {
                clearDelayedHoverTooltips();
            }
        });
    }

    function initDelayedHoverTooltips(root, delayMs = 1000) {
        const scope = root || document;
        scope.querySelectorAll('.fade-hover-text').forEach(function (el) {
            bindTooltipOnElement(el, delayMs);
        });
    }

    function bindSoftDeleteAction(root, options) {
        const scope = root || document;
        const selector = options?.selector || '[data-delete-url]';
        const button = scope.querySelector(selector);

        if (!button || button.dataset.softDeleteBound === '1') {
            return;
        }

        button.dataset.softDeleteBound = '1';
        button.addEventListener('click', async function () {
            const url = button.dataset.deleteUrl;
            const csrfToken = button.dataset.csrfToken;
            const usageUrl = button.dataset.usageUrl;
            let confirmMessage = button.dataset.confirmMessage || 'Tem certeza que deseja excluir este item?';

            if (!url || !csrfToken) {
                return;
            }

            if (usageUrl) {
                try {
                    const usageResponse = await fetch(usageUrl, {
                        method: 'GET',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                    });
                    const usagePayload = await usageResponse.json();
                    if (usagePayload?.success) {
                        const count = Number(usagePayload.usage_count) || 0;
                        const noun = count === 1 ? 'livro' : 'livros';
                        confirmMessage = `Esta tag está sendo usada em ${count} ${noun}, tem certeza que deseja excluir?`;
                    }
                } catch (_) {
                    window.alert('Nao foi possivel consultar o uso da tag. Tente novamente.');
                    return;
                }
            }

            if (!window.confirm(confirmMessage)) {
                return;
            }

            const formBody = new URLSearchParams();
            formBody.append('csrf_token', csrfToken);

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formBody.toString(),
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (payload) {
                    if (payload?.success) {
                        if (typeof options?.onSuccess === 'function') {
                            options.onSuccess(payload);
                        }
                        return;
                    }
                    if (typeof options?.onError === 'function') {
                        options.onError(payload);
                        return;
                    }
                    window.alert(payload?.message || 'Nao foi possivel excluir.');
                })
                .catch(function () {
                    if (typeof options?.onError === 'function') {
                        options.onError();
                        return;
                    }
                    window.alert('Ocorreu um erro ao excluir.');
                });
        });
    }

    if (!document.body?.dataset.managementTooltipScrollBound) {
        document.addEventListener('scroll', clearDelayedHoverTooltips, true);
        document.body.dataset.managementTooltipScrollBound = '1';
    }

    namespace.initDelayedHoverTooltips = initDelayedHoverTooltips;
    namespace.clearDelayedHoverTooltips = clearDelayedHoverTooltips;
    namespace.bindSoftDeleteAction = bindSoftDeleteAction;

    function formatDateBR(rawValue) {
        if (!rawValue) {
            return 'N/A';
        }
        const dt = new Date(rawValue);
        if (Number.isNaN(dt.getTime())) {
            return 'N/A';
        }
        return dt.toLocaleDateString('pt-BR');
    }

    function getStatusBadgeClass(statusName) {
        if (statusName === 'ACTIVE') {
            return 'bg-success';
        }
        if (statusName === 'OVERDUE') {
            return 'bg-danger';
        }
        return 'bg-secondary';
    }

    function openLoanModal(loanId, options = {}) {
        const modalId = options.modalId || 'loanModal';
        const closeModalId = options.closeModalId;
        const modalEl = document.getElementById(modalId);
        if (!modalEl || !loanId) {
            return;
        }

        if (closeModalId) {
            const closeModalEl = document.getElementById(closeModalId);
            const closeModalInstance = closeModalEl ? bootstrap.Modal.getInstance(closeModalEl) : null;
            closeModalInstance?.hide();
        }

        modalEl.dataset.loanId = String(loanId);
        const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
        modalInstance.show();
    }

    function initLoanModalWorkflow(options = {}) {
        const modalId = options.modalId || 'loanModal';
        const saveBtnId = options.saveBtnId || 'saveLoanBtn';
        const returnModalId = options.returnModalId || 'loanReturnModal';
        const returnFormId = options.returnFormId || 'loanReturnForm';
        const returnErrorId = options.returnErrorId || 'loanReturnError';

        const loanModal = document.getElementById(modalId);
        const saveLoanBtn = document.getElementById(saveBtnId);
        const loanReturnModalEl = document.getElementById(returnModalId);
        const loanReturnForm = document.getElementById(returnFormId);
        const loanReturnError = document.getElementById(returnErrorId);

        if (!loanModal || !saveLoanBtn || !loanReturnModalEl || !loanReturnForm || !loanReturnError) {
            return;
        }

        if (loanModal.dataset.workflowBound === '1') {
            return;
        }
        loanModal.dataset.workflowBound = '1';

        function openReturnModalForLoan(loanId) {
            const returnLoanInput = document.getElementById('returnLoanId');
            const returnDateInput = document.getElementById('returnDateInput');
            const returnStatusInput = document.getElementById('returnStatusInput');

            if (returnLoanInput) {
                returnLoanInput.value = loanId || '';
            }
            if (returnDateInput) {
                returnDateInput.valueAsDate = new Date();
            }
            if (returnStatusInput) {
                returnStatusInput.value = 'COMPLETED';
            }
            loanReturnError.classList.add('d-none');
            loanReturnError.textContent = '';

            const returnModal = bootstrap.Modal.getOrCreateInstance(loanReturnModalEl);
            returnModal.show();
        }

        loanModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            const triggerLoanId = trigger?.getAttribute('data-loan-id');
            const loanId = triggerLoanId || loanModal.dataset.loanId || '';
            const modalTitle = loanModal.querySelector('.modal-title');
            const modalBody = loanModal.querySelector('.modal-body');

            if (!modalBody || !modalTitle) {
                return;
            }

            modalTitle.textContent = 'Carregando...';
            modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';

            const formUrl = loanId ? `/emprestimos/form/${loanId}` : '/emprestimos/form';

            fetch(formUrl)
                .then(function (response) { return response.text(); })
                .then(function (html) {
                    modalTitle.textContent = loanId ? 'Editar Empréstimo' : 'Novo Empréstimo';
                    modalBody.innerHTML = html;
                })
                .catch(function () {
                    modalBody.innerHTML = '<p class="text-danger">Erro ao carregar o formulário.</p>';
                });
        });

        loanModal.addEventListener('click', function (event) {
            const returnBtn = event.target.closest('#returnLoanFromEditBtn');
            if (returnBtn) {
                event.preventDefault();
                event.stopPropagation();
                const loanId = returnBtn.getAttribute('data-loan-id');
                const loanModalInstance = bootstrap.Modal.getInstance(loanModal);
                loanModalInstance?.hide();
                openReturnModalForLoan(loanId);
                return;
            }
        });

        saveLoanBtn.addEventListener('click', function () {
            const form = document.getElementById('loanModalForm');
            if (!form) {
                return;
            }

            const formData = new FormData(form);
            const actionUrl = form.getAttribute('action');

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.success) {
                        window.location.reload();
                        return;
                    }
                    window.alert('Erro de validação: ' + JSON.stringify(data.errors));
                })
                .catch(function () {
                    window.alert('Ocorreu um erro ao salvar.');
                });
        });

        loanReturnForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            loanReturnError.classList.add('d-none');
            loanReturnError.textContent = '';

            const loanId = document.getElementById('returnLoanId')?.value;
            const formData = new FormData(loanReturnForm);

            try {
                const resp = await fetch(`/emprestimos/return/${loanId}`, {
                    method: 'POST',
                    body: formData,
                });
                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    const msg = data?.errors ? JSON.stringify(data.errors) : 'Erro ao registrar retorno.';
                    loanReturnError.textContent = msg;
                    loanReturnError.classList.remove('d-none');
                    return;
                }

                window.location.reload();
            } catch (_err) {
                loanReturnError.textContent = 'Falha de comunicação ao registrar retorno.';
                loanReturnError.classList.remove('d-none');
            }
        });

        if (typeof window.cancelLoan !== 'function') {
            window.cancelLoan = function (event, loanId) {
                event?.stopPropagation();
                if (!window.confirm('Deseja realmente cancelar este empréstimo? Esta ação não pode ser desfeita.')) {
                    return;
                }

                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

                fetch(`/emprestimos/cancel/${loanId}`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                })
                    .then(function (resp) { return resp.json(); })
                    .then(function (data) {
                        if (data?.success) {
                            window.location.reload();
                            return;
                        }
                        window.alert(data?.message || 'Não foi possível cancelar o empréstimo.');
                    })
                    .catch(function () {
                        window.alert('Erro ao cancelar empréstimo.');
                    });
            };
        }
    }

    function initUserLoanHistoryBackref(options = {}) {
        const root = options.root;
        const userId = options.userId;
        const modalId = options.modalId || 'loanModal';
        const closeModalId = options.closeModalId || 'userModal';

        if (!root || !userId) {
            return;
        }

        const borrowedEl = root.querySelector('[data-history-summary="borrowed"]');
        const returnedEl = root.querySelector('[data-history-summary="returned"]');
        const searchInput = root.querySelector('[data-history-search]');
        const rowsContainer = root.querySelector('[data-history-rows]');
        const emptyEl = root.querySelector('[data-history-empty]');
        const statusMenu = root.querySelector('[data-history-status-menu]');
        const statusButtonLabel = root.querySelector('[data-history-status-label]');

        if (!borrowedEl || !returnedEl || !searchInput || !rowsContainer || !emptyEl || !statusMenu || !statusButtonLabel) {
            return;
        }

        if (root.dataset.historyBound === '1') {
            return;
        }
        root.dataset.historyBound = '1';

        let statusOptions = [];
        let selectedStatuses = new Set();
        let debounceHandle = null;

        function renderStatusDropdown() {
            const selectedCount = selectedStatuses.size;
            statusButtonLabel.textContent = selectedCount === 0
                ? 'Todos os status'
                : `${selectedCount} status selecionado(s)`;

            const allChecked = selectedCount === 0;
            const optionsHtml = statusOptions.map(function (status) {
                const checked = selectedStatuses.has(status.name) ? 'checked' : '';
                return `
                    <li>
                        <label class="dropdown-item d-flex align-items-center gap-2">
                            <input class="form-check-input mt-0" type="checkbox" data-history-status-item="${status.name}" ${checked}>
                            <span>${status.label}</span>
                        </label>
                    </li>
                `;
            }).join('');

            statusMenu.innerHTML = `
                <li>
                    <label class="dropdown-item d-flex align-items-center gap-2">
                        <input class="form-check-input mt-0" type="checkbox" data-history-status-all ${allChecked ? 'checked' : ''}>
                        <span>Todos</span>
                    </label>
                </li>
                <li><hr class="dropdown-divider"></li>
                ${optionsHtml}
            `;
        }

        function buildHistoryUrl() {
            const params = new URLSearchParams();
            const q = (searchInput.value || '').trim();
            if (q) {
                params.append('q', q);
            }
            selectedStatuses.forEach(function (statusName) {
                params.append('statuses', statusName);
            });
            return `/api/users/${userId}/loan-history?${params.toString()}`;
        }

        function renderRows(items) {
            if (!Array.isArray(items) || items.length === 0) {
                rowsContainer.innerHTML = '';
                emptyEl.classList.remove('d-none');
                return;
            }

            emptyEl.classList.add('d-none');
            rowsContainer.innerHTML = items.map(function (item) {
                const fullBookName = item.bookName || 'N/A';
                return `
                    <tr class="history-loan-row" data-loan-id="${item.loanId}">
                        <td>
                            <span class="fade-hover-text" data-full="${fullBookName}">${fullBookName}</span>
                        </td>
                        <td>${formatDateBR(item.loanDate)}</td>
                        <td>${formatDateBR(item.returnDate)}</td>
                        <td><span class="badge ${getStatusBadgeClass(item.statusName)}">${item.statusLabel || 'N/A'}</span></td>
                    </tr>
                `;
            }).join('');

            initDelayedHoverTooltips(root);
        }

        async function fetchHistory() {
            try {
                const response = await fetch(buildHistoryUrl());
                const payload = await response.json();
                if (!response.ok || !payload?.success) {
                    throw new Error('Erro ao carregar histórico.');
                }

                borrowedEl.textContent = String(payload.summary?.total_borrowed ?? 0);
                returnedEl.textContent = String(payload.summary?.total_returned ?? 0);

                if (statusOptions.length === 0) {
                    statusOptions = payload.status_options || [];
                    renderStatusDropdown();
                }

                renderRows(payload.items || []);
            } catch (_err) {
                rowsContainer.innerHTML = '';
                emptyEl.classList.remove('d-none');
                emptyEl.textContent = 'Erro ao carregar histórico.';
            }
        }

        searchInput.addEventListener('input', function () {
            if (debounceHandle) {
                clearTimeout(debounceHandle);
            }
            debounceHandle = setTimeout(fetchHistory, 300);
        });

        statusMenu.addEventListener('change', function (event) {
            const allCheckbox = event.target.closest('[data-history-status-all]');
            if (allCheckbox) {
                selectedStatuses = new Set();
                renderStatusDropdown();
                fetchHistory();
                return;
            }

            const statusCheckbox = event.target.closest('[data-history-status-item]');
            if (!statusCheckbox) {
                return;
            }

            const statusName = statusCheckbox.getAttribute('data-history-status-item');
            if (statusCheckbox.checked) {
                selectedStatuses.add(statusName);
            } else {
                selectedStatuses.delete(statusName);
            }

            renderStatusDropdown();
            fetchHistory();
        });

        rowsContainer.addEventListener('click', function (event) {
            const row = event.target.closest('.history-loan-row');
            if (!row) {
                return;
            }
            const loanId = row.getAttribute('data-loan-id');
            openLoanModal(loanId, {
                modalId: modalId,
                closeModalId: closeModalId,
            });
        });

        renderStatusDropdown();
        fetchHistory();
    }

    function initBookLoanHistoryBackref(options = {}) {
        const root = options.root;
        const bookId = options.bookId;
        const modalId = options.modalId || 'loanModal';
        const closeModalId = options.closeModalId || 'bookModal';

        if (!root || !bookId) {
            return;
        }

        const borrowedEl = root.querySelector('[data-history-summary="borrowed"]');
        const returnedEl = root.querySelector('[data-history-summary="returned"]');
        const searchInput = root.querySelector('[data-history-search]');
        const rowsContainer = root.querySelector('[data-history-rows]');
        const emptyEl = root.querySelector('[data-history-empty]');
        const statusMenu = root.querySelector('[data-history-status-menu]');
        const statusButtonLabel = root.querySelector('[data-history-status-label]');

        if (!borrowedEl || !returnedEl || !searchInput || !rowsContainer || !emptyEl || !statusMenu || !statusButtonLabel) {
            return;
        }

        if (root.dataset.historyBound === '1') {
            return;
        }
        root.dataset.historyBound = '1';

        let statusOptions = [];
        let selectedStatuses = new Set();
        let debounceHandle = null;

        function renderStatusDropdown() {
            const selectedCount = selectedStatuses.size;
            statusButtonLabel.textContent = selectedCount === 0
                ? 'Todos os status'
                : `${selectedCount} status selecionado(s)`;

            const allChecked = selectedCount === 0;
            const optionsHtml = statusOptions.map(function (status) {
                const checked = selectedStatuses.has(status.name) ? 'checked' : '';
                return `
                    <li>
                        <label class="dropdown-item d-flex align-items-center gap-2">
                            <input class="form-check-input mt-0" type="checkbox" data-history-status-item="${status.name}" ${checked}>
                            <span>${status.label}</span>
                        </label>
                    </li>
                `;
            }).join('');

            statusMenu.innerHTML = `
                <li>
                    <label class="dropdown-item d-flex align-items-center gap-2">
                        <input class="form-check-input mt-0" type="checkbox" data-history-status-all ${allChecked ? 'checked' : ''}>
                        <span>Todos</span>
                    </label>
                </li>
                <li><hr class="dropdown-divider"></li>
                ${optionsHtml}
            `;
        }

        function buildHistoryUrl() {
            const params = new URLSearchParams();
            const q = (searchInput.value || '').trim();
            if (q) {
                params.append('q', q);
            }
            selectedStatuses.forEach(function (statusName) {
                params.append('statuses', statusName);
            });
            return `/api/books/${bookId}/loan-history?${params.toString()}`;
        }

        function renderRows(items) {
            if (!Array.isArray(items) || items.length === 0) {
                rowsContainer.innerHTML = '';
                emptyEl.classList.remove('d-none');
                return;
            }

            emptyEl.classList.add('d-none');
            rowsContainer.innerHTML = items.map(function (item) {
                const fullUserCode = item.userCode || 'N/A';
                const fullUserName = item.userName || 'N/A';
                return `
                    <tr class="history-loan-row" data-loan-id="${item.loanId}">
                        <td><span class="fade-hover-text" data-full="${fullUserCode}">${fullUserCode}</span></td>
                        <td><span class="fade-hover-text" data-full="${fullUserName}">${fullUserName}</span></td>
                        <td>${formatDateBR(item.loanDate)}</td>
                        <td>${formatDateBR(item.returnDate)}</td>
                        <td><span class="badge ${getStatusBadgeClass(item.statusName)}">${item.statusLabel || 'N/A'}</span></td>
                    </tr>
                `;
            }).join('');

            initDelayedHoverTooltips(root);
        }

        async function fetchHistory() {
            try {
                const response = await fetch(buildHistoryUrl());
                const payload = await response.json();
                if (!response.ok || !payload?.success) {
                    throw new Error('Erro ao carregar histórico.');
                }

                borrowedEl.textContent = String(payload.summary?.total_borrowed ?? 0);
                returnedEl.textContent = String(payload.summary?.total_returned ?? 0);

                if (statusOptions.length === 0) {
                    statusOptions = payload.status_options || [];
                    renderStatusDropdown();
                }

                renderRows(payload.items || []);
            } catch (_err) {
                rowsContainer.innerHTML = '';
                emptyEl.classList.remove('d-none');
                emptyEl.textContent = 'Erro ao carregar histórico.';
            }
        }

        searchInput.addEventListener('input', function () {
            if (debounceHandle) {
                clearTimeout(debounceHandle);
            }
            debounceHandle = setTimeout(fetchHistory, 300);
        });

        statusMenu.addEventListener('change', function (event) {
            const allCheckbox = event.target.closest('[data-history-status-all]');
            if (allCheckbox) {
                selectedStatuses = new Set();
                renderStatusDropdown();
                fetchHistory();
                return;
            }

            const statusCheckbox = event.target.closest('[data-history-status-item]');
            if (!statusCheckbox) {
                return;
            }

            const statusName = statusCheckbox.getAttribute('data-history-status-item');
            if (statusCheckbox.checked) {
                selectedStatuses.add(statusName);
            } else {
                selectedStatuses.delete(statusName);
            }

            renderStatusDropdown();
            fetchHistory();
        });

        rowsContainer.addEventListener('click', function (event) {
            const row = event.target.closest('.history-loan-row');
            if (!row) {
                return;
            }
            const loanId = row.getAttribute('data-loan-id');
            openLoanModal(loanId, {
                modalId: modalId,
                closeModalId: closeModalId,
            });
        });

        renderStatusDropdown();
        fetchHistory();
    }

    namespace.openLoanModal = openLoanModal;
    namespace.initLoanModalWorkflow = initLoanModalWorkflow;
    namespace.initUserLoanHistoryBackref = initUserLoanHistoryBackref;
    namespace.initBookLoanHistoryBackref = initBookLoanHistoryBackref;
})(window.ManagementUI);
