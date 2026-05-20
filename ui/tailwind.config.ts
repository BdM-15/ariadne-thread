import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ariadne: {
          ink: "#080b0f",
          panel: "#10151b",
          line: "#26313c",
          copper: "#d88a36",
          cyan: "#4dd8cf",
          signal: "#f2c94c",
          rose: "#e85d75",
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;