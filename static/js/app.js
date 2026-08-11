// Alpine components and analytics hooks. Templates carry no inline script:
// only x-* and hx-* attributes, per section 2 of tech.md.

document.addEventListener("alpine:init", () => {
  // Festive banner. The dismissal is stored per banner identity, so changing
  // the text or the date brings it back.
  Alpine.data("banner", (hash) => ({
    visible: false,
    init() {
      this.visible = window.localStorage.getItem("banner_dismissed") !== hash;
    },
    dismiss() {
      window.localStorage.setItem("banner_dismissed", hash);
      this.visible = false;
    },
  }));

  Alpine.data("cookieConsent", () => ({
    key: "cookie_consent:v1",
    visible: false,
    init() {
      this.visible = !window.localStorage.getItem(this.key);
    },
    choose(value) {
      window.localStorage.setItem(this.key, value);
      this.visible = false;
      window.dispatchEvent(new CustomEvent("cookie-consent", { detail: value }));
    },
    accept() {
      this.choose("accepted");
    },
    reject() {
      this.choose("necessary");
    },
  }));

  Alpine.data("lightbox", (startIndex, total) => ({
    open: false,
    index: startIndex,
    total: total,
    touchX: 0,
    openAt(index) {
      this.index = Number(index) || 0;
      this.open = true;
      document.body.classList.add("is-locked");
    },
    close() {
      this.open = false;
      document.body.classList.remove("is-locked");
    },
    next() {
      if (this.total > 0) this.index = (this.index + 1) % this.total;
    },
    prev() {
      if (this.total > 0) this.index = (this.index - 1 + this.total) % this.total;
    },
    touchStart(event) {
      this.touchX = event.changedTouches[0].clientX;
    },
    touchEnd(event) {
      const delta = event.changedTouches[0].clientX - this.touchX;
      if (Math.abs(delta) < 40) return;
      if (delta < 0) this.next();
      else this.prev();
    },
  }));
});

// Analytics events are declared in markup with data-analytics; the actual
// tracker is wired only after cookie consent.
document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-analytics]");
  if (!target) return;
  window.dispatchEvent(
    new CustomEvent("analytics", {
      detail: { name: target.dataset.analytics, page: window.location.pathname },
    }),
  );
});
