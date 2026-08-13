// Alpine components and analytics hooks. Templates carry no inline script:
// only x-* and hx-* attributes, per section 2 of tech.md.

// Alpine core ships no x-trap, and the focus plugin would be a fourth script
// inside a 60 KB budget. Section 6 allows this to live here instead.
const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function focusableInside(container) {
  // offsetParent weeds out anything the panel keeps hidden.
  return Array.from(container.querySelectorAll(FOCUSABLE)).filter((el) => el.offsetParent !== null);
}

/** Hold the focus inside `container`; the returned call releases it and gives
 *  the focus back to whatever had it before. */
function trapFocus(container) {
  const previous = document.activeElement;

  const onKeydown = (event) => {
    if (event.key !== "Tab") return;
    const items = focusableInside(container);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (!container.contains(document.activeElement)) {
      event.preventDefault();
      first.focus();
    } else if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  document.addEventListener("keydown", onKeydown, true);

  // The panel is still hidden while open() runs, and a transition keeps it
  // hidden for a few frames more, so the first focusable has to be waited for.
  let attempts = 0;
  const moveFocusInside = () => {
    const items = focusableInside(container);
    if (items.length) {
      items[0].focus();
    } else if (++attempts < 6) {
      window.setTimeout(moveFocusInside, 60);
    }
  };
  window.requestAnimationFrame(moveFocusInside);

  return () => {
    document.removeEventListener("keydown", onKeydown, true);
    if (previous && typeof previous.focus === "function") previous.focus();
  };
}

function lockScroll(locked) {
  document.body.classList.toggle("is-locked", locked);
}

/** Shared behaviour of every overlay: open, close, lock, trap, hand back. */
function overlay(id, extra = {}) {
  return {
    isOpen: false,
    release: null,
    id: id,
    openPanel() {
      if (this.isOpen) return;
      this.isOpen = true;
      lockScroll(true);
      this.release = trapFocus(this.$refs.panel);
    },
    close() {
      if (!this.isOpen) return;
      this.isOpen = false;
      lockScroll(false);
      if (this.release) {
        this.release();
        this.release = null;
      }
    },
    openIfMine(event) {
      if (event.detail === this.id) this.openPanel();
    },
    ...extra,
  };
}

document.addEventListener("alpine:init", () => {
  Alpine.data("filterDrawer", (id) => overlay(id));
  Alpine.data("modalDialog", (id) => overlay(id));
  Alpine.data("mobileMenu", () => overlay("mobile-menu"));

  Alpine.data("stickyHeader", () => ({
    scrolled: false,
    onScroll() {
      this.scrolled = window.scrollY > 24;
    },
  }));

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
    release: null,
    openAt(index) {
      this.index = Number(index) || 0;
      this.open = true;
      lockScroll(true);
      this.release = trapFocus(this.$refs.panel);
    },
    close() {
      if (!this.open) return;
      this.open = false;
      lockScroll(false);
      if (this.release) {
        this.release();
        this.release = null;
      }
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
