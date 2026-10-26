/**
 * YouTube Video Virality Analyzer Client JS
 */
const videoUrlInput = document.getElementById("videoUrlInput");
const analyzeVideoBtn = document.getElementById("analyzeVideoBtn");
const statusLine = document.getElementById("statusLine");
const loadingArea = document.getElementById("loadingArea");
const resultsArea = document.getElementById("resultsArea");

const videoThumb = document.getElementById("videoThumb");
const videoTitle = document.getElementById("videoTitle");
const videoChannel = document.getElementById("videoChannel");
const videoDate = document.getElementById("videoDate");
const videoDescription = document.getElementById("videoDescription");

const videoViralityVal = document.getElementById("videoViralityVal");
const videoViewsVal = document.getElementById("videoViewsVal");
const videoEngagementVal = document.getElementById("videoEngagementVal");

const copyTitleBtn = document.getElementById("copyTitleBtn");
const copyDescBtn = document.getElementById("copyDescBtn");
const copyTagsBtn = document.getElementById("copyTagsBtn");

// SEO Intelligence Engine UI Elements
const seoQualityPanel = document.getElementById("seoQualityPanel");
const seoScoreVal = document.getElementById("seoScoreVal");
const seoScoreCircle = document.getElementById("seoScoreCircle");
const seoRatingTitle = document.getElementById("seoRatingTitle");
const seoScoreBasisNote = document.getElementById("seoScoreBasisNote");
const seoBreakdownGrid = document.getElementById("seoBreakdownGrid");
const toggleDraftBtn = document.getElementById("toggleDraftBtn");
const seoDraftCard = document.getElementById("seoDraftCard");
const seoDraftStatus = document.getElementById("seoDraftStatus");
const seoFocusKeywordInput = document.getElementById("seoFocusKeywordInput");
const seoDraftTitleInput = document.getElementById("seoDraftTitleInput");
const seoDraftDescInput = document.getElementById("seoDraftDescInput");
const seoDraftTagsInput = document.getElementById("seoDraftTagsInput");
const reanalyzeSeoBtn = document.getElementById("reanalyzeSeoBtn");
const seoSuggestionsList = document.getElementById("seoSuggestionsList");
const seoUnavailableGrid = document.getElementById("seoUnavailableGrid");


let currentVideoTitle = "";
let currentVideoDescription = "";
let currentVideoTags = [];

const sentimentStats = document.getElementById("sentimentStats");
const sampleCommentText = document.getElementById("sampleCommentText");
const tagsContainer = document.getElementById("tagsContainer");
const commentsList = document.getElementById("commentsList");

if (analyzeVideoBtn) analyzeVideoBtn.addEventListener("click", runVideoAnalysis);

if (toggleDraftBtn) {
  toggleDraftBtn.addEventListener("click", () => {
    if (!seoDraftCard) return;
    const isHidden = seoDraftCard.style.display === "none";
    seoDraftCard.style.display = isHidden ? "block" : "none";
    toggleDraftBtn.textContent = isHidden ? "✕ Close Draft Editor" : "✏️ Edit & Test Draft";
    toggleDraftBtn.setAttribute("aria-expanded", String(isHidden));
  });
}

if (reanalyzeSeoBtn) {
  reanalyzeSeoBtn.addEventListener("click", runDraftSeoEvaluation);
}

if (videoUrlInput) {
  videoUrlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runVideoAnalysis();
  });
}

if (copyTitleBtn) copyTitleBtn.addEventListener("click", () => safeCopyToClipboard(currentVideoTitle, copyTitleBtn));
if (copyDescBtn) copyDescBtn.addEventListener("click", () => safeCopyToClipboard(currentVideoDescription, copyDescBtn));
if (copyTagsBtn) copyTagsBtn.addEventListener("click", () => {
  const tagsText = currentVideoTags.length > 0 ? currentVideoTags.join(", ") : "";
  safeCopyToClipboard(tagsText, copyTagsBtn);
});

async function safeCopyToClipboard(text, btnElement) {
  if (!text) return false;
  let copied = false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      copied = true;
    } else {
      throw new Error("Clipboard API unavailable");
    }
  } catch (err) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    textarea.setAttribute("readonly", "");
    document.body.appendChild(textarea);
    textarea.select();
    try { copied = document.execCommand("copy"); } catch (e) { copied = false; }
    document.body.removeChild(textarea);
  }

  if (copied && btnElement) {
    const originalText = btnElement.textContent;
    btnElement.textContent = "Copied!";
    btnElement.classList.add("copied");
    setTimeout(() => {
      btnElement.textContent = originalText;
      btnElement.classList.remove("copied");
    }, 2000);
  }
  return copied;
}

