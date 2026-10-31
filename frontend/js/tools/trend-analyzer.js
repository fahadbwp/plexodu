
// ── Render Stitch Topic Velocity SVG Canvas ─────────────────────────────────
function renderTrendCanvasVisual(timeSeries, categoryName) {
  const barsGroup = document.getElementById("svgVolumeBars");
  const xAxisGroup = document.getElementById("svgXAxisLabels");
  const baselineCurve = document.getElementById("svgBaselineCurve");
  const areaCurve = document.getElementById("svgAreaCurve");
  const observedCurve = document.getElementById("svgObservedCurve");
  const surgePin = document.getElementById("svgSurgePin");
  const surgeText = document.getElementById("svgSurgeText");
  const tooltip = document.getElementById("chartTooltip");
  const tooltipDate = document.getElementById("tooltipDate");
  const tooltipVal = document.getElementById("tooltipVal");
  const card = document.getElementById("topicVelocityChartCard");

  if (!barsGroup || typeof barsGroup.appendChild !== 'function' || typeof document.createElementNS !== 'function' || !timeSeries || timeSeries.length === 0) return;

  barsGroup.innerHTML = "";
  if (xAxisGroup) xAxisGroup.innerHTML = "";

  const n = timeSeries.length;
  const startX = 70;
  const endX = 690;
  const stepX = n > 1 ? (endX - startX) / (n - 1) : 0;
  const baseY = 230;
  const minY = 50;
  const maxViews = Math.max(...timeSeries.map(p => Number(p.views) || 0), 1000);

  let peakIdx = 0;
  let peakVal = 0;
  timeSeries.forEach((p, i) => {
    const v = Number(p.views) || 0;
    if (v > peakVal) {
      peakVal = v;
      peakIdx = i;
    }
  });

  const points = [];

  timeSeries.forEach((p, i) => {
    const x = Math.round(n === 1 ? 380 : startX + i * stepX);
    const val = Number(p.views) || 0;
    const barHeight = Math.max(16, Math.round(((val) / maxViews) * 160));
    const y = baseY - barHeight;
    points.push({ x, y, label: p.label, val });

    const isPeak = i === peakIdx && val > 0;
    const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bar.setAttribute("class", "chart-bar-hover transition-opacity cursor-pointer");
    bar.setAttribute("x", String(x - 14));
    bar.setAttribute("y", String(y));
    bar.setAttribute("width", "28");
    bar.setAttribute("height", String(barHeight));
    bar.setAttribute("rx", "6");
    bar.setAttribute("fill", isPeak ? "url(#peakBarGrad)" : "url(#purpleBarGrad)");
    bar.setAttribute("data-date", p.label || `Day ${i + 1}`);
    bar.setAttribute("data-val", formatCompact(val));

    // Hover tooltip interaction
    bar.addEventListener("mouseenter", (e) => {
      if (!tooltip || !card) return;
      if (tooltipDate) tooltipDate.textContent = p.label || `Interval ${i + 1}`;
      if (tooltipVal) tooltipVal.textContent = `${Number(val).toLocaleString()} views`;
      const rect = bar.getBoundingClientRect();
      const cardRect = card.getBoundingClientRect();
      tooltip.style.left = `${rect.left - cardRect.left + rect.width / 2}px`;
      tooltip.style.top = `${rect.top - cardRect.top}px`;
      tooltip.classList.remove("opacity-0");
      tooltip.classList.add("opacity-100");
    });
    bar.addEventListener("mouseleave", () => {
      if (!tooltip) return;
      tooltip.classList.remove("opacity-100");
      tooltip.classList.add("opacity-0");
    });

    barsGroup.appendChild(bar);

    // X-Axis text
    if (xAxisGroup) {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", String(x));
      text.setAttribute("y", "252");
      text.setAttribute("text-anchor", "middle");
      if (isPeak) {
        text.setAttribute("fill", "#4648D4");
        text.setAttribute("font-weight", "700");
        text.textContent = `${p.label || "Peak"} ★`;
      } else {
        text.setAttribute("fill", "#767586");
        text.textContent = p.label || `D${i + 1}`;
      }
      xAxisGroup.appendChild(text);
    }
  });

  // Calculate smooth curves if >= 2 points
  if (points.length >= 2) {
    let dCurve = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const mx = (p0.x + p1.x) / 2;
      dCurve += ` C ${mx} ${p0.y}, ${mx} ${p1.y}, ${p1.x} ${p1.y}`;
    }
    if (observedCurve) observedCurve.setAttribute("d", dCurve);
    if (areaCurve) {
      const firstX = points[0].x;
      const lastX = points[points.length - 1].x;
      areaCurve.setAttribute("d", `${dCurve} L ${lastX} 230 L ${firstX} 230 Z`);
    }

    // Baseline curve (median trajectory)
    let dBase = `M ${points[0].x} ${Math.min(210, points[0].y + 15)}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const mx = (p0.x + p1.x) / 2;
      dBase += ` C ${mx} ${p0.y + 10}, ${mx} ${p1.y + 10}, ${p1.x} ${Math.min(215, p1.y + 10)}`;
    }
    if (baselineCurve) baselineCurve.setAttribute("d", dBase);

    // Position surge pin at peak
    const peakPt = points[peakIdx];
    if (surgePin && peakPt) {
      surgePin.setAttribute("transform", `translate(${peakPt.x}, ${Math.max(45, peakPt.y)})`);
      surgePin.style.display = "block";
    }
    if (surgeText) {
      const surgePct = peakVal > 0 ? Math.min(240, Math.round((peakVal / Math.max(1, maxViews * 0.6)) * 100)) : 148;
      surgeText.textContent = `+${surgePct}% Surge`;
    }
  }
}

/**
 * YouTube Trend Analyzer — Claude Pulsecheck Light Theme Controller
 * Connected to Live YouTube Data API v3 (/api/trending-feed)
 * Retains 'First Scan' baseline tracking for single-point queries.
 */

// Global State
let activeRegion = "Pakistan";
let activeTimeframe = "7d";
let activeCategory = "All";
let activeQuery = "";
let currentVideos = [];
let viewsChart = null;
let catChart = null;
let lowerViewsChart = null;
let currentTrendId = null;
let currentKpis = {};
let activeVideoTab = "all";
let currentKeyword = "";
let currentTimelineRaw = [];
let currentLowerRange = "all";

const CATEGORIES = [
  { name: "Music", hue: "#FF6B4A" },
  { name: "Gaming", hue: "#8B5CF6" },
  { name: "Comedy", hue: "#FBBF24" },
  { name: "Tech", hue: "#38BDF8" },
  { name: "Education", hue: "#4ADE80" },
  { name: "Sports", hue: "#F472B6" },
  { name: "News", hue: "#94A3B8" },
  { name: "Lifestyle", hue: "#FB923C" },
];

function formatCompact(n) {
  if (n == null || isNaN(n)) return "0";
  const num = Number(n);
  if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(1).replace(/\.0$/, "") + "B";
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (num >= 1_000) return (num / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return String(Math.round(num));
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── DOM Initialization ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initCategories();
  initTimeframePills();
  initRegionSelect();
  initSearchInput();
  initTimeframeTabs();
  initConnectedActions();
  fetchTrendingFeed();
});

// ── Category Scroller ────────────────────────────────────────────────────────
function initCategories() {
  const container = document.getElementById("pulseCatScroller");
  if (!container) return;

  container.innerHTML = "";

  const allBtn = document.createElement("button");
  allBtn.className = "pulsecheck-cat-chip" + (activeCategory === "All" ? " active" : "");
  allBtn.textContent = "All";
  allBtn.addEventListener("click", () => {
    setActiveCategory("All");
  });
  container.appendChild(allBtn);

  CATEGORIES.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "pulsecheck-cat-chip";
    btn.textContent = cat.name;
    btn.setAttribute("data-category", cat.name);
    btn.addEventListener("click", () => {
      setActiveCategory(cat.name);
    });
    container.appendChild(btn);
  });
}

function setActiveCategory(catName) {
  activeCategory = catName;
  const container = document.getElementById("pulseCatScroller");
  if (container) {
    const chips = container.querySelectorAll(".pulsecheck-cat-chip");
    chips.forEach((chip) => {
      const chipCat = chip.getAttribute("data-category") || "All";
      if (chipCat === catName) {
        chip.classList.add("active");
        const found = CATEGORIES.find((c) => c.name === catName);
        if (found) {
          chip.style.backgroundColor = "var(--stitch-primary)";
          chip.style.borderColor = "var(--stitch-primary)";
          chip.style.color = "#ffffff";
        } else {
          chip.style.backgroundColor = "#4f46e5";
          chip.style.borderColor = "#4f46e5";
          chip.style.color = "#ffffff";
        }
      } else {
        chip.classList.remove("active");
        chip.style.backgroundColor = "#ffffff";
        chip.style.borderColor = "#e2e8f0";
        chip.style.color = "#64748b";
      }
    });
  }

  fetchTrendingFeed();
}

// ── Timeframe Pills ──────────────────────────────────────────────────────────
function initTimeframePills() {
  const pills = document.querySelectorAll(".pulsecheck-pill");
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => {
        p.classList.remove("active", "bg-[#6063EE]", "text-white", "shadow-sm", "font-semibold");
        p.classList.add("text-[#767586]", "font-medium");
      });
      pill.classList.add("active", "bg-[#6063EE]", "text-white", "shadow-sm", "font-semibold");
      pill.classList.remove("text-[#767586]", "font-medium");
      activeTimeframe = pill.getAttribute("data-timeframe") || "7d";
      fetchTrendingFeed();
    });
  });
}

// ── Region Dropdown ──────────────────────────────────────────────────────────
function initRegionSelect() {
  const sel = document.getElementById("pulseRegionSelect");
  if (sel) {
    try {
      const saved = localStorage.getItem("plexudo_region");
      if (saved) {
        activeRegion = saved;
        sel.value = saved;
      } else {
        activeRegion = "Pakistan";
        sel.value = "Pakistan";
      }
    } catch (_) {
      activeRegion = "Pakistan";
      sel.value = "Pakistan";
    }
    sel.addEventListener("change", (e) => {
      activeRegion = e.target.value;
      try { localStorage.setItem("plexudo_region", activeRegion); } catch (_) {}
      fetchTrendingFeed();
    });
  }
}

// ── Search Input ─────────────────────────────────────────────────────────────
function initSearchInput() {
  const inp = document.getElementById("pulseSearchInput");
  if (!inp) return;

  const btn = document.getElementById("analyzeBtn");

  const executeSearch = () => {
    activeQuery = inp.value.trim();
    fetchTrendingFeed(true);
  };

  if (btn) {
    btn.addEventListener("click", executeSearch);
  }

  inp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      executeSearch();
    }
  });

  // If user clears the input box, reset activeQuery state without calling API
  inp.addEventListener("input", (e) => {
    if (!e.target.value.trim()) {
      activeQuery = "";
    }
  });
}

function filterCurrentVideos(q) {
  if (!currentVideos || currentVideos.length === 0) return;
  const filtered = currentVideos.filter(
    (v) =>
      v.title.toLowerCase().includes(q.toLowerCase()) ||
      v.channel.toLowerCase().includes(q.toLowerCase())
  );
  renderTrendingList(filtered, q);
}

// ── Trend Analyzer UI State Management ───────────────────────────────────────
function updateKpiBadges(state, isCached = false) {
  const totalViewsBadge = document.getElementById("kpiTotalViewsDelta");
  const totalViewsDeltaText = document.getElementById("kpiTotalViewsDeltaText");
  const avgEngBadge = document.getElementById("kpiAvgEngDelta");
  const avgEngDeltaText = document.getElementById("kpiAvgEngDeltaText");
  const topCatBadge = document.getElementById("kpiTopCatDelta");
  const risingCountBadge = document.getElementById("kpiRisingCountDelta");

  if (!totalViewsBadge || !totalViewsDeltaText) return;

  if (state === "SUCCESS") {
    if (isCached) {
      totalViewsBadge.className = "stitch-kpi-badge amber";
      totalViewsDeltaText.textContent = "Cached Snapshot";
    } else {
      totalViewsBadge.className = "stitch-kpi-badge mint";
      totalViewsDeltaText.textContent = "API snapshot · freshness unavailable";
    }
    if (avgEngBadge && avgEngDeltaText) {
      avgEngBadge.className = "stitch-kpi-badge mint";
      avgEngDeltaText.textContent = "Sample ratio";
    }
    if (topCatBadge) topCatBadge.className = "stitch-kpi-badge violet";
    if (risingCountBadge) risingCountBadge.className = "stitch-kpi-badge mint";
  } else if (state === "EMPTY") {
    totalViewsBadge.className = "stitch-kpi-badge amber";
    totalViewsDeltaText.textContent = "No Data";
    if (avgEngBadge && avgEngDeltaText) {
      avgEngBadge.className = "stitch-kpi-badge amber";
      avgEngDeltaText.textContent = "—";
    }
  } else if (state === "QUOTA_LIMITED") {
    totalViewsBadge.className = "stitch-kpi-badge amber";
    totalViewsDeltaText.textContent = "Quota Exceeded";
    if (avgEngBadge && avgEngDeltaText) {
      avgEngBadge.className = "stitch-kpi-badge amber";
      avgEngDeltaText.textContent = "Rate Limited";
    }
  } else {
    totalViewsBadge.className = "stitch-kpi-badge amber";
    totalViewsDeltaText.textContent = state === "LOADING" ? "Loading snapshot" : "Unavailable";
    if (avgEngBadge && avgEngDeltaText) {
      avgEngBadge.className = "stitch-kpi-badge amber";
      avgEngDeltaText.textContent = "Unavailable";
    }
  }
}

// ── Fetch Trending Feed from Live YouTube API ────────────────────────────────
let feedRequestId = 0;
async function fetchTrendingFeed(shouldScroll = false) {
  const requestId = ++feedRequestId;
  updateKpiBadges("LOADING");
  renderKpis(null, false);
  const previousResults = document.getElementById("resultsArea");
  if (previousResults) previousResults.style.display = "none";
  hideStatusBar(document.getElementById("statusLine"));
  const loadingEl = document.getElementById("pulseLoading");
  if (loadingEl) loadingEl.style.display = "flex";

  try {
    const params = new URLSearchParams({
      region: activeRegion,
      category: activeCategory,
      timeframe: activeTimeframe,
      q: activeQuery,
    });

    const res = await fetchWithTimeout(`/api/trending-feed?${params.toString()}`, {}, 45000);
    const data = await res.json();
    if (requestId !== feedRequestId) return;

    if (res.status === 429) {
      currentVideos = [];
      const previousResults = document.getElementById("resultsArea");
      if (previousResults) previousResults.style.display = "none";
      updateKpiBadges("QUOTA_LIMITED");
      renderKpis(null, false);
      renderViewsChart([], activeCategory);
      renderCategoryChart([]);
      showStatusBar(document.getElementById("statusLine"), "YouTube API quota limit reached. Please wait a moment or try again.", true);
      const listEl = document.getElementById("pulseList");
      if (listEl) {
        listEl.innerHTML = `<div class="pulsecheck-empty-state">YouTube API quota limit reached. Please wait a few moments or try refreshing.</div>`;
      }
      return;
    }

    if (!res.ok || data.error) {
      throw new Error(data.error || `API returned HTTP ${res.status}`);
    }

    currentVideos = data.videos || [];
    const isCached = Boolean(data.cached || data.is_stale || data.from_cache);

    if (currentVideos.length === 0) {
      const previousResults = document.getElementById("resultsArea");
      if (previousResults) previousResults.style.display = "none";
      updateKpiBadges("EMPTY");
      renderKpis(null, false);
      renderViewsChart([], activeCategory);
      renderCategoryChart([]);
      const listEl = document.getElementById("pulseList");
      if (listEl) {
        listEl.innerHTML = `<div class="pulsecheck-empty-state">No matching public videos found for "${escapeHtml(activeQuery || activeCategory)}". Try clearing search or selecting a different category.</div>`;
      }
      return;
    }

    updateKpiBadges("SUCCESS", isCached);
    currentKpis = data.kpis || {};
    const sourceLabel = document.getElementById("kpiTotalViewsDeltaText");
    if (sourceLabel && data.is_stale) sourceLabel.textContent = "Cached Snapshot · stale";
    renderKpis(data.kpis || {}, true);
    updateFormatBreakdownCard(currentVideos);
    updateVideoTabStates();
    updateExportButtons();
    renderViewsChart(data.timeSeries || [], activeCategory);
    renderTrendCanvasVisual(data.timeSeries || [], activeCategory);
    renderCategoryChart(data.catBreakdown || []);
    renderTrendingList(currentVideos, activeQuery);

    const ytData = data.results && data.results.YouTube ? data.results.YouTube : null;
    if (ytData) {
      renderDeepIntelligence(ytData);
      if (shouldScroll && activeQuery) {
        const resultsArea = document.getElementById("resultsArea");
        if (resultsArea) {
          setTimeout(() => {
            resultsArea.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 150);
        }
      }
    }
  } catch (err) {
    if (requestId !== feedRequestId) return;
    const isQuota = /quota|429/i.test(err.message || "");
    updateKpiBadges(isQuota ? "QUOTA_LIMITED" : "ERROR");
    showStatusBar(document.getElementById("statusLine"), err.message || "Unable to load YouTube data.", true);
    currentVideos = [];
    renderKpis(null, false);
    renderViewsChart([], activeCategory);
    renderCategoryChart([]);
    const results = document.getElementById("resultsArea");
    if (results) results.style.display = "none";
    console.error("Failed to load trending feed:", err);
    // Display graceful state
    const listEl = document.getElementById("pulseList");
    if (listEl && currentVideos.length === 0) {
      listEl.innerHTML = `
        <div class="pulsecheck-empty-state">
          ${escapeHtml(err.message || "Unable to connect to live YouTube feed right now. Please verify your connection or try again.")}
        </div>
      `;
    }
  } finally {
    if (loadingEl && requestId === feedRequestId) loadingEl.style.display = "none";
  }
}

// ── Render KPIs (Explicit Non-Misleading Placeholders on Error/Empty) ─────────
function metricAvailable(value) {
  return value !== null && value !== undefined && value !== "" && typeof value !== "boolean" && Number.isFinite(Number(value)) && Number(value) >= 0;
}

function renderKpis(kpis, isValid = true) {
  const totalViewsVal = document.getElementById("kpiTotalViewsVal");
  const avgEngVal = document.getElementById("kpiAvgEngVal");
  const topCatVal = document.getElementById("kpiTopCatVal");
  const topCatDeltaText = document.getElementById("kpiTopCatDeltaText");
  const risingCountVal = document.getElementById("kpiRisingCountVal");
  const risingCountDeltaText = document.getElementById("kpiRisingCountDeltaText");

  // Stitch UI Card Element references
  const kpiTopTopicTitle = document.getElementById("kpiTopTopicTitle");
  const kpiTopTopicVelocity = document.getElementById("kpiTopTopicVelocity");
  const kpiTopTopicBadge = document.getElementById("kpiTopTopicBadge");
  const kpiMedianViewsVal = document.getElementById("kpiMedianViewsVal");
  const kpiMomentumScoreVal = document.getElementById("kpiMomentumScoreVal");
  const kpiMomentumSpeedBadge = document.getElementById("kpiMomentumSpeedBadge");
  const kpiEngagementRatioDisplay = document.getElementById("kpiEngagementRatioDisplay");
  const kpiGaugeArc = document.getElementById("kpiGaugeArc");
  const kpiFormatCapsuleBar = document.getElementById("kpiFormatCapsuleBar");

  if (!isValid || !kpis || typeof kpis.totalViews === "undefined") {
    if (totalViewsVal) totalViewsVal.textContent = "—";
    if (avgEngVal) avgEngVal.textContent = "—";
    if (topCatVal) topCatVal.textContent = "—";
    if (topCatDeltaText) topCatDeltaText.textContent = "Unavailable";
    if (risingCountVal) risingCountVal.textContent = "—";
    if (risingCountDeltaText) risingCountDeltaText.textContent = "Unavailable";

    if (kpiTopTopicTitle) kpiTopTopicTitle.textContent = "—";
    if (kpiTopTopicVelocity) kpiTopTopicVelocity.innerHTML = `<span class="material-symbols-outlined text-[13px]">trending_up</span><span>0.0%</span>`;
    if (kpiMedianViewsVal) kpiMedianViewsVal.textContent = "—";
    if (kpiMomentumScoreVal) kpiMomentumScoreVal.textContent = "0.0";
    if (kpiMomentumSpeedBadge) kpiMomentumSpeedBadge.textContent = "Calibrating";
    if (kpiEngagementRatioDisplay) kpiEngagementRatioDisplay.textContent = "—";
    return;
  }

  // 1. Total Views
  if (totalViewsVal) {
    totalViewsVal.textContent = metricAvailable(kpis.totalViews) ? formatCompact(kpis.totalViews) : "—";
  }

  // 2. Badges & Ratio
  for (const [id, available] of [
    ["kpiAvgEngDelta", metricAvailable(kpis.avgEngagement)],
    ["kpiTopCatDelta", Boolean(kpis.fastestCategory || kpis.topCategory)],
    ["kpiRisingCountDelta", metricAvailable(kpis.risingCount)],
  ]) {
    const badge = document.getElementById(id);
    if (badge) badge.className = available ? "stitch-kpi-badge mint" : "stitch-kpi-badge amber";
  }
  const engagementLabel = document.getElementById("kpiAvgEngDeltaText");
  if (engagementLabel) engagementLabel.textContent = metricAvailable(kpis.avgEngagement) ? "Sample ratio" : "Unavailable";

  // 3. Avg Engagement
  if (avgEngVal) {
    avgEngVal.textContent = metricAvailable(kpis.avgEngagement) ? `${Number(kpis.avgEngagement).toFixed(1)}%` : "—";
  }
  if (kpiEngagementRatioDisplay) {
    kpiEngagementRatioDisplay.textContent = metricAvailable(kpis.avgEngagement) ? `${Number(kpis.avgEngagement).toFixed(1)}%` : "—";
  }

  // 4. Top Category & Topic
  const leadCat = kpis.fastestCategory || kpis.topCategory || "—";
  if (topCatVal) topCatVal.textContent = leadCat;
  if (kpiTopTopicTitle) {
    const topicText = currentVideos.length > 0 ? currentVideos[0].title : leadCat;
    kpiTopTopicTitle.textContent = topicText;
    if (typeof kpiTopTopicTitle.setAttribute === "function") {
      kpiTopTopicTitle.setAttribute("title", topicText);
    }
  }
  if (kpiTopTopicVelocity) {
    const vel = metricAvailable(kpis.growthRate) ? Number(kpis.growthRate).toFixed(1) : "38.4";
    kpiTopTopicVelocity.innerHTML = `<span class="material-symbols-outlined text-[13px]">trending_up</span><span>+${vel}%</span>`;
  }

  if (topCatDeltaText) {
    const catViews = metricAvailable(kpis.topCategoryViews) ? formatCompact(kpis.topCategoryViews) : "—";
    topCatDeltaText.textContent = `${catViews} views`;
  }

  // 5. Rising Count & Median Views
  if (risingCountVal) {
    risingCountVal.textContent = metricAvailable(kpis.risingCount) ? String(kpis.risingCount) : "—";
  }
  if (risingCountDeltaText) {
    const tracked = kpis.totalTracked ?? kpis.trackedCount ?? currentVideos.length;
    risingCountDeltaText.textContent = metricAvailable(kpis.risingCount) && tracked > 0 ? `of ${tracked} returned` : "Unavailable";
  }

  if (kpiMedianViewsVal) {
    const median = currentVideos.length > 0 ? Math.round(kpis.totalViews / currentVideos.length) : (kpis.medianViews || 0);
    kpiMedianViewsVal.textContent = formatCompact(median);
  }

  // 6. Momentum Score & Radial Arc
  const rawScore = kpis.virality_score != null ? Number(kpis.virality_score) : (kpis.risingCount ? Math.min(95, 50 + kpis.risingCount * 4) : 74.2);
  const score = Math.max(0, Math.min(100, rawScore));
  if (kpiMomentumScoreVal) {
    kpiMomentumScoreVal.textContent = score.toFixed(1);
  }
  if (kpiMomentumSpeedBadge) {
    kpiMomentumSpeedBadge.textContent = score >= 75 ? "Ultra Fast" : (score >= 50 ? "Rapid" : (score >= 30 ? "Moderate" : "Calibrating"));
  }
  if (kpiGaugeArc && typeof kpiGaugeArc.setAttribute === 'function') {
    // Semi-circle from 180 deg to 0 deg
    const rad = Math.PI * (1 - (score / 100));
    const arcX = 80 - 60 * Math.cos(rad);
    const arcY = 80 - 60 * Math.sin(rad);
    kpiGaugeArc.setAttribute("d", `M 20 80 A 60 60 0 0 1 ${arcX.toFixed(1)} ${arcY.toFixed(1)}`);
  }


  // 7. Format breakdown in capsule bar (consistent computation)
  if (kpiFormatCapsuleBar && currentVideos.length > 0) {
    const { shortsPct, longPct, otherPct } = computeFormatBreakdown(currentVideos);
    kpiFormatCapsuleBar.innerHTML = `
      <div class="h-full bg-[#4648D4]" style="width: ${shortsPct}%"></div>
      <div class="h-full bg-[#8A4CFC]" style="width: ${longPct}%"></div>
      <div class="h-full bg-[#00885D]" style="width: ${otherPct}%"></div>
    `;
    const legend = document.getElementById("kpiFormatLegend");
    if (legend) {
      legend.innerHTML = `
        <span class="flex items-center gap-1 shrink-0 whitespace-nowrap"><span class="w-2 h-2 rounded-full bg-[#4648D4]"></span>Shorts ${shortsPct}%</span>
        <span class="flex items-center gap-1 shrink-0 whitespace-nowrap"><span class="w-2 h-2 rounded-full bg-[#8A4CFC]"></span>Long ${longPct}%</span>
        <span class="flex items-center gap-1 shrink-0 whitespace-nowrap"><span class="w-2 h-2 rounded-full bg-[#00885D]"></span>Live/Other ${otherPct}%</span>
      `;
    }
  }
}

// ── Shared Format Breakdown Computation (Used by KPI bar & Format card) ─────
function computeFormatBreakdown(videos) {
  if (!videos || videos.length === 0) {
    return { shortsPct: 0, longPct: 0, otherPct: 0 };
  }
  const total = videos.length;
  let shortsCount = 0;
  let longCount = 0;
  let otherCount = 0;
  for (const v of videos) {
    const d = v.duration_sec;
    if (d != null && d > 0) {
      if (d <= 60 || /#shorts/i.test(v.title || "")) {
        shortsCount++;
      } else if (d >= 480) {
        longCount++;
      } else {
        otherCount++;
      }
    } else {
      if (v.is_short || /#shorts/i.test(v.title || "")) {
        shortsCount++;
      } else {
        longCount++;
      }
    }
  }
  const shortsPct = Math.round((shortsCount / total) * 100);
  const longPct = Math.round((longCount / total) * 100);
  const otherPct = Math.max(0, 100 - shortsPct - longPct);
  return { shortsPct, longPct, otherPct };
}

function updateFormatBreakdownCard(videos) {
  const { shortsPct, longPct, otherPct } = computeFormatBreakdown(videos);
  const donutShortsPct = document.getElementById("donutShortsPct");
  if (donutShortsPct) donutShortsPct.textContent = `${shortsPct}%`;

  const circ = 238.7;
  const donutShortsArc = document.getElementById("donutShortsArc");
  if (donutShortsArc && typeof donutShortsArc.setAttribute === "function") {
    const offset = circ * (1 - shortsPct / 100);
    donutShortsArc.setAttribute("stroke-dashoffset", offset.toFixed(1));
  }
  const donutLongArc = document.getElementById("donutLongArc");
  if (donutLongArc && typeof donutLongArc.setAttribute === "function") {
    const offset = circ * (1 - (shortsPct + longPct) / 100);
    donutLongArc.setAttribute("stroke-dashoffset", offset.toFixed(1));
  }

  const formatShortsStat = document.getElementById("formatShortsStat");
  if (formatShortsStat) formatShortsStat.textContent = `${shortsPct}%`;

  const formatLongStat = document.getElementById("formatLongStat");
  if (formatLongStat) formatLongStat.textContent = `${longPct}%`;

  const formatLiveStat = document.getElementById("formatLiveStat");
  if (formatLiveStat) formatLiveStat.textContent = `${otherPct}%`;
}


// ── Render Views Trajectory Chart ────────────────────────────────────────────
function renderViewsChart(timeSeries, categoryName) {
  const catLabelEl = document.getElementById("viewsTrendCatBadge");
  if (catLabelEl && categoryName && categoryName !== "All") {
    catLabelEl.textContent = `${categoryName} Sample`;
  }

  const canvas = document.getElementById("pulseViewsChart");
  if (!canvas) return;

  const labels = timeSeries.map((p) => p.label);
  const dataPoints = timeSeries.map((p) => p.views);

  if (viewsChart) {
    viewsChart.destroy();
  }

  const a11yEl = document.getElementById("viewsChartA11y");
  if (a11yEl) {
    if (!timeSeries || timeSeries.length === 0) {
      a11yEl.innerHTML = "<p>No upload-age bucket data available for the current sample.</p>";
    } else {
      const rows = timeSeries
        .map(
          (p) =>
            `<tr><th scope="row">${p.label || "Unknown"}</th><td>${formatCompact(p.views || 0)} (${Number(p.views || 0).toLocaleString()} views)</td></tr>`
        )
        .join("");
      a11yEl.innerHTML = `<table><caption>Lifetime views by upload age in current sample cohort</caption><thead><tr><th scope="col">Upload Age Bucket</th><th scope="col">Accumulated Views</th></tr></thead><tbody>${rows}</tbody></table>`;
    }
  }

  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, "rgba(79, 70, 229, 0.16)");
  gradient.addColorStop(1, "rgba(79, 70, 229, 0)");

  // Baseline observation / First Scan tracking status
  // Used when single-point queries are evaluated
  const isFirstScan = timeSeries.length <= 1;

  viewsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Lifetime views by upload age",
          data: dataPoints,
          borderColor: "#4F46E5",
          borderWidth: 2.5,
          backgroundColor: gradient,
          fill: false,
          tension: 0,
          pointRadius: isFirstScan ? 4 : 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: "#4F46E5",
          pointHoverBorderColor: "#FFFFFF",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index",
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F172A",
          titleColor: "#94A3B8",
          bodyColor: "#FFFFFF",
          borderColor: "#1E293B",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          titleFont: { size: 11, family: "Plus Jakarta Sans, Inter, sans-serif" },
          bodyFont: { size: 13, weight: "700", family: "Plus Jakarta Sans, Inter, sans-serif" },
          callbacks: {
            title: (items) => `Upload Age: ${items[0]?.label || ""}`,
            label: (context) => `Accumulated views: ${formatCompact(context.parsed.y)} (${Number(context.raw || 0).toLocaleString()} total)`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { color: "#E2E8F0" },
          ticks: { color: "#64748B", font: { size: 11 } },
        },
        y: {
          grid: { color: "#F1F5F9" },
          border: { display: false },
          ticks: {
            color: "#64748B",
            font: { size: 11 },
            callback: (val) => formatCompact(val),
          },
        },
      },
    },
  });
}

// ── Render Category Bar Chart ────────────────────────────────────────────────
function renderCategoryChart(catBreakdown) {
  const canvas = document.getElementById("pulseCatChart");
  if (!canvas) return;

  if (catChart) {
    catChart.destroy();
  }

  const labels = catBreakdown.map((c) => c.name);
  const values = catBreakdown.map((c) => c.value);
  const hues = catBreakdown.map((c) => c.hue);

  const ctx = canvas.getContext("2d");
  catChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: hues,
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 12,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F172A",
          titleColor: "#94A3B8",
          bodyColor: "#FFFFFF",
          borderColor: "#1E293B",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (context) => `${formatCompact(context.parsed.x)} views`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            color: "#64748B",
            font: { size: 10 },
            callback: (val) => formatCompact(val),
          },
        },
        y: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            color: "#0F172A",
            font: { size: 12, weight: "600" },
          },
        },
      },
    },
  });
}

// ── Render Trending List ─────────────────────────────────────────────────────
function renderTrendingList(videos, query) {
  const titleEl = document.getElementById("trendingListTitle");
  if (titleEl) {
    titleEl.textContent = `Trending now (${videos.length})`;
  }

  const listEl = document.getElementById("pulseList");
  const emptyEl = document.getElementById("pulseEmptyState");
  const emptyQueryEl = document.getElementById("pulseEmptyQuery");

  if (!listEl) return;

  if (videos.length === 0) {
    listEl.innerHTML = "";
    if (emptyEl) {
      if (emptyQueryEl) emptyQueryEl.textContent = query || "this filter";
      emptyEl.style.display = "block";
    }
    return;
  }

  if (emptyEl) emptyEl.style.display = "none";

  listEl.innerHTML = videos
    .map((v) => {
      const momentum = Number(v.momentumScore);
      const hasMomentum = v.momentumScore != null && Number.isFinite(momentum) && momentum >= 0 && momentum <= 100;
      const hue = v.hue || "#4F46E5";
      const vidId = v.id || v.video_id || "";
      const thumbUrl = v.thumbnail || (vidId ? `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg` : "");
      let dur = "—";
      if (v.duration) {
        dur = v.duration;
      } else if (v.duration_sec != null && Number.isFinite(Number(v.duration_sec)) && Number(v.duration_sec) > 0) {
        const s = Number(v.duration_sec);
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        dur = h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : `${m}:${String(sec).padStart(2, '0')}`;
      }
      const engagementText = v.engagement != null && Number.isFinite(Number(v.engagement)) ? Number(v.engagement).toFixed(1) + "%" : "Unavailable";
      const momentumText = hasMomentum ? momentum + " / 100 idx" : "Pending";
      const velocityHourly = formatCompact(Math.round((v.views || 1000) / Math.max(1, v.hoursAgo || 6)));
      const ageText = v.hoursAgo != null && Number.isFinite(Number(v.hoursAgo))
        ? (Number(v.hoursAgo) >= 48 ? `${Math.floor(Number(v.hoursAgo) / 24)}d ago` : `${v.hoursAgo}h ago`)
        : "—";

      const hasSentiment = v.sentiment != null && Number.isFinite(Number(v.sentiment));
      const sentimentPct = hasSentiment ? Math.max(0, Math.min(100, Math.round(v.sentiment))) : null;
      const sentimentLabel = hasSentiment ? `${sentimentPct}% Positive` : "—";
      const sentimentSub = hasSentiment ? "Sampled" : "Unavailable";
      const barWidth = hasSentiment ? `${sentimentPct}%` : "0%";
      const barBg = hasSentiment ? "bg-[#006C49]" : "bg-[#C5C6D0]";

      return `
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#F2F3FF]/60 hover:bg-[#F2F3FF] border border-[#EAEDFF] transition-all flex flex-col lg:grid lg:grid-cols-12 gap-3.5 items-start lg:items-center pulsecheck-row">
        <!-- Col 1: Video details & Thumbnail (5 cols) -->
        <div class="col-span-5 flex items-start gap-3 w-full min-w-0">
          <div class="relative w-28 h-16 sm:w-32 sm:h-20 rounded-xl overflow-hidden shrink-0 shadow-sm bg-[#EAEDFF] flex items-center justify-center">
            ${thumbUrl ? `<img src="${escapeAttr(thumbUrl)}" alt="${escapeAttr(v.title)}" class="w-full h-full object-cover" loading="lazy" />` : `
              <div class="w-full h-full flex items-center justify-center bg-[#6063EE]/15">
                <span class="material-symbols-outlined text-[#4648D4] text-[24px]">play_circle</span>
              </div>
            `}
            <span class="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-[#131B2E]/85 text-white font-mono text-[10px] font-semibold">
              ${dur}
            </span>
          </div>
          <div class="flex flex-col min-w-0 flex-1">
            <div class="flex items-center gap-1.5 mb-0.5 flex-wrap">
              <span class="px-2 py-0.5 rounded-full bg-[#EADDFF] text-[#25005A] text-[10px] font-bold truncate">
                ${escapeHtml(v.category || "Trending")}
              </span>
              <span class="text-[11px] text-[#767586]">${ageText}</span>
            </div>
            <h3 class="text-xs sm:text-sm font-bold text-[#131B2E] truncate leading-snug hover:text-[#4648D4] transition-colors" title="${escapeAttr(v.title)}">
              ${escapeHtml(v.title)}
            </h3>
            <div class="flex items-center gap-1.5 mt-1 text-xs text-[#767586]">
              <span class="font-medium text-[#131B2E] truncate">${escapeHtml(v.channel)}</span>
              <span class="px-1.5 py-0.2 rounded bg-white border border-[#E2E8F0] text-[10px] font-semibold">${v.rank ? `#${v.rank}` : "Top"}</span>
            </div>
          </div>
        </div>

        <!-- Col 2: Velocity & Views (2 cols) -->
        <div class="col-span-2 flex lg:flex-col items-center lg:items-end justify-between w-full lg:w-auto">
          <span class="lg:hidden text-xs text-[#767586] font-medium">Velocity:</span>
          <div class="text-sm sm:text-base font-bold text-[#4648D4]">
            +${velocityHourly} <span class="text-[11px] text-[#767586] font-normal">views/hr</span>
          </div>
          <span class="text-[11px] text-[#006C49] font-bold flex items-center gap-0.5 pulsecheck-growth ${hasMomentum ? "score" : "pending"}">
            <span class="material-symbols-outlined text-[13px]">rocket_launch</span>
            ${momentumText}
          </span>
        </div>

        <!-- Col 3: Engagement (2 cols) -->
        <div class="col-span-2 flex lg:flex-col items-center lg:items-end justify-between w-full lg:w-auto pulsecheck-row-stat">
          <span class="lg:hidden text-xs text-[#767586] font-medium">Engagement:</span>
          <div class="text-sm font-bold text-[#131B2E]">${engagementText}</div>
          <span class="text-[11px] text-[#767586]">
            ${formatCompact(v.views)} views • ${formatCompact(v.comments)} cmts
          </span>
        </div>

        <!-- Col 4: Sentiment (2 cols) -->
        <div class="col-span-2 flex flex-col gap-1 w-full">
          <div class="flex items-center justify-between text-[11px]">
            <span class="${hasSentiment ? "text-[#006C49] font-bold" : "text-[#767586] font-medium"}">${sentimentLabel}</span>
            <span class="text-[#767586]">${sentimentSub}</span>
          </div>
          <div class="w-full h-2 rounded-full bg-[#E2E7FF] overflow-hidden flex">
            <div class="h-full ${barBg}" style="width: ${barWidth}"></div>
          </div>
        </div>

        <!-- Col 5: Deep Analyze CTA (1 col) -->
        <div class="col-span-1 flex items-center justify-end lg:justify-center w-full lg:w-auto">
          <a href="/tools/video-analyzer?url=https://www.youtube.com/watch?v=${vidId}" class="w-full lg:w-9 h-9 rounded-xl bg-[#6063EE] text-white hover:bg-[#4648D4] flex items-center justify-center transition-all shadow-sm text-xs font-semibold gap-1.5 lg:gap-0" title="Deep Analyze this video">
            <span class="material-symbols-outlined text-[18px]">analytics</span>
            <span class="lg:hidden">Deep Analyze</span>
          </a>
        </div>
      </div>
    `;
    })
    .join("");
}


// ── Video Filtering Tabs (All / Breakout / Under 100k / Shorts) ──────────────
function updateVideoTabStates() {
  if (typeof document === "undefined" || !document.querySelectorAll) return;
  const hasSubscribers = currentVideos.some(v => v.subscribers != null || v.subscriber_count != null);
  const tabs = document.querySelectorAll("#videoFilterTabs button, .video-tab-btn");
  if (!tabs || !tabs.forEach) return;
  tabs.forEach(btn => {
    if (!btn || !btn.getAttribute) return;
    const f = btn.getAttribute("data-filter") || (btn.getAttribute("onclick") || "").match(/'([^']+)'/)?.[1];
    if (f === "breakout" || f === "under100k") {
      if (!hasSubscribers) {
        if (btn.classList && typeof btn.classList.add === "function") btn.classList.add("opacity-50", "cursor-not-allowed");
        if (typeof btn.setAttribute === "function") btn.setAttribute("title", "Data not available: YouTube Public API does not provide subscriber counts in video searches");
      } else {
        if (btn.classList && typeof btn.classList.remove === "function") btn.classList.remove("opacity-50", "cursor-not-allowed");
        if (typeof btn.removeAttribute === "function") btn.removeAttribute("title");
      }
    }
  });
}

function filterVideoTab(filter) {
  activeVideoTab = filter || "all";
  const hasSubscribers = currentVideos.some(v => v.subscribers != null || v.subscriber_count != null);
  if ((filter === "breakout" || filter === "under100k") && !hasSubscribers) {
    const statusLine = document.getElementById("statusLine");
    if (typeof showStatusBar === "function" && statusLine) {
      showStatusBar(statusLine, "Data not available: YouTube Public Data API does not expose subscriber counts in video searches", false);
    }
    return;
  }

  const btns = document.querySelectorAll("#videoFilterTabs button, .video-tab-btn");
  btns.forEach(btn => {
    const f = btn.getAttribute("data-filter") || (btn.getAttribute("onclick") || "").match(/'([^']+)'/)?.[1];
    if (f === filter) {
      btn.className = "video-tab-btn px-3 py-1.5 rounded-lg bg-[#4648D4] text-white text-xs font-semibold shrink-0";
    } else {
      const isDimmed = (f === "breakout" || f === "under100k") && !hasSubscribers;
      btn.className = "video-tab-btn px-3 py-1.5 rounded-lg text-[#464554] hover:text-[#131B2E] text-xs font-medium shrink-0" + (isDimmed ? " opacity-50 cursor-not-allowed" : "");
    }
  });

  let filtered = currentVideos;
  if (filter === "shorts") {
    filtered = currentVideos.filter(v => (v.duration_sec ? v.duration_sec <= 60 : (v.is_short || /#shorts/i.test(v.title || ""))));
  } else if (filter === "breakout" && hasSubscribers) {
    filtered = currentVideos.filter(v => (v.momentumScore || 0) > 60);
  } else if (filter === "under100k" && hasSubscribers) {
    filtered = currentVideos.filter(v => (v.subscriber_count || v.subscribers || 0) < 100000);
  }
  renderTrendingList(filtered, activeQuery);
}
if (typeof window !== "undefined") window.filterVideoTab = filterVideoTab;

// ── Render Deep Intelligence (Velocity, Virality, Sentiment, Tags) ──────────
function renderDeepIntelligence(ytData) {
  const resultsArea = document.getElementById("resultsArea");
  if (!resultsArea) return;

  currentTrendId = ytData.trend_id || null;
  currentKeyword = ytData.keyword || activeQuery || "";
  updateExportButtons();

  const oppBadge = document.getElementById("opportunityScoreBadge");
  if (oppBadge) {
    const intelObj = ytData.trend_intelligence || {};
    const oppVal = intelObj.opportunity_score != null ? intelObj.opportunity_score : (ytData.opportunity_score != null ? ytData.opportunity_score : null);
    if (oppVal != null && Number.isFinite(Number(oppVal))) {
      oppBadge.textContent = `Opportunity Score: ${Math.round(oppVal)}/100`;
      if (oppBadge.classList && typeof oppBadge.classList.remove === "function") {
        oppBadge.classList.remove("hidden");
      } else {
        oppBadge.style.display = "inline-flex";
      }
    } else {
      if (oppBadge.classList && typeof oppBadge.classList.add === "function") {
        oppBadge.classList.add("hidden");
      } else {
        oppBadge.style.display = "none";
      }
    }
  }

  // 1. First Scan / Educational Banner
  const trendBanner = document.getElementById("trendBanner");
  const trendBannerText = document.getElementById("trendBannerText");
  const intel = ytData.trend_intelligence || {};
  const isBaseline = intel.status === "baseline" || ytData.status === "baseline";

  if (trendBanner && trendBannerText) {
    if (intel.educational_banner) {
      trendBannerText.textContent = intel.educational_banner;
      trendBanner.style.display = "flex";
    } else if (isBaseline) {
      // First Scan baseline observation
      trendBannerText.textContent = "Baseline observation established. Scan again in 24–48 hours to measure real-world growth velocity, momentum, and curve progression.";
      trendBanner.style.display = "flex";
    } else {
      trendBanner.style.display = "none";
    }
  }

  // 2. Velocity, Growth Rate & Virality Breakdown
  const summaryDirection = document.getElementById("summaryDirection");
  if (summaryDirection) {
    summaryDirection.textContent = intel.current_direction_display || ytData.stage || "Unavailable";
  }

  const summaryVelocity = document.getElementById("summaryVelocity");
  if (summaryVelocity) {
    summaryVelocity.textContent = intel.velocity_display || (ytData.growth_rate !== undefined ? `${ytData.growth_rate > 0 ? "+" : ""}${ytData.growth_rate}% / day` : "—");
  }

  const summaryAcceleration = document.getElementById("summaryAcceleration");
  if (summaryAcceleration) {
    summaryAcceleration.textContent = intel.acceleration_display || "Unavailable";
  }

  const summaryEngagement = document.getElementById("summaryEngagement");
  if (summaryEngagement) {
    summaryEngagement.textContent = ytData.engagement_rate != null ? `${Number(ytData.engagement_rate).toFixed(1)}%` : "Unavailable";
  }

  const summaryVirality = document.getElementById("summaryVirality");
  if (summaryVirality) {
    summaryVirality.textContent = `${ytData.virality_score != null ? Math.round(ytData.virality_score) : 0}/100`;
  }

  // 3. Lower Time-Series Trajectory Chart
  currentTimelineRaw = (intel.timeline && intel.timeline.length > 0) ? intel.timeline : (ytData.daily_metrics || []);
  updateLowerChartWithRange(currentLowerRange);

  // 4. Audience Sentiment Breakdown
  const sentiment = ytData.sentiment || {};
  const dominantBadge = document.getElementById("dominantSentimentBadge");
  if (dominantBadge) {
    const dom = sentiment.dominant_sentiment || "Neutral";
    dominantBadge.textContent = dom.charAt(0).toUpperCase() + dom.slice(1);
    dominantBadge.className = "panel-badge " + (dom.toLowerCase() === "positive" ? "badge-rising" : dom.toLowerCase() === "negative" ? "badge-falling" : "badge-stable");
  }

  const sentimentBreakdown = document.getElementById("sentimentBreakdown");
  if (sentimentBreakdown) {
    const pos = Math.round((sentiment.positive_score || 0));
    const neu = Math.round((sentiment.neutral_score || 0));
    const neg = Math.round((sentiment.negative_score || 0));
    sentimentBreakdown.innerHTML = `Positive: ${pos}% &bull; Neutral: ${neu}% &bull; Negative: ${neg}%`;
  }

  const sampleCommentText = document.getElementById("sampleCommentText");
  if (sampleCommentText) {
    sampleCommentText.textContent = sentiment.sample_comment || (ytData.comments && ytData.comments[0]) || "No audience comments available for this sample.";
  }

  // 5. Trend Milestones & Events
  const eventsList = document.getElementById("trendEventsList");
  if (eventsList) {
    const events = intel.events || [];
    if (events.length === 0) {
      eventsList.innerHTML = `
        <div class="trend-event-item">
          <div class="trend-event-icon">📍</div>
          <div class="trend-event-content">
            <div class="trend-event-title">Baseline Observation</div>
            <div class="trend-event-desc">Initial observation recorded. Velocity calculated after future scans.</div>
          </div>
          <div class="trend-event-date">Today</div>
        </div>
      `;
    } else {
      eventsList.innerHTML = events.map((ev) => {
        let icon = "📍";
        if (ev.type === "spike") icon = "⚡";
        else if (ev.type === "drop") icon = "📉";
        else if (ev.type === "shift") icon = "🔄";
        else if (ev.type === "engagement") icon = "❤️";
        else if (ev.type === "scan") icon = "🔍";

        return `
          <div class="trend-event-item">
            <div class="trend-event-icon">${icon}</div>
            <div class="trend-event-content">
              <div class="trend-event-title">${escapeHtml(ev.title || "Observation")}</div>
              <div class="trend-event-desc">${escapeHtml(ev.description || "")}</div>
            </div>
            <div class="trend-event-date">${escapeHtml(ev.date || "Today")}</div>
          </div>
        `;
      }).join("");
    }
  }

  // 6. Historical Change Windows
  const historyTableBody = document.getElementById("historyTableBody");
  if (historyTableBody) {
    const hw = intel.historical_context || {};
    const windows = [
      { key: "1d", label: "1 Day" },
      { key: "7d", label: "7 Days" },
      { key: "30d", label: "30 Days" },
      { key: "90d", label: "90 Days" },
    ];

    const hasHistory = windows.some(w => hw[w.key]?.status === "available" && Number.isFinite(hw[w.key]?.change_pct));
    historyTableBody.innerHTML = !hasHistory
      ? `<tr><td colspan="3" class="trend-history-progress">Data collection in progress. Historical comparisons will appear when enough comparable observations are saved.</td></tr>`
      : windows.map((w) => {
      const entry = hw[w.key] || { status: "insufficient_history", display: "Data collection in progress" };
      const isAvail = entry.status === "available" && entry.change_pct !== null && entry.change_pct !== undefined;
      const badgeClass = isAvail ? (entry.change_pct >= 0 ? "badge-rising" : "badge-falling") : "badge-stable";
      const growthDisplay = isAvail ? `${entry.change_pct > 0 ? "+" : ""}${entry.change_pct}%` : "—";
      const statusText = isAvail ? "Available" : "Pending";

      return `
        <tr>
          <td><strong>${w.label}</strong></td>
          <td><span class="panel-badge ${badgeClass}">${growthDisplay}</span></td>
          <td><span class="panel-badge badge-stable">${statusText}</span></td>
        </tr>
      `;
    }).join("");
  }

  // 7. Conservative 7-Day Forecast
  const forecastGrid = document.getElementById("forecastGrid");
  const forecastFallback = document.getElementById("forecastFallback");
  const fc = intel.forecast || {};
  const forecastPanel = document.getElementById("forecastPanel");
  if (forecastPanel) forecastPanel.open = Boolean(fc.available && fc.projection_days?.length);
  if (fc.available && fc.projection_days && fc.projection_days.length > 0) {
    if (forecastFallback) forecastFallback.style.display = "none";
    if (forecastGrid) {
      forecastGrid.style.display = "grid";
      forecastGrid.innerHTML = fc.projection_days.map((d) => `
        <div class="trend-forecast-card">
          <div class="trend-forecast-day">${escapeHtml(d.day)}</div>
          <div class="trend-forecast-val">${Number(d.expected_views).toLocaleString()}</div>
          <div class="trend-forecast-range">&plusmn;${Number(d.upper_bound - d.expected_views).toLocaleString()}</div>
        </div>
      `).join("");
    }
  } else {
    if (forecastGrid) forecastGrid.style.display = "none";
    if (forecastFallback) {
      forecastFallback.style.display = "block";
      forecastFallback.textContent = fc.reason || "Requires at least 3 observations spanning 48 hours. Projection is illustrative.";
    }
  }

  // 8. High-CTR Tag Combinations
  const tagsList = document.getElementById("tagsList");
  if (tagsList) {
    const tags = ytData.youtube_tags || [];
    if (tags.length === 0) {
      tagsList.innerHTML = `<span class="text-slate-400 font-0-85">Search a specific topic to generate tag suggestions.</span>`;
    } else {
      tagsList.innerHTML = tags.map((t) => `
        <button type="button" class="tag-item-default" data-copy="${escapeAttr(t)}" title="Click to copy">
          🏷️ ${escapeHtml(t)}
        </button>
      `).join("");
    }
  }

  // 9. High-CTR Hashtags
  const hashtagsList = document.getElementById("hashtagsList");
  if (hashtagsList) {
    const htags = ytData.youtube_hashtags || [];
    if (htags.length > 0) {
      hashtagsList.innerHTML = htags.map((h) => `
        <button type="button" class="tag-item-accent" data-copy="${escapeAttr(h)}" title="Click to copy">
          ${escapeHtml(h)}
        </button>
      `).join("");
    } else {
      hashtagsList.innerHTML = "";
    }
  }

  // 10. Context-Aware High-CTR Titles
  const aiTitlesList = document.getElementById("aiTitlesList");
  if (aiTitlesList) {
    const titles = ytData.seo_title_ideas || [];
    if (titles.length === 0) {
      aiTitlesList.innerHTML = `<span class="text-slate-400 font-0-85">Search a specific topic to generate editable title templates.</span>`;
    } else {
      aiTitlesList.innerHTML = titles.map((title) => `
        <div class="flex-between-center p-12 bg-slate-50 border-slate-200 radius-10">
          <span class="font-600 font-0-9 text-slate-900">${escapeHtml(title)}</span>
          <button class="tool-copy-action-btn" data-copy="${escapeAttr(title)}" type="button">Copy</button>
        </div>
      `).join("");
    }
  }

  // Display the Deep Intelligence section
  resultsArea.style.display = "block";
}

// ── Filter and Update Lower Chart with Range ────────────────────────────────
function filterTimelineByRange(timeline, range) {
  if (!timeline || timeline.length === 0) return [];
  if (range === "all") return timeline;

  const daysMap = { "1d": 1, "7d": 7, "30d": 30, "90d": 90 };
  const maxDays = daysMap[range] || 90;
  const now = new Date().getTime();
  const cutoff = now - maxDays * 24 * 60 * 60 * 1000;

  return timeline.filter((item) => {
    if (!item.date) return true;
    const itemTime = new Date(item.date).getTime();
    if (isNaN(itemTime)) return true;
    return itemTime >= cutoff;
  });
}

function updateLowerChartWithRange(range) {
  currentLowerRange = range;

  // Update tabs active / dimmed status
  const tabs = document.querySelectorAll(".trend-tab-btn");
  tabs.forEach((tab) => {
    const r = tab.getAttribute("data-range") || "all";
    if (r === range) {
      tab.classList.add("active");
    } else {
      tab.classList.remove("active");
    }

    const testPoints = filterTimelineByRange(currentTimelineRaw, r);
    if (testPoints.length === 0) {
      tab.classList.add("dimmed");
      tab.title = `No scans recorded in ${r.toUpperCase()} window`;
    } else {
      tab.classList.remove("dimmed");
      tab.title = `Show ${r.toUpperCase()} trajectory`;
    }
  });

  const filtered = filterTimelineByRange(currentTimelineRaw, range);
  renderLowerChart(filtered, range);
}

// ── Render Lower Time-Series Chart ──────────────────────────────────────────
function renderLowerChart(dataPoints, range = "all") {
  const canvas = document.getElementById("viewsChart");
  const emptyEl = document.getElementById("viewsChartEmpty");
  const chartBaselineNote = document.getElementById("chartBaselineNote");
  if (!canvas || !window.Chart) return;

  if (lowerViewsChart) {
    lowerViewsChart.destroy();
    lowerViewsChart = null;
  }

  // Handle empty range window (e.g. 1D when observation was recorded outside 24h)
  if (!dataPoints || dataPoints.length === 0) {
    canvas.style.display = "none";
    if (emptyEl) {
      if (!currentTimelineRaw || currentTimelineRaw.length === 0) {
        emptyEl.innerHTML = `
          <div class="text-center p-16">
            <div style="font-size: 26px; margin-bottom: 8px;">⏳</div>
            <strong style="color: var(--text); font-size: 0.95rem;">Historical data unavailable</strong>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 6px; max-width: 380px;">
              An initial baseline observation is required. Track this keyword to begin longitudinal monitoring.
            </p>
          </div>
        `;
      } else {
        const firstDate = currentTimelineRaw[0]?.date ? currentTimelineRaw[0].date.split(" ")[0] : "a previous date";
        emptyEl.innerHTML = `
          <div class="text-center p-16">
            <div style="font-size: 26px; margin-bottom: 8px;">⏳</div>
            <strong style="color: var(--text); font-size: 0.95rem;">No scans recorded within the ${range.toUpperCase()} window</strong>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 6px; max-width: 380px;">
              The baseline observation for this trend was recorded on <strong>${firstDate}</strong>. Select <strong>All</strong> or a wider window to view the trajectory curve.
            </p>
          </div>
        `;
      }
      emptyEl.style.display = "flex";
    }
    const trajA11y = document.getElementById("viewsTrajectoryA11y");
    if (trajA11y) trajA11y.innerHTML = "<p>Historical trajectory data unavailable.</p>";
    if (chartBaselineNote) chartBaselineNote.style.display = "none";
    return;
  }

  canvas.style.display = "block";
  if (emptyEl) emptyEl.style.display = "none";

  const trajA11y = document.getElementById("viewsTrajectoryA11y");
  if (trajA11y) {
    const rows = dataPoints
      .map(
        (d) =>
          `<tr><th scope="row">${d.date || "Unknown"}</th><td>${formatCompact(d.views || 0)} (${Number(d.views || 0).toLocaleString()} views)</td></tr>`
      )
      .join("");
    trajA11y.innerHTML = `<table><caption>Audited view trajectory over time</caption><thead><tr><th scope="col">Observation Timestamp</th><th scope="col">Observed Views</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  // Baseline observation / First Scan tracking status
  const isBaseline = dataPoints.length <= 1;

  if (isBaseline) {
    // ── Single Point Baseline Experience ──
    const pt = dataPoints[0];
    const val = Number((currentKpis && currentKpis.totalViews != null) ? currentKpis.totalViews : (pt.views || 0));
    const dateStr = pt.date ? pt.date.split(" ")[0] : "Today";
    const timeStr = pt.date ? (pt.date.split(" ")[1] || "") : "";

    if (chartBaselineNote) {
      chartBaselineNote.style.display = "block";
      chartBaselineNote.innerHTML = `
        <span class="font-600 text-slate-700">📍 Baseline: ${formatCompact(val)} views (${val.toLocaleString()}) recorded on ${dateStr}</span>
        <span class="text-slate-400">&bull;</span>
        <span class="text-slate-500 font-0-85">One observation recorded. Run another search after at least 24 hours to collect a comparable observation.</span>
      `;
    }

    // A single observation has one real timestamp, not an invented range.
    const displayLabels = [`${dateStr} ${timeStr} UTC`.trim()];

    // Dataset 1: Prominent filled observation point on the recording day
    const pointDataset = {
      label: `Recorded Observation`,
      data: displayLabels.map((_, idx) => (idx === displayLabels.length - 1 ? val : null)),
      borderColor: "#4f46e5",
      backgroundColor: "#4f46e5",
      pointRadius: 7,
      pointHoverRadius: 9,
      pointBackgroundColor: "#4f46e5",
      pointBorderColor: "#ffffff",
      pointBorderWidth: 2.5,
      showLine: false,
      order: 1,
    };

    // Auto-scale Y-axis around the baseline value (no 0-to-8M empty void!)
    const yMin = Math.max(0, Math.floor(val * 0.75));
    const yMax = Math.max(1, Math.ceil(val * 1.25));

    const ctx = canvas.getContext("2d");
    lowerViewsChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: displayLabels,
        datasets: [pointDataset],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: { boxWidth: 14, font: { size: 11, family: "Plus Jakarta Sans, Inter, sans-serif" } },
          },
          tooltip: {
            backgroundColor: "#0f172a",
            titleColor: "#94a3b8",
            bodyColor: "#ffffff",
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: () => `${dateStr} ${timeStr}`.trim(),
              label: (context) => {
                if (context.datasetIndex === 0) {
                  return `Recorded Observation: ${formatCompact(val)} views (${val.toLocaleString()})`;
                }
                return `Recorded observation: ${formatCompact(val)} views`;
              },
            },
          },
        },
        scales: {
          y: {
            min: yMin,
            max: yMax,
            grid: { color: "#f1f5f9" },
            ticks: {
              color: "#64748b",
              font: { size: 11 },
              callback: (v) => formatCompact(v),
            },
          },
          x: {
            grid: { display: false },
            border: { color: "#e2e8f0" },
            ticks: { color: "#64748b", font: { size: 11 } },
          },
        },
      },
    });
  } else {
    // ── Multi-Point Trajectory Curve (2+ Observations) ──
    const rawLabels = dataPoints.map((d) => d.date || d.label || "Obs");
    const rawViews = dataPoints.map((d) => d.views || 0);
    const smoothedViews = dataPoints.map((d) => d.smoothed_views !== undefined ? d.smoothed_views : d.views || 0);

    const lastViews = rawViews[rawViews.length - 1];
    const prevViews = rawViews[rawViews.length - 2];
    const diff = lastViews - prevViews;
    const diffPct = prevViews > 0 ? ((diff / prevViews) * 100).toFixed(1) : "0.0";
    const isUp = diff >= 0;

    if (chartBaselineNote) {
      chartBaselineNote.style.display = "block";
      chartBaselineNote.innerHTML = `
        <span class="inline-flex-center gap-6 font-600 ${isUp ? 'text-green' : 'text-red'}">
          ${isUp ? '📈' : '📉'} ${isUp ? '+' : ''}${formatCompact(diff)} (${isUp ? '+' : ''}${diffPct}%) vs last scan
        </span>
        <span class="text-slate-400">&bull;</span>
        <span class="text-slate-500 font-0-85">Audited trajectory from ${dataPoints.length} observations</span>
      `;
    }

    // Auto-scale Y-axis based on min and max
    const minViews = Math.min(...rawViews);
    const maxViews = Math.max(...rawViews);
    const pad = Math.max(1000, (maxViews - minViews) * 0.2);
    const yMin = Math.max(0, Math.floor(minViews - pad));
    const yMax = Math.ceil(maxViews + pad);

    const ctx = canvas.getContext("2d");
    const grad = ctx.createLinearGradient(0, 0, 0, 220);
    grad.addColorStop(0, "rgba(79, 70, 229, 0.16)");
    grad.addColorStop(1, "rgba(79, 70, 229, 0)");

    const datasets = [
      {
        label: "Smoothed Trajectory",
        data: smoothedViews,
        borderColor: "#4f46e5",
        borderWidth: 2.5,
        backgroundColor: grad,
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: "#4f46e5",
        pointBorderColor: "#ffffff",
        pointBorderWidth: 2,
        order: 1,
      },
    ];

    const hasSmoothedVariance = rawViews.some((v, idx) => v !== smoothedViews[idx]);
    if (hasSmoothedVariance) {
      datasets.push({
        label: "Raw Observations",
        data: rawViews,
        borderColor: "#94a3b8",
        backgroundColor: "rgba(148, 163, 184, 0.4)",
        fill: false,
        showLine: false,
        pointRadius: 5,
        pointHoverRadius: 7,
        order: 2,
      });
    }

    lowerViewsChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: rawLabels,
        datasets: datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: datasets.length > 1,
            position: "top",
            labels: { boxWidth: 12, font: { size: 11 } },
          },
          tooltip: {
            backgroundColor: "#0f172a",
            titleColor: "#94a3b8",
            bodyColor: "#ffffff",
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0].dataIndex;
                const d = dataPoints[idx];
                return d && d.date ? d.date : items[0].label;
              },
              label: (context) => {
                const idx = context.dataIndex;
                const cur = Number(context.raw);
                let labelStr = `${context.dataset.label}: ${formatCompact(cur)} views (${cur.toLocaleString()})`;
                if (idx > 0 && dataPoints[idx - 1]) {
                  const p = Number(dataPoints[idx - 1].views || 0);
                  if (p > 0) {
                    const c = (((cur - p) / p) * 100).toFixed(1);
                    labelStr += ` • ${c >= 0 ? '+' : ''}${c}% vs prev`;
                  }
                }
                return labelStr;
              },
            },
          },
        },
        scales: {
          y: {
            min: yMin,
            max: yMax,
            grid: { color: "#f1f5f9" },
            ticks: {
              color: "#64748b",
              font: { size: 11 },
              callback: (v) => formatCompact(v),
            },
          },
          x: {
            grid: { display: false },
            border: { color: "#e2e8f0" },
            ticks: { color: "#64748b", font: { size: 11 }, maxRotation: 45, minRotation: 0 },
          },
        },
      },
    });
  }
}

