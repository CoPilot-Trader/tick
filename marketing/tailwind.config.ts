import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["var(--f-mono)"],
        sans: ["var(--f-sans)"],
      },
      colors: {
        ink: {
          bg: "var(--bg)",
          panel: "var(--panel)",
          border: "var(--bd)",
          text: "var(--ink)",
          muted: "var(--ink-muted)",
          accent: "var(--accent)",
          up: "var(--up)",
          down: "var(--down)",
        },
      },
    },
  },
  plugins: [],
};

export default config;
