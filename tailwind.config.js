/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./apps/**/*.py", "./static/js/**/*.js"],
  theme: {
    // Replaced, not extended: two shadow levels is the whole system.
    boxShadow: {
      card: "0 1px 2px rgba(43, 36, 41, 0.06), 0 8px 24px rgba(43, 36, 41, 0.06)",
      overlay: "0 12px 40px rgba(43, 36, 41, 0.18)",
      none: "none",
    },
    extend: {
      colors: {
        // Core v9: the neutrals carry the logo's hue at a low saturation, so
        // the page reads warm purple rather than warm beige around it.
        cream: "#F8F0F7",
        ink: "#2B2429",
        // Kept dark enough for the 4.5:1 floor of section 13: this measures
        // 5.57:1 on the cream above. Core v3 had to darken its predecessor
        // #7A736C for the same reason.
        muted: "#6D6069",
        line: "#E7D8E5",
        // Core v8: the accent follows the logo. The mark itself is #A95DA0,
        // which measures 4.17:1 on cream and 4.41:1 under white type - both
        // under the 4.5:1 floor of section 13. This is the same hue and
        // saturation carried down to 44% lightness: 5.32:1 and 5.63:1.
        accent: "#944E8C",
        // A shade lighter than it looks like it wants to be: the chips
        // set accent text on it, and #F0E0EE measured 4.45:1.
        accentSoft: "#F2E4F1",
        leaf: "#5E7355",
        success: "#4B7A52",
        danger: "#A6413A",
      },
      maxWidth: { site: "1280px" },
      // The mobile filter panel covers 90% of the viewport (section 10).
      maxHeight: { drawer: "90vh" },
      aspectRatio: { card: "4 / 5" },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ["Manrope", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      borderRadius: { sm: "4px", md: "8px", lg: "16px" },
      transitionDuration: { DEFAULT: "200ms" },
      transitionTimingFunction: { DEFAULT: "cubic-bezier(0, 0, 0.2, 1)" },
    },
  },
  plugins: [],
};
