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
      // Mirrored into a cookie so the server can decide whether to put the
      // analytics tag on the page at all. Without it "no consent, no script"
      // would be a promise only the browser could keep.
      document.cookie = `cookie_consent=${value}; path=/; max-age=31536000; SameSite=Lax`;
      this.visible = false;
      window.dispatchEvent(new CustomEvent("cookie-consent", { detail: value }));
      if (value === "accepted") window.location.reload();
    },
    accept() {
      this.choose("accepted");
    },
    reject() {
      this.choose("necessary");
    },
  }));

  // The article is copied without the number sign: it is dictated on the
  // phone and pasted into a message.
  Alpine.data("copyNumber", (value) => ({
    copied: false,
    async copy() {
      try {
        await navigator.clipboard.writeText(value);
      } catch (error) {
        const field = document.createElement("textarea");
        field.value = value;
        document.body.appendChild(field);
        field.select();
        document.execCommand("copy");
        field.remove();
      }
      this.copied = true;
      window.setTimeout(() => {
        this.copied = false;
      }, 2000);
    },
  }));

  Alpine.data("shareLink", () => ({
    async share() {
      const data = { title: document.title, url: window.location.href };
      if (navigator.share) {
        try {
          await navigator.share(data);
          return;
        } catch (error) {
          if (error.name === "AbortError") return;
        }
      }
      await navigator.clipboard.writeText(data.url);
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
  // Section 16: an event carries the work it happened on and the page it came
  // from. The article is declared once per block, not once per button.
  const holder = target.closest("[data-analytics-article]");
  window.dispatchEvent(
    new CustomEvent("analytics", {
      detail: {
        name: target.dataset.analytics,
        page: window.location.pathname,
        article: holder ? Number(holder.dataset.analyticsArticle) : undefined,
      },
    }),
  );
});
