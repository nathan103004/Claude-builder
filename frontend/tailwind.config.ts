import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Quebec flag blue (fleurdelisé) — overrides Tailwind's default blue
        blue: {
          50:  "#EAF0FB",
          100: "#C9D8F5",
          200: "#A0BCEE",
          300: "#6E99E5",
          400: "#3D77DC",
          500: "#1557CC",
          600: "#003DA5", // Quebec flag blue — primary action colour
          700: "#002F80",
          800: "#00215B",
          900: "#001338",
          950: "#000A20",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
