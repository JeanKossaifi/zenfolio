/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.{html,j2}',
    './theme.py',
  ],
  darkMode: ['class'],
  theme: {
    extend: {
      fontFamily: {
        'display': ['Playfair Display', 'serif'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
  safelist: [
    // Only essential classes
    'prose', 'prose-lg', 'prose-invert',
    'notebook-content', 'notebook-cell', 'notebook-input', 'notebook-output',
    'notebook-error', 'markdown-cell', 'prose-main', 'prose-bio',
  ],
}
