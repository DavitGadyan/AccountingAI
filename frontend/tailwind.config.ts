import type { Config } from "tailwindcss";

// Design tokens are CSS variables so the architecture explorer's canvas can read the
// same palette the DOM uses, and so a theme switch does not need a rebuild.
const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--canvas) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-raised": "rgb(var(--surface-raised) / <alpha-value>)",
        // The explorer needs a pressed state and a recessed well; naming them here
        // rather than reaching for a grey keeps the graph on the same palette as the
        // rest of the app when the theme flips.
        "surface-active": "rgb(var(--surface-active) / <alpha-value>)",
        "surface-sunken": "rgb(var(--surface-sunken) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        primary: "rgb(var(--text-primary) / <alpha-value>)",
        secondary: "rgb(var(--text-secondary) / <alpha-value>)",
        tertiary: "rgb(var(--text-tertiary) / <alpha-value>)",
        accent: "rgb(var(--accent) / <alpha-value>)",
        // Requirement states carry meaning, so they are named for the meaning rather
        // than the colour: a "protective" filing is not a warning, it is a decision.
        required: "rgb(var(--required) / <alpha-value>)",
        protective: "rgb(var(--protective) / <alpha-value>)",
        analysis: "rgb(var(--analysis) / <alpha-value>)",
        cleared: "rgb(var(--cleared) / <alpha-value>)",
        blocking: "rgb(var(--blocking) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
