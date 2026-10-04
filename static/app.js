/* ═══════════════════════════════════════════════════════════
   🧥 Wearther — Frontend Application
   ═══════════════════════════════════════════════════════════ */

// ─── State ───
let currentWeather = null;
let currentCity = localStorage.getItem('lastCity') || 'Istanbul';
let pinnedCities = JSON.parse(localStorage.getItem('pinnedCities') || '[]');

const FEEDBACK_MAP = {
    '-1': '🥶 Üşüdüm',
    '0': '👌 Tam Kararında',
    '1': '🥵 Terledim'
};


// ─── Initialization ───
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupThemeToggle();
    document.getElementById('sehir-input').value = currentCity;
    setupTabs();
    setupSidebar();
    setupCitySearch();
    renderPinnedCities();
    setupForm();
    await loadOptions();
    await refreshData();
}

// ─── Theme Management ───
const THEME_STORAGE_KEY = 'wearther_theme';

function getPreferredTheme() {
    try {
        const saved = localStorage.getItem(THEME_STORAGE_KEY);
        if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {}
    return 'dark'; // Varsayılan: Koyu tema
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) {
        document.body.setAttribute('data-theme', theme);
    }
    try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {}

    const toggleBtn = document.getElementById('theme-toggle-btn');
    const toggleLabel = document.getElementById('theme-toggle-label');
    if (toggleBtn) {
        toggleBtn.setAttribute('data-current-theme', theme);
        toggleBtn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }
    if (toggleLabel) {
        toggleLabel.textContent = theme === 'dark' ? 'Koyu Tema' : 'Açık Tema';
    }
}

function setupThemeToggle() {
    const currentTheme = getPreferredTheme();
    applyTheme(currentTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const active = document.documentElement.getAttribute('data-theme') || 'light';
            const next = active === 'dark' ? 'light' : 'dark';
            applyTheme(next);
        });
    }
}


// ═══════════════════════════════════════════
// TAB MANAGEMENT
// ═══════════════════════════════════════════

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            // Deactivate all
            document.querySelectorAll('.tab').forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

            // Activate matching tabs (both desktop and mobile)
            document.querySelectorAll('.tab[data-tab="' + targetTab + '"]').forEach(t => {
                t.classList.add('active');
                t.setAttribute('aria-selected', 'true');
            });

            const panelId = 'panel-' + targetTab;
            document.getElementById(panelId).classList.add('active');

            // Load history data lazily when switching to that tab
            if (targetTab === 'gecmis') {
                loadHistory();
            }

            // Close sidebar on mobile
            if (window.innerWidth <= 768) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebar-overlay');
                if (sidebar) sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('active');
            }
        });
    });
}


// ═══════════════════════════════════════════
// SIDEBAR
// ═══════════════════════════════════════════

function setupSidebar() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const body = document.body;

    toggle.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        } else {
            body.classList.toggle('sidebar-closed');
        }
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }
    });
}

function setupCitySearch() {
    const input = document.getElementById('sehir-input');
    const btn = document.getElementById('sehir-btn');

    btn.addEventListener('click', () => {
        const city = input.value.trim();
        if (city) {
            currentCity = city;
            refreshData();
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const city = input.value.trim();
            if (city) {
                currentCity = city;
                refreshData();
            }
        }
    });

    const pinBtn = document.getElementById('pin-btn');
    if (pinBtn) {
        pinBtn.addEventListener('click', () => {
            const city = currentCity;
            if (!pinnedCities.includes(city)) {
                if (pinnedCities.length >= 3) {
                    showToast('En fazla 3 şehir sabitleyebilirsiniz.', 'error');
                    return;
                }
                pinnedCities.push(city);
                localStorage.setItem('pinnedCities', JSON.stringify(pinnedCities));
                renderPinnedCities();
                showToast(city + ' sabitlendi 📌', 'success');
            } else {
                showToast('Bu şehir zaten sabitli.', 'error');
            }
        });
    }
}

function renderPinnedCities() {
    const container = document.getElementById('pinned-cities');
    if (!container) return;

    if (pinnedCities.length === 0) {
        container.innerHTML = '<div style="font-size:13px; color:rgba(233,213,255,0.5); font-style:italic; padding: 4px 0;">Henüz sabitlenmiş bir şehir yok.</div>';
        return;
    }

    container.innerHTML = pinnedCities.map(city => `
        <div class="pinned-city-item">
            <span class="pinned-city-name" onclick="loadPinnedCity('${city}')">${city}</span>
            <button class="pinned-city-remove" onclick="removePinnedCity('${city}')" title="Kaldır"><i class="fas fa-xmark"></i></button>
        </div>
    `).join('');
}

