// Google Analytics 4, loaded only when the page decided to load it: the
// server renders this script exactly when a measurement id is set and the
// visitor has accepted (section 16). This file never checks consent itself -
// by the time it runs, the answer was already yes.

(() => {
  const holder = document.querySelector("script[data-ga-id]");
  const measurementId = holder && holder.dataset.gaId;
  if (!measurementId) return;

  window.dataLayer = window.dataLayer || [];
  function track() {
    window.dataLayer.push(arguments);
  }
  window.gtag = track;

  track("js", new Date());
  track("config", measurementId);

  // Events are declared in markup with data-analytics and dispatched by app.js
  // and favorites.js, so no template ever carries a script.
  window.addEventListener("analytics", (event) => {
    const detail = event.detail || {};
    if (!detail.name) return;
    track("event", detail.name, {
      page_path: detail.page,
      work_article: detail.article,
    });
  });

  // The conversion of section 16: the thank you page is the counting point.
  if (window.location.pathname.replace(/\/$/, "").endsWith("/dyakuyemo")) {
    track("event", "lead_submitted", { page_path: window.location.pathname });
  }
})();
