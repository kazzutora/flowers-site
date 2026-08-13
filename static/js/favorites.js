// The collection lives in the browser (section 10). No account, no cookie:
// a list of work numbers in localStorage, and a link that carries them.

const FAVORITES_KEY = "favorites";
const FAVORITES_LIMIT = 50;

/** The same rules `catalog.filters.parse_articles` applies on the server, in
 *  the same order: digits only, positive, duplicates dropped, and only then
 *  the limit. Number() was looser - it accepted "7.0" and "0x10", which the
 *  server throws away - and slicing before the duplicates were gone let a
 *  repeated number eat a place in the fifty. */
function normalizeFavorites(values) {
  const picked = [];
  for (const value of values) {
    const candidate = String(value).trim();
    if (!/^\d+$/.test(candidate)) continue;
    const number = Number(candidate);
    if (number <= 0 || picked.includes(number)) continue;
    picked.push(number);
    if (picked.length === FAVORITES_LIMIT) break;
  }
  return picked;
}

function readFavorites() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(FAVORITES_KEY));
    if (!Array.isArray(stored)) return [];
    return normalizeFavorites(stored);
  } catch (error) {
    return [];
  }
}

function writeFavorites(list) {
  window.localStorage.setItem(FAVORITES_KEY, JSON.stringify(normalizeFavorites(list)));
}

// Read by the hx-vals of the favourites page, which asks the server to render
// the cards for exactly these numbers.
window.favoriteArticles = () => readFavorites().join(",");

document.addEventListener("alpine:init", () => {
  Alpine.store("favorites", {
    items: readFavorites(),

    has(article) {
      return this.items.includes(Number(article));
    },

    toggle(article) {
      const number = Number(article);
      if (!Number.isInteger(number) || number <= 0) return;
      if (this.has(number)) {
        this.items = this.items.filter((value) => value !== number);
      } else if (this.items.length < FAVORITES_LIMIT) {
        this.items = [...this.items, number];
        window.dispatchEvent(
          new CustomEvent("analytics", {
            detail: { name: "favorite_add", article: number, page: window.location.pathname },
          }),
        );
      }
      writeFavorites(this.items);
    },

    get count() {
      return this.items.length;
    },

    get shareUrl() {
      return `${window.location.origin}/obrane/?a=${this.items.join(",")}`;
    },
  });

  Alpine.data("collectionLink", () => ({
    copied: false,
    async copy() {
      await navigator.clipboard.writeText(Alpine.store("favorites").shareUrl);
      this.copied = true;
      window.setTimeout(() => {
        this.copied = false;
      }, 2000);
    },
  }));
});

// Every enquiry form carries the collection, so the owner sees the whole list.
// Only when the server left the field empty: on a shared /obrane/?a=... the
// visitor is looking at somebody else's collection, and their own browser has
// a different one, or none at all.
document.addEventListener("submit", (event) => {
  const field = event.target.querySelector("input[data-favorites]");
  if (field && !field.value) field.value = readFavorites().join(",");
});
