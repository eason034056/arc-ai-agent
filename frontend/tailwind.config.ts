import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#FFFFFF',
          100:'#DCECF5',
          200:'#B9D8EA',
          300: '#D7E2E5',
          400: '#38bdf8',
          500: '#B7D1DA',
          600: '#00B3FF',
          700: '#078FC9',
          800: '#2E3137',
          900: '#15223C',
        },
      },
      boxShadow: {
        'card' : '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }
    },
  },
  plugins: [],
}

export default config