function decodeHtmlEntities(str) {
  if (!str) return "";
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value;
}

function createVideoTag(tag) {
  const el = document.createElement("button");
  el.type = "button";
  el.className = "panel-badge";
  el.style.cssText = "background:#f1f5f9; color:#0f172a; padding:6px 12px; border-radius:8px; font-size:13px; cursor:pointer;";
  el.title = "Click to copy";
  el.textContent = `🏷️ ${tag}`;
  el.addEventListener("click", () => safeCopyToClipboard(tag, el));
  return el;
}

async function runVideoAnalysis() {
  const url = videoUrlInput ? videoUrlInput.value.trim() : "";
  if (!url) {
    showStatusBar(statusLine, "Please enter a valid YouTube video URL or ID", true);
    return;
  }

  hideStatusBar(statusLine);
  if (loadingArea) loadingArea.style.display = "block";
  if (resultsArea) resultsArea.style.display = "none";
  if (analyzeVideoBtn) analyzeVideoBtn.disabled = true;

  try {
    const res = await fetchWithTimeout("/api/video-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    }, 25000);

    const data = await res.json();
    if (!res.ok || data.error) {
      showStatusBar(statusLine, data.error || data.message || "Could not analyze video. Please verify the link.", true);
      return;
    }
    renderVideoResults(data);
  } catch (err) {
    showStatusBar(statusLine, err.message || "Network error. Please try again.", true);
  } finally {
    if (loadingArea) loadingArea.style.display = "none";
    if (analyzeVideoBtn) analyzeVideoBtn.disabled = false;
  }
}

function renderVideoResults(data) {
  currentVideoTitle = (data.title || "Unknown Video").trim();
  currentVideoTags = Array.isArray(data.tags) ? data.tags : [];

  if (videoThumb) videoThumb.src = sanitizeUrl(data.thumbnail || "");
  if (videoTitle) videoTitle.textContent = currentVideoTitle;
  if (videoChannel) videoChannel.textContent = data.channel_title || data.channel_name || "Unknown Channel";
  if (videoDate) {
    const pubDate = data.published_at || data.upload_date;
    videoDate.textContent = pubDate ? pubDate.slice(0, 10) : "—";
  }

  const rawDesc = (data.description != null && String(data.description).trim() !== "") ? String(data.description).trim() : "";
  if (rawDesc) {
    const decoded = decodeHtmlEntities(rawDesc).replace(/<br\s*\/?>/gi, "\n");
    currentVideoDescription = decoded;
    if (videoDescription) {
      videoDescription.textContent = decoded;
      videoDescription.classList.remove("is-empty");
      videoDescription.style.display = "block";
    }
    if (copyDescBtn) copyDescBtn.disabled = false;
  } else {
    currentVideoDescription = "";
    if (videoDescription) {
      videoDescription.textContent = "No description available.";
      videoDescription.classList.add("is-empty");
      videoDescription.style.display = "block";
    }
    if (copyDescBtn) copyDescBtn.disabled = true;
  }

  if (copyTagsBtn) copyTagsBtn.disabled = currentVideoTags.length === 0;
  if (videoViralityVal) videoViralityVal.textContent = `${data.virality_score || 0}/100`;
  if (videoViewsVal) videoViewsVal.textContent = Number(data.views || data.view_count || 0).toLocaleString();
  if (videoEngagementVal) videoEngagementVal.textContent = data.engagement_rate != null ? `${data.engagement_rate}%` : "Unavailable";

  const s = data.sentiment || {};
  if (sentimentStats) sentimentStats.textContent = `Positive: ${s.positive_score || 0}% • Neutral: ${s.neutral_score || 0}% • Negative: ${s.negative_score || 0}%`;
  if (sampleCommentText) sampleCommentText.textContent = s.sample_comment ? `"${s.sample_comment}"` : "No sample comment recorded.";

  if (tagsContainer) {
    tagsContainer.replaceChildren();
    if (currentVideoTags.length === 0) {
      const empty = document.createElement("span");
      empty.className = "tool-empty-note";
      empty.textContent = "No tags provided for this upload";
      tagsContainer.appendChild(empty);
    } else {
      currentVideoTags.forEach(tag => tagsContainer.appendChild(createVideoTag(tag)));
    }
  }

  if (commentsList) {
    commentsList.replaceChildren();
    const comments = Array.isArray(data.comments) ? data.comments : [];
    if (comments.length === 0) {
      const empty = document.createElement("div");
      empty.className = "tool-empty-note";
      empty.textContent = "No public comments available.";
      commentsList.appendChild(empty);
    } else {
      comments.slice(0, 10).forEach(comment => {
        const item = document.createElement("div");
        item.style.cssText = "padding:12px 14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; font-size:13px; color:#334155; line-height:1.5;";
        item.textContent = comment && typeof comment === "object" ? (comment.text || "") : String(comment || "");
        commentsList.appendChild(item);
      });
    }
  }


  // Prefill SEO Draft Fields
  if (seoDraftTitleInput) seoDraftTitleInput.value = currentVideoTitle;
  if (seoDraftDescInput) seoDraftDescInput.value = currentVideoDescription;
  if (seoDraftTagsInput) seoDraftTagsInput.value = currentVideoTags.join(", ");

  if (data.seo_quality) {
    renderSeoQuality(data.seo_quality);
  } else if (currentVideoTitle) {
    // Fallback: evaluate SEO metadata directly
    fetchWithTimeout("/api/seo/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: currentVideoTitle,
        description: currentVideoDescription,
        tags: currentVideoTags
      })
    }, 15000)
      .then(res => res.json())
      .then(seoRes => { if (!seoRes.error) renderSeoQuality(seoRes); })
      .catch(() => {});
  }

  if (resultsArea) resultsArea.style.display = "block";
}


