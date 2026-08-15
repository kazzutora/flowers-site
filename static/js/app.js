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

  // The collection lives in the browser, so the heart reads its own state out
  // of the store rather than out of the response.
  Alpine.data("favoriteButton", (article) => ({
    article: Number(article),
    // Set for the length of the beat, so the heart answers the tap.
    popping: false,
    get active() {
      const store = Alpine.store("favorites");
      return store ? store.has(this.article) : false;
    },
    toggle() {
      const store = Alpine.store("favorites");
      if (!store) return;
      const adding = !store.has(this.article);
      store.toggle(this.article);
      // Only on the way in: removing something does not deserve a flourish.
      if (!adding) return;
      this.popping = false;
      requestAnimationFrame(() => {
        this.popping = true;
        setTimeout(() => (this.popping = false), 320);
      });
    },
  }));

  // The map is the only third party request on a public page, and it waits
  // until the visitor is nearly at it.
  Alpine.data("lazyMap", () => ({
    loaded: false,
    init() {
      if (!("IntersectionObserver" in window)) {
        this.loaded = true;
        return;
      }
      const observer = new IntersectionObserver(
        (entries) => {
          if (!entries.some((entry) => entry.isIntersecting)) return;
          this.loaded = true;
          observer.disconnect();
        },
        { rootMargin: "200px" },
      );
      observer.observe(this.$el);
    },
  }));

  // The hero fan leans a little towards the pointer. Decoration only: without
  // a pointer, and for a visitor who asked for less motion, the fan simply
  // stands still.
  Alpine.data("heroFan", () => ({
    init() {
      const still = window.matchMedia("(prefers-reduced-motion: reduce)");
      if (still.matches || !window.matchMedia("(hover: hover)").matches) return;
      this.$el.addEventListener("pointermove", (event) => this.lean(event));
      this.$el.addEventListener("pointerleave", () => this.rest());
    },
    lean(event) {
      const box = this.$el.getBoundingClientRect();
      // -1 at the left edge, 1 at the right one. Six degrees is enough to read
      // as depth and small enough not to distort the photographs.
      const across = (event.clientX - box.left) / box.width - 0.5;
      this.$el.style.setProperty("--hero-tilt", `${(across * 12).toFixed(2)}deg`);
    },
    rest() {
      this.$el.style.removeProperty("--hero-tilt");
    },
  }));

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

// Ten seconds, the same ceiling the Telegram client works to. Without it a
// request that never answers leaves the button disabled for good.
if (window.htmx) window.htmx.config.timeout = 10000;

// Every htmx request owes the visitor an error state (section 7). The markup
// and its wording are rendered by the server into #htmx-error; this only shows
// it and remembers what to retry. The existing page is never torn down.
let lastFailedRequest = null;

function htmxErrorRegion() {
  return document.getElementById("htmx-error");
}

function showHtmxError(detail) {
  lastFailedRequest = (detail && detail.requestConfig) || null;
  const region = htmxErrorRegion();
  if (region) region.hidden = false;
}

function hideHtmxError() {
  const region = htmxErrorRegion();
  if (region) region.hidden = true;
}

document.addEventListener("htmx:responseError", (event) => showHtmxError(event.detail));
document.addEventListener("htmx:sendError", (event) => showHtmxError(event.detail));
document.addEventListener("htmx:timeout", (event) => showHtmxError(event.detail));
document.addEventListener("htmx:beforeRequest", hideHtmxError);

document.addEventListener("click", (event) => {
  if (event.target.closest("[data-htmx-error-dismiss]")) {
    hideHtmxError();
    return;
  }
  if (!event.target.closest("[data-htmx-retry]")) return;
  hideHtmxError();
  const config = lastFailedRequest;
  if (!config || !window.htmx) return;
  window.htmx.ajax(config.verb, config.path, {
    source: config.elt,
    target: config.target,
    values: config.parameters,
  });
});

// Turnstile renders the widgets it finds when its script loads. A form that
// comes back from /hx/lead/ with validation errors carries a fresh, unrendered
// one, and without this the second attempt would post no token at all.
document.addEventListener("htmx:afterSwap", (event) => {
  if (!window.turnstile) return;
  const target = event.target;
  const widgets = Array.from(target.querySelectorAll(".cf-turnstile:empty"));
  if (target.matches && target.matches(".cf-turnstile:empty")) widgets.push(target);
  widgets.forEach((widget) => window.turnstile.render(widget));
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
