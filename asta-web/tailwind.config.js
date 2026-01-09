/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        asta: {
          deep: "#11111F",      // The Navy Background
          platinum: "#C1C6C8",  // The Text
          card: "rgba(17, 17, 31, 0.95)", 
        }
      },
      fontFamily: {
        sans: ['"Open Sans"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
