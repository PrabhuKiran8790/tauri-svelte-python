/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {},
  },
  plugins: [],
  // Exclude problematic patterns from being parsed as CSS
  safelist: [],
  blocklist: ['invoke']
}