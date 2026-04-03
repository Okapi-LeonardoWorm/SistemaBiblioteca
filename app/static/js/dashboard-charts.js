(function () {
    function emptyChart(targetId, title) {
        Plotly.react(
            targetId,
            [],
            {
                title,
                margin: { t: 40, r: 10, b: 40, l: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            },
            { displayModeBar: false, responsive: true }
        )
    }

    function renderTagsTop(items) {
        if (!items || !items.length) {
            emptyChart('tagsTopChart', 'Top tags');
            return;
        }
        Plotly.react(
            'tagsTopChart',
            [{
                x: items.map((i) => i.count),
                y: items.map((i) => i.word),
                customdata: items.map((i) => i.word_id),
                type: 'bar',
                orientation: 'h',
                marker: { color: '#6d9f71' },
                text: items.map((i) => `${i.percentage}%`),
                textposition: 'outside',
                hovertemplate: 'Tag: %{y}<br>Ocorrências: %{x}<extra></extra>'
            }],
            {
                margin: { t: 10, r: 30, b: 30, l: 100 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            },
            { displayModeBar: false, responsive: true }
        )
    }

    function renderEngajamento(data) {
        const turmas = data?.emprestimos_por_turma || [];
        const series = data?.emprestimos_por_serie || [];

        Plotly.react(
            'engajamentoTurmaChart',
            [{
                x: turmas.map((i) => i.turma),
                y: turmas.map((i) => i.count),
                customdata: turmas.map((i) => i.turma),
                type: 'bar',
                marker: { color: '#0f4c5c' },
                hovertemplate: 'Turma: %{x}<br>Empréstimos: %{y}<extra></extra>'
            }],
            {
                margin: { t: 20, r: 10, b: 60, l: 45 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            },
            { displayModeBar: false, responsive: true }
        );

        Plotly.react(
            'engajamentoSerieChart',
            [{
                x: series.map((i) => i.serie),
                y: series.map((i) => i.count),
                customdata: series.map((i) => i.serie),
                type: 'bar',
                marker: { color: '#bb9457' },
                hovertemplate: 'Série: %{x}<br>Empréstimos: %{y}<extra></extra>'
            }],
            {
                margin: { t: 20, r: 10, b: 60, l: 45 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            },
            { displayModeBar: false, responsive: true }
        );
    }

    function renderPopularidade(data) {
        const livros = data?.top_livros || [];
        const tags = data?.distribuicao_tags || [];

        Plotly.react(
            'popularidadeLivrosChart',
            [{
                x: livros.map((i) => i.count),
                y: livros.map((i) => `${i.title} - ${i.author || 'Sem autor'}`),
                customdata: livros.map((i) => i.book_id),
                type: 'bar',
                orientation: 'h',
                marker: { color: '#457b9d' },
                hovertemplate: '%{y}<br>Empréstimos: %{x}<extra></extra>'
            }],
            {
                margin: { t: 10, r: 10, b: 40, l: 220 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            },
            { displayModeBar: false, responsive: true }
        );

        Plotly.react(
            'popularidadeTagsChart',
            [{
                labels: tags.map((i) => i.tag),
                values: tags.map((i) => i.count),
                customdata: tags.map((i) => i.tag),
                type: 'pie',
                hole: 0.45,
                textinfo: 'label+percent',
                hovertemplate: 'Tag: %{label}<br>Leituras: %{value}<extra></extra>'
            }],
            {
                margin: { t: 10, r: 10, b: 10, l: 10 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                showlegend: false
            },
            { displayModeBar: false, responsive: true }
        );
    }

    window.DashboardCharts = {
        renderEngajamento,
        renderPopularidade,
        renderTagsTop
    };
})();
