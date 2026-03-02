document.addEventListener('DOMContentLoaded', () => {
    const dataBody = document.getElementById('data-body');
    const countdownEl = document.getElementById('countdown');
    const recordCountEl = document.getElementById('record-count');
    const searchInput = document.getElementById('search-input');
    const refreshBtn = document.getElementById('refresh-btn');

    const marketPriceEl = document.getElementById('market-price');
    const priceDriftEl = document.getElementById('price-drift');

    const searchGlobal = document.getElementById('search-global');
    const filterCategory = document.getElementById('filter-category');
    const filterPriority = document.getElementById('filter-priority');
    const filterStatus = document.getElementById('filter-status');
    const maxValEl = document.getElementById('max-val');
    const countdownBar = document.getElementById('countdown-bar');
    const resetBtn = document.getElementById('reset-btn');

    const dropThresholdEl = document.getElementById('drop-threshold');
    const riseThresholdEl = document.getElementById('rise-threshold');

    let allData = [];
    let prevBasePrice = 0;
    let refreshTimer = 5;
    let countdownInterval;
    let priceChart;

    // Initialize Chart.js
    function initChart() {
        const ctx = document.getElementById('priceChart').getContext('2d');
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Market Price',
                    borderColor: '#2f81f7',
                    backgroundColor: 'rgba(47, 129, 247, 0.1)',
                    borderWidth: 2,
                    data: [],
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#8b949e', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // Fetch data from Flask API
    async function fetchData() {
        try {
            const [dataRes, historyRes] = await Promise.all([
                fetch('/api/data'),
                fetch('/api/history')
            ]);

            const result = await dataRes.json();
            const history = await historyRes.json();

            allData = result.data;
            const currentBasePrice = result.base_price;

            // Update Stats
            marketPriceEl.textContent = currentBasePrice.toFixed(2);
            recordCountEl.textContent = allData.length.toLocaleString();

            // Calculate Highest Value
            const maxVal = Math.max(...allData.map(d => d.price));
            maxValEl.textContent = `$${maxVal.toLocaleString()}`;

            // Price drift indicator
            if (prevBasePrice > 0) {
                const diff = currentBasePrice - prevBasePrice;
                if (diff > 0) {
                    priceDriftEl.textContent = `+${diff.toFixed(2)} ↑`;
                    priceDriftEl.style.color = '#3fb950';
                } else if (diff < 0) {
                    priceDriftEl.textContent = `${diff.toFixed(2)} ↓`;
                    priceDriftEl.style.color = '#f85149';
                } else {
                    priceDriftEl.textContent = 'Stable';
                    priceDriftEl.style.color = '#8b949e';
                }
            }
            prevBasePrice = currentBasePrice;

            // Update Chart
            priceChart.data.labels = history.map(h => h.time);
            priceChart.data.datasets[0].data = history.map(h => h.price);
            priceChart.update('none'); // Update without animation for performance

            renderData();
        } catch (error) {
            console.error('Error:', error);
            dataBody.innerHTML = `<tr><td colspan="7" class="loading-state">Syncing error...</td></tr>`;
        }
    }

    // Render data to the table
    function renderData() {
        const query = searchGlobal.value.toLowerCase();
        const cat = filterCategory.value;
        const prio = filterPriority.value;
        const stat = filterStatus.value;

        const filtered = allData.filter(item => {
            const matchesGlobal = item.name.toLowerCase().includes(query) || item.id.toLowerCase().includes(query);
            const matchesCat = !cat || item.metadata.category === cat;
            const matchesPrio = !prio || item.metadata.priority === prio;
            const matchesStat = !stat || item.status === stat;
            return matchesGlobal && matchesCat && matchesPrio && matchesStat;
        });

        // Displaying only first 100 items for performance
        const display = filtered.slice(0, 100);

        if (display.length === 0) {
            dataBody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:3rem">No results found</td></tr>`;
            return;
        }

        dataBody.innerHTML = display.map(item => `
            <tr>
                <td style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-secondary)">${item.id.substring(0, 8)}</td>
                <td style="font-weight:600">${item.name}</td>
                <td style="font-family:var(--font-mono)">${item.value}</td>
                <td style="font-family:var(--font-mono); color:var(--accent-color); font-weight:600">$${item.price.toLocaleString()}</td>
                <td>${item.metadata.category}</td>
                <td><span class="tag ${item.metadata.priority}">${item.metadata.priority}</span></td>
                <td><span class="status-pill status-${item.status}">${item.status}</span></td>
            </tr>
        `).join('');
    }

    // Timer logic
    function startCountdown() {
        clearInterval(countdownInterval);
        refreshTimer = 5;
        countdownEl.textContent = `${refreshTimer}s`;
        countdownBar.style.width = '100%';

        countdownInterval = setInterval(() => {
            refreshTimer--;
            countdownEl.textContent = `${refreshTimer}s`;

            // Update progress bar
            const percent = (refreshTimer / 5) * 100;
            countdownBar.style.width = `${percent}%`;

            if (refreshTimer <= 0) {
                fetchData();
                refreshTimer = 5;
                countdownBar.style.width = '100%';
            }
        }, 1000);
    }

    // Event Listeners
    [searchGlobal, filterCategory, filterPriority, filterStatus].forEach(el => {
        el.addEventListener('input', renderData);
    });

    resetBtn.addEventListener('click', () => {
        searchGlobal.value = '';
        filterCategory.value = '';
        filterPriority.value = '';
        filterStatus.value = '';
        renderData();
    });

    refreshBtn.addEventListener('click', () => { fetchData(); startCountdown(); });

    // Fetch Thresholds
    async function fetchThresholds() {
        try {
            const res = await fetch('/api/thresholds');
            if (res.ok) {
                const data = await res.json();
                if (data.price_drop_threshold) {
                    dropThresholdEl.value = data.price_drop_threshold;
                }
                if (data.price_rise_threshold) {
                    riseThresholdEl.value = data.price_rise_threshold;
                }
            }
        } catch (error) {
            console.error('Error fetching thresholds:', error);
        }
    }

    // Update Thresholds
    async function updateThresholds() {
        try {
            await fetch('/api/thresholds', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    price_drop_threshold: dropThresholdEl.value,
                    price_rise_threshold: riseThresholdEl.value
                })
            });
        } catch (error) {
            console.error('Error updating thresholds:', error);
        }
    }

    dropThresholdEl.addEventListener('change', updateThresholds);
    riseThresholdEl.addEventListener('change', updateThresholds);

    // Initial Fetch
    initChart();
    fetchData();
    fetchThresholds();
    startCountdown();
});
