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
        muted: "#7A736C",
        line: "#E7E0D8",
        accent: "#B25C4B",
        accentSoft: "#F2E3DF",
        leaf: "#5E7355",
        success: "#4B7A52",
        danger: "#A6413A",
      },
      maxWidth: { site: "1280px" },
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