window.loadPinnedCity = function (city) {
    document.getElementById('sehir-input').value = city;
    currentCity = city;
    refreshData();
};

window.removePinnedCity = function (city) {
    pinnedCities = pinnedCities.filter(c => c !== city);
    localStorage.setItem('pinnedCities', JSON.stringify(pinnedCities));
    renderPinnedCities();
};


// ═══════════════════════════════════════════
// DATA LOADING
// ═══════════════════════════════════════════

async function refreshData(showLoadingScreen = true) {
    if (showLoadingScreen) {
        setLoading(true);
        setContent(false);
        hideError();
    }

    try {
        const res = await fetch('api/oneri?sehir=' + encodeURIComponent(currentCity));
        if (!res.ok) throw new Error('API hatası');
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        currentCity = data.hava.sehir;
        document.getElementById('sehir-input').value = currentCity;
        localStorage.setItem('lastCity', currentCity);

        currentWeather = data.hava;
        renderWeatherCard(data.hava);
        renderMiniWeatherCard(data.hava);
        renderRecommendations(data.oneri, data.hava);
        prefillForm(data.oneri);

        await loadStats();

        if (showLoadingScreen) {
            setLoading(false);
            setContent(true);
        }
    } catch (err) {
        console.error('Veri yüklenirken hata:', err);
        if (showLoadingScreen) {
            setLoading(false);
            showError();
        } else {
            showToast('Veri güncellenirken hata oluştu.', 'error');
        }
    }
}

async function loadStats() {
    try {
        const res = await fetch('api/istatistikler');
        const stats = await res.json();
        renderSidebarStats(stats);
    } catch (err) {
        console.error('İstatistik yüklenirken hata:', err);
    }
}

