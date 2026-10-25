/**
 * Plexudo Standalone Tools — Shared Utilities (Zero Authentication)
 */

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  const d = document.createElement("div");
  d.textContent = String(str);
  return d.innerHTML;
}

function escapeAttr(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function sanitizeUrl(url) {
  if (!url || typeof url !== "string") return "";
  const trimmed = url.trim();
  if (/^(?:javascript|data|vbscript):/i.test(trimmed)) {
    return "";
  }
  return trimmed;
}

async function fetchWithTimeout(resource, options = {}, timeoutMs = 20000) {
  const { timeout: _, ...fetchOptions } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(resource, {
      ...fetchOptions,
      signal: controller.signal
    });

    // Some hosting/proxy failures return plain text or HTML instead of JSON.
    // Wrap .json() once so every tool gets a safe object rather than throwing
    // "Unexpected token 'A'..." and losing the real server-side error context.
    const nativeJson = response.json.bind(response);
    const fallbackClone = response.clone();
    response.json = async () => {
      try {
        return await nativeJson();
      } catch (err) {
        let raw = "";
        try {
          raw = await fallbackClone.text();
        } catch (readErr) {
          // Ignore secondary body-read failures.
        }
        const trimmed = raw.trim();
        const looksLikeHtml = /<\/?(?:html|body|!doctype|head)/i.test(trimmed);
        const message = trimmed && !looksLikeHtml
          ? trimmed.slice(0, 240)
          : response.status >= 500
            ? "Server error. Please try again in a moment."
            : response.status === 404
              ? "The requested service endpoint was not found (HTTP 404)."
              : response.status === 429
                ? "API rate limit reached. Please wait a moment and try again."
                : `Unexpected server response (HTTP ${response.status}).`;
        return { error: message };
      }
    };

    return response;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw err;
  } finally {
    clearTimeout(id);
  }
}

function showStatusBar(statusEl, message, isError = false) {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.className = `tool-status-bar ${isError ? "error" : "success"}`;
  statusEl.style.display = "block";
}

function hideStatusBar(statusEl) {
  if (!statusEl) return;
  statusEl.style.display = "none";
  statusEl.textContent = "";
}

function copyToClipboard(text, btn) {
  const onSuccess = () => {
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = "Copied! ✓";
      setTimeout(() => { btn.textContent = orig; }, 2000);
    }
  };

  if (!navigator.clipboard) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand("copy");
      onSuccess();
    } catch (e) {
      console.error("Copy failed", e);
    }
    document.body.removeChild(textArea);
    return;
  }

  navigator.clipboard.writeText(text).then(onSuccess).catch((err) => {
    console.error("Copy failed", err);
  });
}

let drawerLastFocusedElement = null;

function toggleMobileMenu() {
  toggleSidebarDrawer();
}

function openSidebarDrawer() {
  drawerLastFocusedElement = document.activeElement;
  const drawer = document.getElementById("stitchMobileDrawer") || document.getElementById("mobileDrawer");
  const backdrop = document.getElementById("stitchDrawerBackdrop");
  if (drawer) {
    drawer.classList.add("active");
    drawer.setAttribute("aria-hidden", "false");
    const focusable = drawer.querySelector("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    if (focusable) {
      setTimeout(() => focusable.focus(), 50);
    }
  }
  if (backdrop) {
    backdrop.classList.add("active");
    backdrop.setAttribute("aria-hidden", "false");
  }
  document.body.style.overflow = "hidden";
}

function closeSidebarDrawer() {
  const drawer = document.getElementById("stitchMobileDrawer") || document.getElementById("mobileDrawer");
  const backdrop = document.getElementById("stitchDrawerBackdrop");
  if (drawer) {
    drawer.classList.remove("active");
    drawer.setAttribute("aria-hidden", "true");
  }
  if (backdrop) {
    backdrop.classList.remove("active");
    backdrop.setAttribute("aria-hidden", "true");
  }
  document.body.style.overflow = "";
  if (drawerLastFocusedElement && typeof drawerLastFocusedElement.focus === "function") {
    try {
      drawerLastFocusedElement.focus();
    } catch (_) {}
  }
}

function toggleSidebarDrawer() {
  const drawer = document.getElementById("stitchMobileDrawer") || document.getElementById("mobileDrawer");
  if (drawer && drawer.classList.contains("active")) {
    closeSidebarDrawer();
  } else {
    openSidebarDrawer();
  }
}

// Global dismiss listeners for accessibility
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeSidebarDrawer();
  }
});
