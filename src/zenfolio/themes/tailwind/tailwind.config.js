/** @type {import('tailwindcss').Config} */
// Consolidated Tailwind config for ZenFolio Elysian theme
// All styling customizations are in input.css for maintainability
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
    // Essential prose classes
    'prose', 'prose-lg', 'prose-invert', 'prose-main', 'prose-bio', 'prose-secondary',
    // Notebook classes
    'notebook-content', 'notebook-cell', 'notebook-input', 'notebook-output',
    'notebook-error', 'markdown-cell',
    // Publication classes
    'publication-image-container', 'publication-image', 'publication-image-overlay',
    'publication-with-image',
    // Theme classes
    'elysian-card', 'hero-section', 'hero-image', 'timeline-item', 'timeline-container',
    'social-icon-link', 'reveal', 'heading', 'highlight',
  ],
}
