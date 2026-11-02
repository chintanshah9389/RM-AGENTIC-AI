/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#0B1F3A",
          800: "#123056",
          700: "#1A3F6F",
        },
        accent: {
          500: "#0EA5E9",
          600: "#0284C7",
        },
      },
      fontFamily: {
        sans: ["\"Source Sans 3\"", "Segoe UI", "sans-serif"],
        display: ["\"DM Sans\"", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
