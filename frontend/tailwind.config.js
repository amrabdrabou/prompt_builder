/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: {
          50: "#eff0ff",
          100: "#dfe2ff",
          500: "#5e6ad2",
          600: "#5e6ad2",
          700: "#828fff"
        },
        canvas: "#010102",
        surface: {
          1: "#0f1011",
          2: "#141516",
          3: "#18191a",
          4: "#191a1b"
        },
        ink: {
          DEFAULT: "#f7f8f8",
          muted: "#d0d6e0",
          subtle: "#8a8f98",
          tertiary: "#62666d"
        },
        hairline: {
          DEFAULT: "#23252a",
          strong: "#34343a",
          tertiary: "#3e3e44"
        }
      },
      boxShadow: {
        soft: "0 20px 70px rgba(0, 0, 0, 0.38)",
        glow: "0 0 0 1px rgba(94, 106, 210, 0.22), 0 24px 80px rgba(0, 0, 0, 0.45)"
      }
    }
  },
  plugins: []
};
