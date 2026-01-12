export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Importante para o tema escuro que você gostou
  theme: {
    extend: {
      colors: {
        "primary": "#0fb87d", // A cor verde do seu design
        "background-light": "#f6f8f7",
        "background-dark": "#0f172a",
      },
      fontFamily: {
        "display": ["Space Grotesk", "sans-serif"],
        "mono": ["JetBrains Mono", "monospace"]
      }
    },
  },
  plugins: [],
}