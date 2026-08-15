/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./apps/**/*.py", "./static/js/**/*.js"],
  theme: {
    // Replaced, not extended: two shadow levels is the whole system.
    boxShadow: {
      card: "0 1px 2px rgba(42, 39, 36, 0.06), 0 8px 24px rgba(42, 39, 36, 0.06)",
      overlay: "0 12px 40px rgba(42, 39, 36, 0.18)",
      none: "none",
    },
    extend: {
      colors: {
        cream: "#FBF8F4",
        ink: "#2A2724",
        // Darkened in core v3: the previous #7A736C and #B25C4B measured
        // 4.41:1 and 4.38:1 on cream and missed the 4.5:1 floor that the same
        // section of tech.md declares. These measure 5.26:1 and 5.49:1.
        muted: "#6E675F",
        line: "#E7E0D8",
        // Core v8: the accent follows the logo. The mark itself is #A95DA0,
        // which measures 4.17:1 on cream and 4.41:1 under white type - both
        // under the 4.5:1 floor of section 13. This is the same hue and
        // saturation carried down to 44% lightness: 5.32:1 and 5.63:1.
        accent: "#944E8C",
        accentSoft: "#F0E4EF",
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
