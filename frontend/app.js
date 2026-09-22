document.addEventListener("DOMContentLoaded", () => {
    // 1. Theme Management
    const themeToggle = document.getElementById("theme-toggle");
    const htmlEl = document.documentElement;
    
    // Load persisted theme
    try {
        const savedTheme = localStorage.getItem("aerofare-theme");
        if (savedTheme) {
            htmlEl.setAttribute("data-theme", savedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            htmlEl.setAttribute("data-theme", "light");
        }
    } catch (e) {
        console.warn("localStorage not accessible");
    }

    themeToggle.addEventListener("click", () => {
        const currentTheme = htmlEl.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        htmlEl.setAttribute("data-theme", newTheme);
        try {
            localStorage.setItem("aerofare-theme", newTheme);
        } catch (e) {}
        // Refresh charts for theme colors
        renderCharts(true);
    });

    // 2. Split-flap animation (Signature Moment 1)
    const animateSplitFlap = (targetValue) => {
        const flapContainer = document.getElementById("main-index-value");
        const chars = targetValue.toString().split("");
        
        flapContainer.innerHTML = "";
        
        chars.forEach((char, index) => {
            const digitEl = document.createElement("span");
            digitEl.className = "flap-digit";
            digitEl.textContent = "0";
            flapContainer.appendChild(digitEl);
            
            // If it's a decimal, just show it
            if (char === ".") {
                digitEl.textContent = ".";
                return;
            }
            
            // Random flipping
            let flips = 0;
            const maxFlips = 10 + (index * 5); // Staggered stops
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

    // 3. Stat Strip Count Up
    const animateValue = (id, start, end, duration, decimals = 2) => {
        const obj = document.getElementById(id);
        if(!obj) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // Ease out quad
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

    // 4. Data Fetching
    const fetchDashboardData = async () => {
        const apiStatus = document.getElementById("api-status");
        const statusText = apiStatus.querySelector(".status-text");
        
        try {
            // Attempt real fetch
            const response = await fetch("http://localhost:8000/api/v1/inflation_vectors?base_year=2026", { signal: AbortSignal.timeout(2000) });
            if (!response.ok) throw new Error("API Error");
            const data = await response.json();
            
            apiStatus.classList.add("live");
            statusText.textContent = "Live Data";
            
            // Wait for split-flap animation before setting stats
            animateSplitFlap(data.headline_index || "112.45");
            // More integration logic...
        } catch (error) {
            // Fallback to simulated data
            apiStatus.classList.remove("live");
            statusText.textContent = "Simulated Fallback";
            
            renderSimulatedData();
        }
    };

    const renderSimulatedData = () => {
        // Hero
        animateSplitFlap("112.45");
        
        // Stats
        animateValue("stat-core", 0, 108.20, 800, 2);
        const varianceVal = 0.06; // Intentionally triggering the alert threshold
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

    // Chart.js Configuration
    let inflationChartInstance = null;
    let routeChartInstance = null;

    const renderCharts = (isThemeChange = false) => {
        const root = document.documentElement;
        const style = getComputedStyle(root);
        
        const getVar = (name) => style.getPropertyValue(name).trim();
        
        const cyan = getVar('--cyan');
        const amber = getVar('--amber');
        const violet = getVar('--violet');
        const emerald = getVar('--emerald');
        const text3 = getVar('--text-3');
        const border = getVar('--border');

        Chart.defaults.color = text3;
        Chart.defaults.font.family = "'Inter', sans-serif";

        if (inflationChartInstance) inflationChartInstance.destroy();
        if (routeChartInstance) routeChartInstance.destroy();

        const ctxInf = document.getElementById('inflationChart').getContext('2d');
        inflationChartInstance = new Chart(ctxInf, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [
                    {
                        label: 'Headline (Fisher)',
                        data: [100, 101.2, 102.5, 102.8, 104.1, 105.0, 107.2, 108.5, 109.1, 110.5, 111.8, 112.45],
                        borderColor: cyan,
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Core (Trimmed)',
                        data: [100, 100.8, 101.5, 102.0, 102.5, 103.2, 104.0, 105.2, 106.0, 107.1, 107.8, 108.2],
                        borderColor: violet,
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Törnqvist Val',
                        data: [100, 101.3, 102.6, 102.9, 104.2, 105.2, 107.5, 108.7, 109.4, 110.8, 112.1, 112.8],
                        borderColor: emerald,
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    // Only animate on first load
                    duration: isThemeChange ? 0 : 2000, 
                    easing: 'easeOutQuart'
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: { grid: { color: border } },
                    y: { grid: { color: border } }
                }
            }
        });

        const ctxRoute = document.getElementById('routeChart').getContext('2d');
        routeChartInstance = new Chart(ctxRoute, {
            type: 'bar',
            data: {
                labels: ['DEL-BOM', 'BLR-DEL', 'BOM-BLR', 'HYD-MAA'],
                datasets: [{
                    label: 'YoY Price %',
                    data: [12.5, 8.2, 15.4, 4.1],
                    backgroundColor: [amber, cyan, emerald, violet]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: isThemeChange ? 0 : 1500,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: border } }
                }
            }
        });
    };

    // Start
    fetchDashboardData();
});
