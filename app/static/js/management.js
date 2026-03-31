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
        button.addEventListener('click', function () {
            const url = button.dataset.deleteUrl;
            const csrfToken = button.dataset.csrfToken;
            const confirmMessage = button.dataset.confirmMessage || 'Tem certeza que deseja excluir este item?';

            if (!url || !csrfToken) {
                return;
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
})(window.ManagementUI);
