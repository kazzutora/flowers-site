/**
 * Design tokens — the only place colors, radii and shadows are defined.
 * Templates use these token classes exclusively; a literal #hex in any
 * template is a CI failure (tech.md §8, grepped in ci.yml).
 */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf2f6",
          100: "#fce7ef",
          200: "#fbd0e0",
          300: "#f8a8c4",
          400: "#f274a0",
          500: "#e64980",
          600: "#d02a63",
          700: "#af1d4f",
          800: "#911c44",
          900: "#7a1c3d",
          950: "#450b1f",
        },
        ink: {
          50: "#f7f7f8",
          100: "#eeeef0",
          200: "#d9d9de",
          300: "#b6b6c0",
          400: "#8c8c9a",
          500: "#6c6c7c",
          600: "#565664",
          700: "#464652",
          800: "#3b3b45",
          900: "#26262d",
          950: "#18181d",
        },
        success: { 50: "#f0faf3", 500: "#2fa860", 600: "#238a4d", 700: "#1f7a46" },
        warning: { 50: "#fdf8ec", 500: "#d99a1f", 600: "#b9800f", 700: "#9c6b12" },
        danger: { 50: "#fdf0f0", 500: "#d1443b", 600: "#b8352d", 700: "#9c2f28" },
      },
      borderRadius: {
        token: "0.625rem",
        "token-lg": "1rem",
        "token-xl": "1.5rem",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(24 24 29 / 0.06), 0 1px 3px 0 rgb(24 24 29 / 0.08)",
        "card-hover": "0 4px 10px 0 rgb(24 24 29 / 0.10)",
        "live-glow": "0 0 0 1px rgb(230 73 128 / 0.25), 0 0 24px 0 rgb(230 73 128 / 0.20)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