async function loadHistory() {
    const container = document.getElementById('gecmis-content');
    container.innerHTML = '<div class="loading-screen" style="min-height:30vh"><div class="spinner"></div></div>';

    try {
        const [histRes, statsRes] = await Promise.all([
            fetch('api/gecmis'),
            fetch('api/istatistikler')
        ]);
        const history = await histRes.json();
        const stats = await statsRes.json();

        if (history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="es-icon">📭</div>
                    <h3>Henüz hiç kayıt yok</h3>
                    <p>"Bugün Ne Giydin?" sekmesinden ilk kaydını gir!</p>
                </div>
            `;
            return;
        }

        // Stats cards
        let html = `
            <div class="stats-grid">
                <div class="stat-card" style="animation-delay:0.05s">
                    <div class="sc-value">${stats.toplam}</div>
                    <div class="sc-label">Toplam Kayıt</div>
                </div>
                <div class="stat-card" style="animation-delay:0.1s">
                    <div class="sc-value">${stats.ort_sicaklik ?? '-'}°</div>
                    <div class="sc-label">Ort. Sıcaklık</div>
                </div>
                <div class="stat-card" style="animation-delay:0.15s">
                    <div class="sc-value">${stats.min_sicaklik ?? '-'}°</div>
                    <div class="sc-label">Min Sıcaklık</div>
                </div>
                <div class="stat-card" style="animation-delay:0.2s">
                    <div class="sc-value">${stats.max_sicaklik ?? '-'}°</div>
                    <div class="sc-label">Max Sıcaklık</div>
                </div>
            </div>
        `;

        // Table
        const reversed = [...history].reverse();
        html += `
            <div class="data-table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>📅 Tarih</th>
                            <th>🌡️ Sıcaklık</th>
                            <th>🤒 Hissedilen</th>
                            <th>💧 Nem</th>
                            <th>💨 Rüzgar</th>
                            <th>👕 Üst</th>
                            <th>👖 Alt</th>
                            <th>🧥 Dış</th>
                            <th>👟 Ayakkabı</th>
                            <th>🧣 Ekstra</th>
                            <th>🎯 Geri Bildirim</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${reversed.map(row => `
                            <tr>
                                <td>${row.Tarih}</td>
                                <td>${row.Sicaklik}°C</td>
                                <td>${row.Hissedilen}°C</td>
                                <td>%${row.Nem}</td>
                                <td>${row.Ruzgar} km/h</td>
                                <td>${row.Ust_Giyim}</td>
                                <td>${row.Alt_Giyim}</td>
                                <td>${row.Dis_Giyim}</td>
                                <td>${row.Ayakkabi}</td>
                                <td>${row.Ekstra}</td>
                                <td>${FEEDBACK_MAP[String(row.Geri_Bildirim)] || '❓'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        // Actions
        html += `
            <div class="actions-row">
                <a href="api/indir" class="btn-secondary" download><i class="fas fa-file-csv"></i> Verileri CSV Olarak İndir</a>
            </div>
            <details class="delete-section">
                <summary><i class="fas fa-trash-can"></i> Son Kaydı Sil</summary>
                <div class="delete-content">
                    <p class="warning-text">⚠️ Bu işlem geri alınamaz!</p>
                    <button class="btn-danger" onclick="deleteLastRecord()"><i class="fas fa-trash-can"></i> Son kaydı sil</button>
                </div>
            </details>
        `;

        container.innerHTML = html;

    } catch (err) {
        console.error('Geçmiş yüklenirken hata:', err);
        container.innerHTML = '<div class="info-box" style="border-left-color:#ef4444">❌ Veriler yüklenirken hata oluştu.</div>';
    }
}


// ═══════════════════════════════════════════
// RENDER FUNCTIONS & DYNAMIC WEATHER ATMOSPHERE
// ═══════════════════════════════════════════

let _wcAnimId = null;
let _wcResizeObs = null;

function _parseWeather(hava) {
    const desc = (hava.aciklama || '').toLowerCase();
    const icon = hava.ikon || '01d';
    const isNight = icon.endsWith('n');
    const wind = parseFloat(hava.ruzgar) || 0;
    const humidity = parseInt(hava.nem) || 50;

    let cond = 'clear', rain = 'none';

    if (desc.includes('fırtına') || desc.includes('gök gürültü') || icon.startsWith('11')) {
        cond = 'thunderstorm'; rain = 'heavy';
    } else if (desc.includes('kar') || icon.startsWith('13')) {
        cond = 'snow';
    } else if (desc.includes('yağmur') || desc.includes('sağanak') || desc.includes('çise') || icon.startsWith('09') || icon.startsWith('10')) {
        cond = 'rain';
        rain = desc.includes('hafif') || desc.includes('çise') ? 'light'
            : desc.includes('şiddetli') || desc.includes('sağanak') || humidity > 85 ? 'heavy'
                : 'moderate';
    } else if (desc.includes('sis') || desc.includes('pus') || icon.startsWith('50')) {
        cond = 'mist';
    } else if (desc.includes('kapalı') || desc.includes('çok bulutlu')) {
        cond = 'clouds';
    } else if (desc.includes('parçalı') || icon.startsWith('03')) {
        cond = 'scattered-clouds';
    } else if (desc.includes('bulut') || icon.startsWith('02')) {
        cond = 'few-clouds';
    } else if (icon.startsWith('04')) {
        cond = 'clouds';
    }

    let theme, sun = false, moon = false, cloudCount = 0;
    switch (cond) {
        case 'clear': theme = isNight ? 'wc-theme-clear-night' : 'wc-theme-clear-day'; if (isNight) moon = true; else sun = true; break;
        case 'few-clouds': theme = isNight ? 'wc-theme-few-clouds-night' : 'wc-theme-few-clouds-day'; cloudCount = 2; if (isNight) moon = true; else sun = true; break;
        case 'scattered-clouds': theme = isNight ? 'wc-theme-few-clouds-night' : 'wc-theme-few-clouds-day'; cloudCount = 3; if (isNight) moon = true; else sun = true; break;
        case 'clouds': theme = 'wc-theme-clouds'; cloudCount = 4; break;
        case 'rain': theme = 'wc-theme-rain'; cloudCount = 5; break;
        case 'thunderstorm': theme = 'wc-theme-thunderstorm'; cloudCount = 5; break;
        case 'snow': theme = 'wc-theme-snow'; cloudCount = 4; break;
        case 'mist': theme = 'wc-theme-mist'; cloudCount = 2; if (isNight) moon = true; else sun = true; break;
        default: theme = 'wc-theme-clear-day'; sun = true;
    }
    return { cond, isNight, wind, humidity, rain, theme, sun, moon, cloudCount };
}

function renderWeatherCard(hava) {
    const dateStr = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
    const w = _parseWeather(hava);

    let bgHTML = '';

    // Sun or Moon
    if (w.sun) {
        bgHTML += `<div class="wc-sun-container"><div class="wc-sun-glow"></div><div class="wc-sun-rays"></div><div class="wc-sun-core"></div></div>`;
    }
    if (w.moon) {
        bgHTML += `<div class="wc-moon-container"><div class="wc-moon-core"></div></div>`;
    }

    // Clouds
    if (w.cloudCount > 0) {
        // Rüzgara göre bulut animasyon hızı çarpanı (az rüzgar = yavaş = büyük çarpan)
        // 10 km/h standart hız kabul ediyoruz
        const windFactor = Math.max(0.4, Math.min(3.5, 12 / (w.wind || 10)));
        let cloudsHTML = '';
        const baseDurs = [50, 35, 24, 40, 60];
        for (let i = 1; i <= w.cloudCount; i++) {
            // we have up to 5 classes: wc-cloud-1, ..., wc-cloud-5
            const cls = ((i - 1) % 5) + 1;
            const dur = (baseDurs[cls - 1] * windFactor).toFixed(1);
            cloudsHTML += `<div class="wc-cloud wc-cloud-${cls}" style="animation-duration: ${dur}s;"></div>`;
        }
        bgHTML += `<div class="wc-clouds-container">${cloudsHTML}</div>`;
    }

    document.getElementById('weather-card-container').innerHTML = `
        <div class="weather-card ${w.theme}">
            ${bgHTML}
            <canvas id="wc-canvas" class="wc-canvas"></canvas>
            <div class="wc-content">
                <div class="wc-header">${hava.emoji} ${hava.sehir} — ${hava.aciklama}</div>
                <div class="wc-temp">${hava.sicaklik}°C</div>
                <div class="wc-details">
                    <span>🌡️ Hissedilen: ${hava.hissedilen}°C</span>
                    <span>💧 Nem: ${hava.nem}%</span>
                    <span>💨 Rüzgar: ${hava.ruzgar} km/h</span>
                    <span>📅 ${dateStr}</span>
                </div>
            </div>
        </div>
    `;

    _initWeatherCanvas(w);
}

function _initWeatherCanvas(w) {
    if (_wcAnimId) { cancelAnimationFrame(_wcAnimId); _wcAnimId = null; }
    if (_wcResizeObs) { _wcResizeObs.disconnect(); _wcResizeObs = null; }

    const canvas = document.getElementById('wc-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const card = canvas.closest('.weather-card');
    if (!card) return;

    function resize() {
        const r = card.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) { canvas.width = r.width; canvas.height = r.height; }
    }
    resize();
    _wcResizeObs = new ResizeObserver(resize);
    _wcResizeObs.observe(card);

    const { cond, wind, rain, humidity } = w;
    const drops = [], splashes = [], streaks = [], flakes = [], motes = [], lightnings = [];

    function createLightning() {
        const x = canvas.width * 0.1 + Math.random() * canvas.width * 0.8;
        const bolt = [];
        let cx = x, cy = 0;
        bolt.push({ x: cx, y: cy });
        while (cy < canvas.height) {
            cx += (Math.random() - 0.5) * 60; // branch left/right
            cy += 15 + Math.random() * 35; // branch down
            bolt.push({ x: cx, y: cy });
        }
        lightnings.push({ path: bolt, life: 1 });
    }

    // Rain
    if (cond === 'rain' || cond === 'thunderstorm') {
        const n = rain === 'light' ? 15 : rain === 'heavy' ? 65 : 32;
        const sm = rain === 'light' ? 0.5 : rain === 'heavy' ? 0.8 : 0.6;
        for (let i = 0; i < n; i++) drops.push({
            x: Math.random() * (canvas.width + 160) - 80, y: Math.random() * canvas.height,
            len: (14 + Math.random() * 16) * sm, speed: (14 + Math.random() * 8) * sm,
            op: 0.35 + Math.random() * 0.45, w: rain === 'heavy' ? 1.5 + Math.random() * 0.8 : 1.1 + Math.random() * 0.5
        });
    }

    // Wind streaks (>= 14 km/h)
    if (wind >= 14) {
        const n = wind >= 38 ? 7 : wind >= 25 ? 5 : 3;
        for (let i = 0; i < n; i++) streaks.push({
            x: Math.random() * canvas.width, y: 15 + Math.random() * (canvas.height - 30),
            len: 90 + Math.random() * 130, speed: 3.5 + (wind / 10) * 1.8 + Math.random() * 2,
            op: 0.28 + Math.random() * 0.4, seed: Math.random() * 100, thick: 1.2 + Math.random() * 1.3
        });
    }

    // Snow
    if (cond === 'snow') for (let i = 0; i < 55; i++) flakes.push({
        x: Math.random() * canvas.width, y: Math.random() * canvas.height,
        r: 1.5 + Math.random() * 2.5, speed: 0.8 + Math.random() * 1.6,
        wb: Math.random() * Math.PI * 2, ws: 0.02 + Math.random() * 0.03, op: 0.4 + Math.random() * 0.5
    });

    // Sun motes
    if ((cond === 'clear' || cond === 'few-clouds') && !w.isNight) for (let i = 0; i < 16; i++) motes.push({
        x: canvas.width * 0.4 + Math.random() * canvas.width * 0.6, y: Math.random() * canvas.height,
        r: 1.2 + Math.random() * 2.2, sy: 0.25 + Math.random() * 0.45, op: 0.25 + Math.random() * 0.5, p: Math.random() * Math.PI * 2
    });

    let lFlash = 0, lNext = 140 + Math.random() * 200, lFrame = 0;

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const drift = Math.max(-0.55, Math.min(0.75, (wind - 5) / 45));

        // Lightning
        if (cond === 'thunderstorm') {
            lFrame++;
            if (lFrame >= lNext) {
                lFlash = 0.6;
                lNext = lFrame + 120 + Math.random() * 200;
                createLightning();
                if (Math.random() > 0.6) createLightning(); // bazen çift yıldırım
            }
            if (lFlash > 0) {
                ctx.fillStyle = `rgba(255,255,255,${lFlash * 0.4})`; // soft background flash
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                lFlash -= 0.05;
            }

            // Draw bolts
            for (let i = lightnings.length - 1; i >= 0; i--) {
                const l = lightnings[i];
                ctx.beginPath();
                ctx.moveTo(l.path[0].x, l.path[0].y);
                for (let j = 1; j < l.path.length; j++) {
                    ctx.lineTo(l.path[j].x, l.path[j].y);
                }

                // Bolt outer glow
                ctx.strokeStyle = `rgba(220, 230, 255, ${l.life * 0.6})`;
                ctx.lineWidth = 6 + Math.random() * 4;
                ctx.stroke();

                // Bolt core
                ctx.strokeStyle = `rgba(255, 255, 255, ${l.life})`;
                ctx.lineWidth = 1.5 + Math.random() * 2;
                ctx.stroke();

                l.life -= 0.1; // kaybolma hızı
                if (l.life <= 0) lightnings.splice(i, 1);
            }
        }

        // Rain
        for (const d of drops) {
            const vx = drift * d.speed, vy = d.speed;
            ctx.strokeStyle = `rgba(186,230,253,${d.op})`; ctx.lineWidth = d.w;
            ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - vx * 0.6, d.y - vy * 0.6); ctx.stroke();
            d.x += vx; d.y += vy;
            if (d.y >= canvas.height) {
                if (rain !== 'light' && splashes.length < 35) splashes.push({ x: d.x, y: canvas.height - 2, vx: (Math.random() - 0.5) * 3, vy: -(1.5 + Math.random() * 2), life: 1 });
                d.y = -20; d.x = Math.random() * (canvas.width + 160) - 80;
            }
        }
        for (let i = splashes.length - 1; i >= 0; i--) {
            const s = splashes[i];
            ctx.fillStyle = `rgba(186,230,253,${s.life * 0.6})`; ctx.beginPath(); ctx.arc(s.x, s.y, 1, 0, Math.PI * 2); ctx.fill();
            s.x += s.vx; s.y += s.vy; s.vy += 0.22; s.life -= 0.08;
            if (s.life <= 0) splashes.splice(i, 1);
        }

        // Wind streaks
        for (const st of streaks) {
            st.x += st.speed;
            if (st.x - st.len > canvas.width) { st.x = -st.len - Math.random() * 70; st.y = 15 + Math.random() * (canvas.height - 30); }
            const g = ctx.createLinearGradient(st.x - st.len, st.y, st.x, st.y);
            g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.65, `rgba(255,255,255,${st.op * 0.5})`); g.addColorStop(1, `rgba(255,255,255,${st.op})`);
            ctx.strokeStyle = g; ctx.lineWidth = st.thick; ctx.beginPath();
            const sx = st.x - st.len;
            ctx.moveTo(sx, st.y + Math.sin(sx * 0.025 + st.seed) * 5);
            for (let px = sx; px <= st.x; px += 10) ctx.lineTo(px, st.y + Math.sin(px * 0.025 + st.seed) * 5);
            ctx.stroke();
        }

        // Snow
        for (const f of flakes) {
            f.wb += f.ws; f.x += Math.sin(f.wb) * 0.8 + (wind / 35); f.y += f.speed;
            if (f.y > canvas.height + 10) { f.y = -10; f.x = Math.random() * canvas.width; }
            if (f.x > canvas.width + 10) f.x = -10; if (f.x < -10) f.x = canvas.width + 10;
            ctx.fillStyle = `rgba(255,255,255,${f.op})`; ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fill();
        }

        // Sun motes
        for (const m of motes) {
            m.p += 0.04; m.x += Math.cos(m.p) * 0.3; m.y -= m.sy;
            if (m.y < -10) { m.y = canvas.height + 10; m.x = canvas.width * 0.3 + Math.random() * canvas.width * 0.7; }
            const o = m.op * (0.6 + 0.4 * Math.sin(m.p));
            ctx.fillStyle = `rgba(254,240,138,${o})`; ctx.shadowColor = 'rgba(251,191,36,0.5)'; ctx.shadowBlur = 5;
            ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
        }

        _wcAnimId = requestAnimationFrame(animate);
    }
    _wcAnimId = requestAnimationFrame(animate);
}

function renderMiniWeatherCard(hava) {
    document.getElementById('mini-weather-container').innerHTML = `
        <div class="mini-weather-card">
            <div class="mwc-title">📍 Bugünkü Hava — ${hava.sehir}</div>
            <div class="mwc-details">
                <span>🌡️ ${hava.sicaklik}°C</span>
                <span>🤒 Hiss: ${hava.hissedilen}°C</span>
                <span>💧 %${hava.nem}</span>
                <span>💨 ${hava.ruzgar} km/h</span>
            </div>
        </div>
    `;
}

function renderRecommendations(oneri, hava) {
    const recContainer = document.getElementById('recommendations-container');
    const simContainer = document.getElementById('similar-days-container');
    const infoContainer = document.getElementById('data-info-container');

    if (!oneri) {
        recContainer.innerHTML = `
            <div class="info-box">
                🧠 <strong>Henüz yeterli veri yok.</strong><br>
                Sistemin seni tanıması için "Bugün Ne Giydin?" sekmesinden en az 3 gün veri girmelisin.
                Ne kadar çok veri girersen, öneriler o kadar isabetli olur!
            </div>
        `;
        simContainer.innerHTML = '';
        infoContainer.innerHTML = '';
        return;
    }

    // Build recommendation cards
    function recCard(emoji, kategori, data, delay) {
        const altChips = (data.alternatifler || []).slice(1, 3)
            .map(a => '<span class="alt-chip">' + a.kiyafet + ' %' + a.oran + '</span>')
            .join('');

        return `
            <div class="rec-card" style="animation-delay:${delay}s">
                <div class="rc-category">${emoji} ${kategori}</div>
                <div class="rc-item">${data.tahmin}</div>
                <div class="rc-confidence">Güven: %${data.guven}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" data-width="${data.guven}"></div>
                </div>
                <div class="alt-chips">${altChips}</div>
            </div>
        `;
    }

    let html = '<h3 class="rec-section-title"><i class="fas fa-robot" style="color: var(--accent);"></i> Yapay Zeka Önerisi</h3>';
    html += '<div class="rec-grid">';
    html += recCard('👕', 'Üst Giyim', oneri.ust_giyim, 0.05);
    html += recCard('👖', 'Alt Giyim', oneri.alt_giyim, 0.1);
    html += recCard('🧥', 'Dış Giyim', oneri.dis_giyim, 0.15);
    html += '</div>';
    html += '<div class="rec-grid-2">';
    html += recCard('👟', 'Ayakkabı', oneri.ayakkabi, 0.2);
    html += recCard('🧣', 'Ekstralar', oneri.ekstra, 0.25);
    html += '</div>';

    recContainer.innerHTML = html;

    // Animate confidence bars after a short delay
    requestAnimationFrame(() => {
        setTimeout(() => {
            document.querySelectorAll('.confidence-fill').forEach(bar => {
                bar.style.width = bar.dataset.width + '%';
            });
        }, 100);
    });

    // Similar days
    if (oneri.benzer_gunler && oneri.benzer_gunler.length > 0) {
        let simHtml = '<h3 class="similar-section-title"><i class="fas fa-calendar-days" style="color: var(--accent);"></i> Bu Havaya En Benzer Geçmiş Günler</h3>';
        oneri.benzer_gunler.slice(0, 3).forEach((gun, i) => {
            simHtml += `
                <div class="similar-day" style="animation-delay:${0.05 * (i + 1)}s">
                    <span class="sd-date">📌 ${gun.tarih}</span>
                    <div class="sd-weather">
                        🌡️ ${gun.sicaklik}°C (hiss: ${gun.hissedilen}°C) &nbsp;
                        💧 %${gun.nem} &nbsp; 💨 ${gun.ruzgar} km/h
                    </div>
                    <div class="sd-clothes">
                        👕 ${gun.ust} &nbsp;|&nbsp; 👖 ${gun.alt} &nbsp;|&nbsp;
                        🧥 ${gun.dis} &nbsp;|&nbsp; 👟 ${gun.ayakkabi} &nbsp;|&nbsp;
                        🧣 ${gun.ekstra}
                        &nbsp;&nbsp; ${gun.geri_bildirim_etiket || ''}
                    </div>
                </div>
            `;
        });
        simContainer.innerHTML = simHtml;
    } else {
        simContainer.innerHTML = '';
    }

    // Data info
    infoContainer.innerHTML = `
        <div class="info-box" style="margin-top:20px">
            📈 Model şu an <strong>${oneri.toplam_veri}</strong> günlük veriyle eğitildi.
            Ne kadar çok veri girersen, öneriler o kadar kişiselleşir!
        </div>
    `;
}

function renderSidebarStats(stats) {
    const container = document.getElementById('sidebar-stats');
    if (!stats || stats.toplam === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = `
        <h3 class="section-title"><i class="fas fa-chart-bar"></i> Özet</h3>
        <div class="sidebar-stat">
            <span>Toplam Kayıt</span>
            <span class="stat-value">${stats.toplam}</span>
        </div>
        <div class="sidebar-stat">
            <span>En Sık Üst</span>
            <span class="stat-value">${stats.en_sik_ust || '-'}</span>
        </div>
        <div class="sidebar-stat">
            <span>En Sık Alt</span>
            <span class="stat-value">${stats.en_sik_alt || '-'}</span>
        </div>
        <div class="sidebar-stat">
            <span>Ort. Sıcaklık</span>
            <span class="stat-value">${stats.ort_sicaklik ?? '-'}°C</span>
        </div>
    `;
}


// ═══════════════════════════════════════════
// FORM HANDLING
// ═══════════════════════════════════════════

async function loadOptions() {
    try {
        const res = await fetch('api/secenekler');
        const opts = await res.json();

        populateSelect('select-ust', opts.ust_giyim);
        populateSelect('select-alt', opts.alt_giyim, 1);
        populateSelect('select-dis', opts.dis_giyim);
        populateSelect('select-ayakkabi', opts.ayakkabi);
        populateSelect('select-ekstra', opts.ekstra);
    } catch (err) {
        console.error('Seçenekler yüklenirken hata:', err);
    }
}

function populateSelect(id, options, defaultIndex) {
    defaultIndex = defaultIndex || 0;
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = options.map(function (opt, i) {
        return '<option value="' + opt + '"' + (i === defaultIndex ? ' selected' : '') + '>' + opt + '</option>';
    }).join('');
}

function prefillForm(oneri) {
    if (!oneri) return;

    if (oneri.ust_giyim && oneri.ust_giyim.tahmin) {
        document.getElementById('select-ust').value = oneri.ust_giyim.tahmin;
    }
    if (oneri.alt_giyim && oneri.alt_giyim.tahmin) {
        document.getElementById('select-alt').value = oneri.alt_giyim.tahmin;
    }
    if (oneri.dis_giyim && oneri.dis_giyim.tahmin) {
        document.getElementById('select-dis').value = oneri.dis_giyim.tahmin;
    }
    if (oneri.ayakkabi && oneri.ayakkabi.tahmin) {
        document.getElementById('select-ayakkabi').value = oneri.ayakkabi.tahmin;
    }
    if (oneri.ekstra && oneri.ekstra.tahmin) {
        document.getElementById('select-ekstra').value = oneri.ekstra.tahmin;
    }
}

function setupForm() {
    const form = document.getElementById('kiyafet-formu');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!currentWeather) {
            showToast('Hava durumu verisi henüz yüklenmedi.', 'error');
            return;
        }

        const btn = document.getElementById('btn-kaydet');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kaydediliyor...';

        const gbRadio = document.querySelector('input[name="geri-bildirim"]:checked');
        const geri_bildirim = gbRadio ? parseInt(gbRadio.value) : 0;

        const data = {
            tarih: currentWeather.tarih,
            sicaklik: currentWeather.sicaklik,
            hissedilen: currentWeather.hissedilen,
            nem: currentWeather.nem,
            ruzgar: currentWeather.ruzgar,
            ust: document.getElementById('select-ust').value,
            alt: document.getElementById('select-alt').value,
            dis: document.getElementById('select-dis').value,
            ayakkabi: document.getElementById('select-ayakkabi').value,
            ekstra: document.getElementById('select-ekstra').value,
            geri_bildirim: geri_bildirim,
        };

        try {
            const res = await fetch('api/kaydet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await res.json();

            if (result.basarili) {
                showToast(
                    '✅ Kaydedildi! ' + data.ust + ' + ' + data.alt + ' + ' + data.dis +
                    ' + ' + data.ayakkabi + ' — Sistem bu veriyi öğrendi 🧠',
                    'success'
                );
                createConfetti();

                // Reset form to defaults
                form.reset();
                document.querySelector('input[name="geri-bildirim"][value="0"]').checked = true;

                // Refresh stats and recommendations silently
                await loadStats();
                await refreshData(false);
            } else {
                showToast('❌ Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error');
            }
        } catch (err) {
            showToast('❌ Sunucu bağlantı hatası.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-floppy-disk"></i> Sisteme Kaydet ve Öğret';
        }
    });
}


// ═══════════════════════════════════════════
// DELETE RECORD
// ═══════════════════════════════════════════

async function deleteLastRecord() {
    if (!confirm('Son kaydı silmek istediğinize emin misiniz? Bu işlem geri alınamaz!')) return;

    try {
        const res = await fetch('api/son-kayit-sil', { method: 'DELETE' });
        const result = await res.json();

        if (result.basarili) {
            showToast('🗑️ Son kayıt silindi.', 'success');
            loadHistory();
            loadStats();
        } else {
            showToast('❌ Silinecek kayıt bulunamadı.', 'error');
        }
    } catch (err) {
        showToast('❌ Silme sırasında hata oluştu.', 'error');
    }
}


// ═══════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════

function setLoading(show) {
    document.getElementById('loading-screen').style.display = show ? 'flex' : 'none';
}

function setContent(show) {
    document.getElementById('content-wrapper').style.display = show ? 'block' : 'none';
}

function showError() {
    document.getElementById('error-screen').style.display = 'flex';
    document.getElementById('content-wrapper').style.display = 'none';
}

function hideError() {
    document.getElementById('error-screen').style.display = 'none';
}


// ═══════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════

function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toast-container');
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(function () {
        toast.classList.add('show');
    });

    setTimeout(function () {
        toast.classList.remove('show');
        setTimeout(function () { toast.remove(); }, 400);
    }, 4000);
}


// ═══════════════════════════════════════════
// CONFETTI 🎉
// ═══════════════════════════════════════════

function createConfetti() {
    var colors = ['#c084fc', '#d8b4fe', '#a855f7', '#e9d5ff', '#10b981', '#f472b6'];
    for (var i = 0; i < 60; i++) {
        var el = document.createElement('span');
        el.className = 'confetti';
        el.style.left = Math.random() * 100 + '%';
        el.style.animationDelay = Math.random() * 2 + 's';
        el.style.animationDuration = (2 + Math.random() * 2) + 's';
        el.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        el.style.width = (6 + Math.random() * 8) + 'px';
        el.style.height = (6 + Math.random() * 8) + 'px';
        el.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        document.body.appendChild(el);
        (function (element) {
            setTimeout(function () { element.remove(); }, 5000);
        })(el);
    }
}
