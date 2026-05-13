/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ceva: {
          red: "#98012E",
          redDark: "#7A0124",
          black: "#231F20",
          navy: "#0B2C5C",
          navyDark: "#081F40",
          gray: "#F5F5F7",
          grayMid: "#E5E5EA",
          grayText: "#6B6B72",
          green: "#1B7F3A",
          amber: "#E5A100",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)",
        cardLg: "0 2px 6px rgba(0,0,0,0.06), 0 12px 28px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};
