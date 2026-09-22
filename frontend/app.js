document.addEventListener("DOMContentLoaded", () => {
    // 1. Theme Management
    // Removed because we are strictly using the bright colorful white theme!

    // 2. Split-flap animation
    const animateSplitFlap = (targetValue) => {
        const flapContainer = document.getElementById("main-index-value");
        const chars = targetValue.toString().split("");
        
        flapContainer.innerHTML = "";
        
        chars.forEach((char, index) => {
            const digitEl = document.createElement("span");
            digitEl.className = "flap-digit";
            digitEl.textContent = "0";
            flapContainer.appendChild(digitEl);
            
            if (char === ".") {
                digitEl.textContent = ".";
                return;
            }
            
            let flips = 0;
            const maxFlips = 10 + (index * 5); 
            const interval = setInterval(() => {
                digitEl.textContent = Math.floor(Math.random() * 10);
                flips++;
                if (flips >= maxFlips) {
                    clearInterval(interval);
                    digitEl.textContent = char;
                }
            }, 50);
        });
    };

    const animateValue = (id, start, end, duration, decimals = 2) => {
        const obj = document.getElementById(id);
        if(!obj) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const easeProgress = progress * (2 - progress);
            const current = start + (end - start) * easeProgress;
            obj.textContent = decimals > 0 ? current.toFixed(decimals) : Math.floor(current);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.textContent = decimals > 0 ? end.toFixed(decimals) : end;
            }
        };
        window.requestAnimationFrame(step);
    };

    // 4. Data Fetching & Mock Data injection
    const fetchDashboardData = async () => {
        const apiStatus = document.getElementById("api-status");
        const statusText = apiStatus.querySelector(".status-text");
        
        try {
            const response = await fetch("http://localhost:8000/api/v1/inflation_vectors?base_year=2026", { signal: AbortSignal.timeout(1000) });
            if (!response.ok) throw new Error("API Error");
            const data = await response.json();
            
            apiStatus.classList.add("live");
            statusText.textContent = "Live Data";
            // Normal live parse goes here...
        } catch (error) {
            apiStatus.classList.remove("live");
            statusText.textContent = "Simulated Fallback";
            renderSimulatedData();
        }
    };

    const renderSimulatedData = () => {
        animateSplitFlap("112.45");
        
        // Header Stats
        animateValue("stat-core", 0, 108.20, 800, 2);
        const varianceVal = 0.06; 
        animateValue("stat-variance", 0, varianceVal, 800, 2);
        
        setTimeout(() => {
            if (varianceVal > 0.05) {
                const varEl = document.getElementById("stat-variance");
                varEl.classList.add("alert");
                varEl.textContent = varianceVal.toFixed(2) + " ⚠️";
            }
        }, 900);
        
        document.getElementById("stat-impact").textContent = "+14 bps";
        animateValue("stat-anomalies", 0, 3, 800, 0);

        // Superlative indices
        animateValue("idx-fisher", 0, 112.45, 1000, 2);
        animateValue("idx-tornqvist", 0, 112.80, 1000, 2);
        animateValue("idx-walsh", 0, 112.55, 1000, 2);

        // Trust Panel
        animateValue("trust-score-main", 0, 94, 1500, 0);
        
        const dims = [
            { label: "Freshness", score: 98 },
            { label: "Completeness", score: 95 },
            { label: "Route Coverage", score: 92 },
            { label: "Source Health", score: 100 },
            { label: "De-duplication", score: 88 },
            { label: "Outlier Cleanliness", score: 96 },
            { label: "Cross Consensus", score: 89 },
        ];
        
        const trustList = document.getElementById("trust-dimensions-list");
        let trustHTML = '';
        dims.forEach(d => {
            const color = d.score >= 90 ? 'var(--emerald)' : (d.score >= 80 ? 'var(--amber)' : 'var(--coral)');
            trustHTML += `
                <div class="trust-dim-row">
                    <div class="trust-dim-label">${d.label}</div>
                    <div class="trust-dim-bar-bg">
                        <div class="trust-dim-bar-fill" style="width: ${d.score}%; background-color: ${color}"></div>
                    </div>
                    <div class="trust-dim-score" style="color: ${color}">${d.score}</div>
                </div>
            `;
        });
        trustList.innerHTML = trustHTML;

        // Anomalies List
        const anomalyContainer = document.getElementById("anomaly-list");
        anomalyContainer.innerHTML = `
            <div class="anomaly-row severe">
                <div>
                    <div class="anomaly-desc">Spike: BOM-DEL</div>
                    <div class="anomaly-meta">Rs 18,500 (+140%)</div>
                </div>
                <div class="anomaly-meta">MAD Z-Score 4.2</div>
            </div>
            <div class="anomaly-row">
                <div>
                    <div class="anomaly-desc">Carrier Sync Issue</div>
                    <div class="anomaly-meta">AI-802 vs OTA Data</div>
                </div>
                <div class="anomaly-meta">Variance 12%</div>
            </div>
            <div class="anomaly-row">
                <div>
                    <div class="anomaly-desc">Volume Drop: HYD-MAA</div>
                    <div class="anomaly-meta">Seats < 100</div>
                </div>
                <div class="anomaly-meta">Flagged for Review</div>
            </div>
        `;

        renderCharts(false);
    };

    // Simulator Logic
    const initSimulator = () => {
        const sliders = ['fuel', 'demand', 'cap', 'season'];
        
        const calculateImpact = () => {
            const f = parseFloat(document.getElementById("sim-fuel").value);
            const d = parseFloat(document.getElementById("sim-demand").value);
            const c = parseFloat(document.getElementById("sim-cap").value);
            const s = parseFloat(document.getElementById("sim-season").value);

            // Mock mathematical formula replicating the FASTAPI POST request calculation
            // Real code would await fetch('/api/v1/simulate', { method: 'POST', body: JSON.stringify({...}) })
            let transportImpact = (f * 0.4) + (d * 0.3) + (c * 0.5) * s;
            let nationalImpact = transportImpact * 0.085; // 8.5% weight

            // Animation of simulator output (Signature Motion 2)
            const oldT = parseFloat(document.getElementById("res-transport").getAttribute("data-val") || 0);
            const oldN = parseFloat(document.getElementById("res-national").getAttribute("data-val") || 0);

            document.getElementById("res-transport").setAttribute("data-val", transportImpact);
            document.getElementById("res-national").setAttribute("data-val", nationalImpact);

            animateValue("res-transport", oldT, transportImpact, 400, 1);
            animateValue("res-national", oldN, nationalImpact, 400, 1);
            
            // Format labels with signs
            setTimeout(() => {
                document.getElementById("res-transport").textContent = (transportImpact > 0 ? "+" : "") + transportImpact.toFixed(1) + " bps";
                document.getElementById("res-national").textContent = (nationalImpact > 0 ? "+" : "") + nationalImpact.toFixed(1) + " bps";
            }, 410);
        };

        sliders.forEach(id => {
            const input = document.getElementById("sim-" + id);
            const valDisplay = document.getElementById("val-" + id);
            input.addEventListener("input", (e) => {
                valDisplay.textContent = e.target.value;
                calculateImpact();
            });
        });
    };

    // Chart.js Configuration
    let inflationChartInstance = null;
    let routeChartInstance = null;
    let regionalChartInstance = null;

    const renderCharts = (isThemeChange = false) => {
        const root = document.documentElement;
        const style = getComputedStyle(root);
        
        const getVar = (name) => style.getPropertyValue(name).trim();
        const cyan = getVar('--cyan'), amber = getVar('--amber'), violet = getVar('--violet'), 
              emerald = getVar('--emerald'), text3 = getVar('--text-3'), border = getVar('--border'), coral = getVar('--coral');

        Chart.defaults.color = text3;
        Chart.defaults.font.family = "'Inter', sans-serif";

        if (inflationChartInstance) inflationChartInstance.destroy();
        if (routeChartInstance) routeChartInstance.destroy();
        if (regionalChartInstance) regionalChartInstance.destroy();

        // 1. Inflation Temporal Matrix
        inflationChartInstance = new Chart(document.getElementById('inflationChart').getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [
                    { label: 'Headline', data: [100, 101.2, 102.5, 102.8, 104.1, 105.0, 107.2, 108.5, 109.1, 110.5, 111.8, 112.45], borderColor: cyan, borderWidth: 2, tension: 0.4, pointRadius: 0 },
                    { label: 'Core', data: [100, 100.8, 101.5, 102.0, 102.5, 103.2, 104.0, 105.2, 106.0, 107.1, 107.8, 108.2], borderColor: violet, borderWidth: 2, tension: 0.4, pointRadius: 0 },
                    { label: 'Törnqvist', data: [100, 101.3, 102.6, 102.9, 104.2, 105.2, 107.5, 108.7, 109.4, 110.8, 112.1, 112.8], borderColor: emerald, borderWidth: 2, borderDash: [5, 5], tension: 0.4, pointRadius: 0 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: { duration: isThemeChange ? 0 : 2000, easing: 'easeOutQuart' },
                interaction: { mode: 'index', intersect: false },
                scales: { x: { grid: { color: border } }, y: { grid: { color: border } } }
            }
        });

        // 2. Route Comparison
        routeChartInstance = new Chart(document.getElementById('routeChart').getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['DEL-BOM', 'BLR-DEL', 'BOM-BLR', 'HYD-MAA'],
                datasets: [{ data: [12.5, 8.2, 15.4, 4.1], backgroundColor: [amber, cyan, emerald, violet] }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: { duration: isThemeChange ? 0 : 1500, easing: 'easeOutQuart' },
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false } }, y: { grid: { color: border } } }
            }
        });

        // 3. Regional Sub-Indices
        regionalChartInstance = new Chart(document.getElementById('regionalChart').getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Delhi NCR', 'Mumbai MMR', 'Bengaluru', 'Eastern Hub', 'Southern Hub'],
                datasets: [{ data: [115.2, 118.4, 110.1, 104.5, 108.9], backgroundColor: cyan }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                animation: { duration: isThemeChange ? 0 : 1500, easing: 'easeOutQuart' },
                plugins: { legend: { display: false } },
                scales: { x: { grid: { color: border } }, y: { grid: { display: false } } }
            }
        });
    };

    // Start
    fetchDashboardData();
    initSimulator();
});
