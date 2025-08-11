/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.{html,j2}',
    './theme.py',
    // Only scan essential files for classes
    '../base_theme.py',
  ],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        text: {
          DEFAULT: 'var(--text)',
          dark: 'var(--dark-text)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          dark: 'var(--dark-secondary)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          dark: 'var(--dark-accent)',
        },
        surface: {
          DEFAULT: 'var(--surface)',
          dark: 'var(--dark-surface)',
        },
        border: {
          DEFAULT: 'var(--border)',
          dark: 'var(--dark-border)',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },
      fontFamily: {
        'display': ['Playfair Display', 'serif'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'slow-pulse': 'slow-pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'slow-pulse': {
          '50%': { opacity: '0.8', transform: 'scale(1.05)' }
        }
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            maxWidth: 'none',
            '--tw-prose-body': theme('colors.gray[900]'),
            '--tw-prose-headings': theme('colors.gray[900]'),
            '--tw-prose-links': theme('colors.teal[600]'),
            '--tw-prose-bold': theme('colors.gray[900]'),
            '--tw-prose-counters': theme('colors.gray[500]'),
            '--tw-prose-bullets': theme('colors.gray[400]'),
            '--tw-prose-hr': theme('colors.gray[200]'),
            '--tw-prose-quotes': theme('colors.gray[900]'),
            '--tw-prose-quote-borders': theme('colors.gray[200]'),
            '--tw-prose-captions': theme('colors.gray[600]'),
            '--tw-prose-code': theme('colors.gray[900]'),
            '--tw-prose-th-borders': theme('colors.gray[300]'),
            '--tw-prose-td-borders': theme('colors.gray[200]'),
            
            // Dark mode variables
            '--tw-prose-invert-body': theme('colors.white'),
            '--tw-prose-invert-headings': theme('colors.white'),
            '--tw-prose-invert-links': theme('colors.teal[400]'),
            '--tw-prose-invert-bold': theme('colors.white'),
            '--tw-prose-invert-counters': theme('colors.gray[400]'),
            '--tw-prose-invert-bullets': theme('colors.gray[600]'),
            '--tw-prose-invert-hr': theme('colors.gray[700]'),
            '--tw-prose-invert-quotes': theme('colors.gray[100]'),
            '--tw-prose-invert-quote-borders': theme('colors.gray[700]'),
            '--tw-prose-invert-captions': theme('colors.gray[400]'),
            '--tw-prose-invert-code': theme('colors.white'),
            '--tw-prose-invert-th-borders': theme('colors.gray[600]'),
            '--tw-prose-invert-td-borders': theme('colors.gray[700]'),
            
            // Base typography
            fontFamily: '"Inter", sans-serif',
            color: 'var(--tw-prose-body)',
            lineHeight: '1.6',
            
            // Headings
            h1: {
              fontFamily: '"Playfair Display", serif',
              fontWeight: '700',
              letterSpacing: '-0.02em',
              fontSize: '2rem',
              lineHeight: '1.2',
              marginTop: '2.5rem',
              marginBottom: '1rem',
            },
            h2: {
              fontFamily: '"Playfair Display", serif',
              fontWeight: '600',
              letterSpacing: '-0.01em',
              fontSize: '1.5rem',
              lineHeight: '1.3',
              marginTop: '2rem',
              marginBottom: '0.75rem',
            },
            h3: {
              fontFamily: '"Playfair Display", serif',
              fontWeight: '600',
              fontSize: '1.25rem',
              lineHeight: '1.4',
              marginTop: '1.5rem',
              marginBottom: '0.5rem',
            },
            
            // Content
            p: {
              marginTop: '1rem',
              marginBottom: '1rem',
            },
            li: {
              marginTop: '1rem',
              marginBottom: '1rem',
            },
            strong: {
              fontFamily: '"Inter", sans-serif',
              fontWeight: '600',
            },
            blockquote: {
              fontFamily: '"Inter", sans-serif',
              fontStyle: 'italic',
              marginTop: '2rem',
              marginBottom: '2rem',
              marginLeft: '2rem',
              paddingLeft: '2rem',
              position: 'relative',
              color: 'var(--tw-prose-quotes)',
              borderLeft: 'none',
              fontSize: '1.125rem',
              lineHeight: '1.7',
              '&::before': {
                content: '"""',
                position: 'absolute',
                left: '-2rem',
                top: '0',
                fontSize: '6rem',
                lineHeight: '0.8',
                fontFamily: '"Playfair Display", serif',
                fontWeight: '400',
                color: 'var(--tw-prose-links)',
                opacity: '0.4',
              },
            },
            code: {
              fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            },
          },
        },
        
        // Large prose variant
        lg: {
          css: {
            fontSize: '1.125rem',
            h1: {
              fontFamily: '"Playfair Display", serif',
              fontSize: '2.5rem',
              lineHeight: '1.1',
            },
            h2: {
              fontFamily: '"Playfair Display", serif',
              fontSize: '2rem',
              lineHeight: '1.2',
            },
            h3: {
              fontFamily: '"Playfair Display", serif',
              fontSize: '1.5rem',
              lineHeight: '1.3',
            },
          },
        },
        

      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
  safelist: [
    // Only include specific notebook classes we actually use
    'notebook-content', 'notebook-cell', 'notebook-input', 'notebook-output',
    'notebook-error', 'markdown-cell', 'prose-main', 'prose-bio',
    // Prose classes
    {
      pattern: /^prose/,
      variants: ['dark'],
    },
    // Background colors
    {
      pattern: /^bg-/,
      variants: ['dark'],
    },
    // Border colors
    {
      pattern: /^border-/,
      variants: ['dark'],
    },
    // Text colors
    {
      pattern: /^text-/,
      variants: ['dark'],
    },
  ],
}