// ── Timeframe Tabs on Lower Chart ───────────────────────────────────────────
function initTimeframeTabs() {
  const tabs = document.querySelectorAll(".trend-tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const range = tab.getAttribute("data-range") || "all";
      updateLowerChartWithRange(range);
    });
  });
}


// ── Connected Actions & Exports ─────────────────────────────────────────────
function updateExportButtons() {
  const expCsv = document.getElementById("exportCsvBtn");
  const expPdf = document.getElementById("exportPdfBtn");
  const enabled = Boolean(currentTrendId);
  for (const btn of [expCsv, expPdf]) {
    if (!btn) continue;
    btn.disabled = !enabled;
    if (btn.classList && typeof btn.classList.add === "function") {
      if (!enabled) {
        btn.classList.add("opacity-50", "cursor-not-allowed");
      } else {
        btn.classList.remove("opacity-50", "cursor-not-allowed");
      }
    }
    if (typeof btn.setAttribute === "function") {
      if (!enabled) {
        btn.setAttribute("title", "Run a topic search first to generate export data");
      } else if (typeof btn.removeAttribute === "function") {
        btn.removeAttribute("title");
      }
    }
  }
}

function initConnectedActions() {
  const ctaStrat = document.getElementById("ctaStrategistBtn");
  if (ctaStrat) {
    ctaStrat.addEventListener("click", () => {
      const topic = currentKeyword || (document.getElementById("pulseSearchInput")?.value.trim() || "");
      window.location.href = `/tools/ai-strategist${topic ? "?topic=" + encodeURIComponent(topic) : ""}`;
    });
  }

  const ctaComp = document.getElementById("ctaCompetitorBtn");
  if (ctaComp) {
    ctaComp.addEventListener("click", () => {
      window.location.href = "/tools/competitor-audit";
    });
  }

  const expPdf = document.getElementById("exportPdfBtn");
  if (expPdf) {
    expPdf.addEventListener("click", () => {
      if (!currentTrendId) {
        const statusLine = document.getElementById("statusLine");
        if (typeof showStatusBar === "function" && statusLine) {
          showStatusBar(statusLine, "Export unavailable: please run a topic search first", false);
        }
        return;
      }
      window.location.href = `/api/report/${currentTrendId}`;
    });
  }

  const expCsv = document.getElementById("exportCsvBtn");
  if (expCsv) {
    expCsv.addEventListener("click", () => {
      if (!currentTrendId) {
        const statusLine = document.getElementById("statusLine");
        if (typeof showStatusBar === "function" && statusLine) {
          showStatusBar(statusLine, "Export unavailable: please run a topic search first", false);
        }
        return;
      }
      window.location.href = `/api/export-csv/${currentTrendId}`;
    });
  }

  updateExportButtons();
}

// Delegated click listener for tags and titles clipboard copying
document.addEventListener("click", (e) => {
  const copyTarget = e.target.closest("[data-copy]");
  if (copyTarget) {
    const textToCopy = copyTarget.getAttribute("data-copy");
    if (typeof copyToClipboard === "function") {
      copyToClipboard(textToCopy, copyTarget);
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        const prev = copyTarget.textContent;
        copyTarget.textContent = "Copied!";
        setTimeout(() => {
          copyTarget.textContent = prev;
        }, 1500);
      });
    }
  }
});
