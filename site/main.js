// Chart name for each scroll step (12 steps, indices 0–11)
const STEP_CHARTS = [
  'chart_01_global_choropleth',   // 0  — global academic freedom map
  'chart_02b_regime_af_scatter',  // 1  — regime type vs academic freedom scatter
  'chart_02_regime_timeline',     // 2  — regime type share 1900–2025
  'chart_03_case_countries',      // 3  — all 4 countries equal
  'chart_03_case_countries',      // 4  — Russia highlighted
  'chart_03_case_countries',      // 5  — China highlighted
  'chart_03_case_countries',      // 6  — Hungary highlighted
  'chart_03_case_countries',      // 7  — US highlighted
  'chart_04_bans_choropleth',     // 8  — bans by US state
  'chart_05_bans_timeline',       // 9  — monthly ban spike
  'chart_08_doe_spending',        // 10 — quarterly DoE spending
  'chart_10_literacy',            // 11 — literacy rate
];

const STEP_SOURCES = [
  'V-Dem Institute, Academic Freedom Index (2025)',
  'V-Dem Institute, Varieties of Democracy Dataset v16 (2025)',
  'V-Dem Institute, Varieties of Democracy Dataset v16 (2025)',
  'V-Dem Institute, Academic Freedom Index (2025)',
  'V-Dem Institute, Academic Freedom Index (2025)',
  'V-Dem Institute, Academic Freedom Index (2025)',
  'V-Dem Institute, Academic Freedom Index (2025)',
  'V-Dem Institute, Academic Freedom Index (2025)',
  'PEN America, Index of School Book Bans 2021–2022',
  'PEN America, Index of School Book Bans 2021–2022',
  'USASpending.gov, Department of Education Quarterly Obligations FY2017–2026',
  'World Bank, World Development Indicators; V-Dem Institute (2025)',
];

// Country trace indices in chart_03 (order matches COUNTRY_COLORS in build_charts.py)
const TRACE = { RUSSIA: 0, CHINA: 1, HUNGARY: 2, USA: 3 };

// Highlight config per step (null = show all equally)
const STEP_HIGHLIGHT = {
  4: [TRACE.RUSSIA],
  5: [TRACE.CHINA],
  6: [TRACE.HUNGARY],
  7: [TRACE.USA],
};

const charts  = {};         // loaded figure data, keyed by chart name
let currentChart = null;    // name of the chart currently rendered

// MAP SIZING 
const MAP_LON_LAT_RATIO = 360 / 145;   // equirectangular, lat -60→85 (145°)
const GEO_DOMAIN_X      = 1.0;         // map now uses full paper width
const GEO_DOMAIN_Y      = 0.70;        // fraction of paper used by the map (y = 1.0 − 0.30)
const MAP_MARGIN_PX     = 10;          // t=5 + b=5

// Plotly preserves a map's aspect ratio, so we work backwards from the container
// width to get the exact height the choropleth will occupy, leaving no blank space.
function fitContainerToMap() {
  const w       = container.offsetWidth;
  const plotW   = (w - 20) * GEO_DOMAIN_X;          // subtract l=10 + r=10
  const mapH    = plotW / MAP_LON_LAT_RATIO;
  const plotH   = mapH  / GEO_DOMAIN_Y;
  container.style.height = Math.ceil(plotH + MAP_MARGIN_PX) + 'px';
}

function resetContainerHeight() {
  container.style.height = '';
}

//  CHART LOADING
async function loadCharts() {
  // deduplicate chart names — multiple steps can share the same chart
  const names = [...new Set(STEP_CHARTS)];
  // fetch all chart JSON files in parallel and store them by name
  await Promise.all(names.map(async name => {
    const res = await fetch(`charts/${name}.json`);
    charts[name] = await res.json();
  }));
}

// RENDER 
const container = document.getElementById('chart-container');

const BASE_LAYOUT = {
  autosize:       true,
  paper_bgcolor:  '#111111',
  plot_bgcolor:   '#0d0d0d',
  font:           { color: '#cccccc', family: "'Courier New', Consolas, monospace" },
  margin:         { t: 40, b: 50, l: 60, r: 30 },
};

const CONFIG = {
  responsive:    true,
  displaylogo:   false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
};

function renderChart(name, highlightIndices) {
  const fig = charts[name];
  if (!fig) return;

  if (name === 'chart_01_global_choropleth') {
    fitContainerToMap();
  } else {
    resetContainerHeight();
  }

  const frames = fig.frames || [];
  // merge the stored layout with shared base styles (colors, font, margins)
  const layout = { ...fig.layout, ...BASE_LAYOUT };

  let promise;
  if (frames.length > 0) {
    // animated chart: build the plot first, then attach the animation frames
    promise = Plotly.newPlot(container, fig.data, layout, CONFIG)
      .then(() => Plotly.addFrames(container, frames))
      .then(() => { currentChart = name; });
  } else if (currentChart === name) {
    // chart already showing — no re-render needed
    promise = Promise.resolve();
  } else {
    // swap to a different chart using a lightweight diff instead of full redraw
    promise = Plotly.react(container, fig.data, layout, CONFIG)
      .then(() => { currentChart = name; });
  }

  promise.then(() => {
    if (frames.length > 0) return;   // animated charts handle their own opacity
    if (!container._fullData) return;
    const n = container._fullData.length;
    if (n === 0) return;

    if (highlightIndices) {
      // dim every trace, then restore full opacity only on the highlighted ones
      const opacities = Array(n).fill(0.08);
      highlightIndices.forEach(i => { if (i < n) opacities[i] = 1; });
      Plotly.restyle(container, { opacity: opacities });
    } else {
      // no highlight — all traces at full opacity
      Plotly.restyle(container, { opacity: Array(n).fill(1) });
    }
  });
}

// SCROLLAMA 
function initScroller() {
  const scroller = scrollama();

  scroller
    // offset: 0.5 means a step triggers when it crosses the middle of the viewport
    .setup({ step: '.step', offset: 0.5 })
    .onStepEnter(({ index }) => {
      // mark the current step active (used for CSS fade-in)
      document.querySelectorAll('.step').forEach((el, i) => {
        el.classList.toggle('is-active', i === index);
      });

      const name = STEP_CHARTS[index];
      if (!name || !charts[name]) return;

      renderChart(name, STEP_HIGHLIGHT[index] ?? null);

      const sourceEl = document.getElementById('chart-source');
      if (sourceEl) sourceEl.textContent = `Source: ${STEP_SOURCES[index] ?? ''}`;
    });

  // recalculate step positions when the window is resized
  window.addEventListener('resize', scroller.resize);
}

// INIT 
loadCharts()
  .then(() => {
    renderChart(STEP_CHARTS[0], null);
    document.getElementById('chart-source').textContent = `Source: ${STEP_SOURCES[0]}`;
    initScroller();
  })
  .catch(err => {
    container.innerHTML = `<div class="chart-loading" style="color:#c0392b">
      Failed to load charts.<br>
      <span style="font-size:0.7rem;color:#666">Serve this folder with a local server:<br>
      python -m http.server 8000</span>
    </div>`;
    console.error(err);
  });