async function runDraftSeoEvaluation() {
  if (!seoDraftTitleInput) return;
  const draftTitle = seoDraftTitleInput.value.trim();
  if (!draftTitle) {
    if (seoDraftStatus) showStatusBar(seoDraftStatus, "Title is required for SEO evaluation", true);
    return;
  }

  const draftDesc = seoDraftDescInput ? seoDraftDescInput.value : "";
  const rawTags = seoDraftTagsInput ? seoDraftTagsInput.value : "";
  const draftTags = rawTags.split(",").map(t => t.trim()).filter(Boolean);
  const focusKw = seoFocusKeywordInput ? seoFocusKeywordInput.value.trim() : "";

  if (seoDraftStatus) hideStatusBar(seoDraftStatus);
  if (reanalyzeSeoBtn) {
    reanalyzeSeoBtn.disabled = true;
    reanalyzeSeoBtn.textContent = "Evaluating Draft…";
  }

  try {
    const payload = {
      title: draftTitle,
      description: draftDesc,
      tags: draftTags,
    };
    if (focusKw) payload.focus_keyword = focusKw;

    const res = await fetchWithTimeout("/api/seo/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 15000);

    const seoData = await res.json();
    if (!res.ok || seoData.error) {
      if (seoDraftStatus) showStatusBar(seoDraftStatus, seoData.error || "Failed to evaluate SEO draft", true);
      return;
    }

    renderSeoQuality(seoData);
    if (seoDraftStatus) showStatusBar(seoDraftStatus, "✅ Draft re-evaluated successfully!", false);
  } catch (err) {
    if (seoDraftStatus) showStatusBar(seoDraftStatus, err.message || "Network error evaluating draft", true);
  } finally {
    if (reanalyzeSeoBtn) {
      reanalyzeSeoBtn.disabled = false;
      reanalyzeSeoBtn.textContent = "Re-evaluate Draft ⚡";
    }
  }
}

function renderSeoQuality(seoData) {
  if (!seoData) return;

  const score = seoData.score != null ? Math.round(seoData.score) : 0;
  if (seoScoreVal) seoScoreVal.textContent = String(score);
  if (seoScoreCircle) {
    seoScoreCircle.setAttribute("aria-label", `SEO Quality Score: ${score} out of 100`);
    let borderColor = "#0284c7";
    if (score >= 80) borderColor = "#16a34a";
    else if (score >= 60) borderColor = "#0284c7";
    else if (score >= 40) borderColor = "#ca8a04";
    else borderColor = "#dc2626";
    seoScoreCircle.style.borderColor = borderColor;
  }

  if (seoRatingTitle) {
    if (score >= 80) seoRatingTitle.textContent = "SEO Quality: Well-Optimized";
    else if (score >= 60) seoRatingTitle.textContent = "SEO Quality: Good Foundation";
    else if (score >= 40) seoRatingTitle.textContent = "SEO Quality: Needs Optimization";
    else seoRatingTitle.textContent = "SEO Quality: Critical Metadata Gaps";
  }

  if (seoScoreBasisNote) {
    const basis = seoData.score_basis || {};
    if (basis.unavailable_components && basis.unavailable_components.includes("focus_keyword")) {
      seoScoreBasisNote.textContent = `Calculated on available components (${basis.available_max || 75} pt basis, normalized to 100). Add a Focus Keyword for full 100-pt rubric.`;
    } else {
      seoScoreBasisNote.textContent = "Evaluated against 100-point Plexudo YouTube metadata heuristic rubric.";
    }
  }

  // Render Component Breakdown
  if (seoBreakdownGrid) {
    seoBreakdownGrid.replaceChildren();
    const breakdown = Array.isArray(seoData.breakdown) ? seoData.breakdown : [];
    breakdown.forEach(item => {
      const card = document.createElement("div");
      card.className = "seo-comp-card";

      const top = document.createElement("div");
      top.className = "seo-comp-top";

      const name = document.createElement("div");
      name.className = "seo-comp-name";
      name.textContent = item.label || item.id;

      const pts = document.createElement("div");
      pts.className = "seo-comp-points";
      pts.textContent = item.points != null ? `${item.points}/${item.max}` : `—/${item.max}`;

      top.appendChild(name);
      top.appendChild(pts);

      const badgeWrap = document.createElement("div");
      const badge = document.createElement("span");
      const statusKey = String(item.status || "pass").toLowerCase();
      badge.className = `seo-badge seo-badge-${statusKey}`;
      badge.textContent = statusKey.toUpperCase();
      badgeWrap.appendChild(badge);

      const evidence = document.createElement("div");
      evidence.className = "seo-comp-evidence";
      evidence.textContent = item.evidence || "";

      card.appendChild(top);
      card.appendChild(badgeWrap);
      card.appendChild(evidence);

      seoBreakdownGrid.appendChild(card);
    });
  }

  // Render Prioritized Suggestions
  if (seoSuggestionsList) {
    seoSuggestionsList.replaceChildren();
    const suggestions = Array.isArray(seoData.suggestions) ? seoData.suggestions : [];
    if (suggestions.length === 0) {
      const clean = document.createElement("div");
      clean.style.cssText = "padding:14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:13px; color:#166534;";
      clean.textContent = "🎉 Excellent! No critical metadata optimization issues detected.";
      seoSuggestionsList.appendChild(clean);
    } else {
      suggestions.forEach(s => {
        const item = document.createElement("div");
        item.className = "seo-suggestion-item";

        const top = document.createElement("div");
        top.className = "seo-suggestion-top";

        const pBadge = document.createElement("span");
        const priorityNum = s.priority || 3;
        pBadge.className = `seo-badge ${priorityNum === 1 ? 'seo-badge-fail' : (priorityNum === 2 ? 'seo-badge-warn' : 'seo-badge-pass')}`;
        pBadge.textContent = priorityNum === 1 ? 'PRIORITY 1 — CRITICAL' : (priorityNum === 2 ? 'PRIORITY 2 — HIGH' : 'PRIORITY 3 — TIP');

        const compTag = document.createElement("span");
        compTag.style.cssText = "font-size:11px; color:#64748b; font-weight:700; text-transform:uppercase;";
        compTag.textContent = s.component || "METADATA";

        top.appendChild(pBadge);
        top.appendChild(compTag);

        const msg = document.createElement("div");
        msg.className = "seo-suggestion-msg";
        msg.textContent = s.message || "";

        const fix = document.createElement("div");
        fix.className = "seo-suggestion-fix";
        fix.textContent = `💡 Recommended Fix: ${s.fix || s.message || ''}`;

        item.appendChild(top);
        item.appendChild(msg);
        item.appendChild(fix);
        seoSuggestionsList.appendChild(item);
      });
    }
  }

  // Render Unavailable Telemetry
  if (seoUnavailableGrid) {
    seoUnavailableGrid.replaceChildren();
    const unavail = seoData.unavailable || {};
    const unavailLabels = {
      observed_performance: "📊 Observed Channel Performance",
      ranking_evidence: "🎯 Search Ranking Position",
      vph: "⚡ Real-time Velocity (VPH)"
    };
    Object.keys(unavail).forEach(key => {
      const u = unavail[key];
      const card = document.createElement("div");
      card.className = "seo-unavail-card";

      const title = document.createElement("div");
      title.className = "seo-unavail-title";
      title.textContent = unavailLabels[key] || key;

      const badge = document.createElement("span");
      badge.className = "seo-badge seo-badge-unavail";
      badge.textContent = "UNAVAILABLE BY DESIGN";
      badge.style.display = "inline-block";
      badge.style.marginBottom = "6px";

      const reason = document.createElement("div");
      reason.textContent = u.reason || "Telemetry not available.";

      card.appendChild(title);
      card.appendChild(badge);
      card.appendChild(reason);
      seoUnavailableGrid.appendChild(card);
    });
  }
}
