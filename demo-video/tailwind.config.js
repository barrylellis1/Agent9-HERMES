/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        satoshi: ['Satoshi', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Decision Studio dark clarity palette
        ds: {
          bg: '#020617',        // slate-950
          surface: '#0f172a',   // slate-900
          card: '#1e293b',      // slate-800
          border: '#334155',    // slate-700
          muted: '#64748b',     // slate-500
          text: '#f8fafc',      // slate-50
          accent: '#4f46e5',    // indigo-600
          'accent-light': '#818cf8', // indigo-400
          emerald: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
        },
      },
    },
  },
  plugins: [],
};
