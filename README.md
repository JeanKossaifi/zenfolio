# ZenFolio 🧘‍♂️📚

A minimal, powerful academic website generator built with [ZenCFG](https://github.com/JeanKossaifi/zencfg).

## ✨ Features

- **🎨 Beautiful Themes**: Modern, responsive designs with Tailwind CSS and Minimal themes
- **📓 Jupyter Notebook Support**: Native rendering of `.ipynb` files with enhanced styling
- **🧠 Smart Path Handling**: No complex APIs - just use strings! Auto-detects URLs vs local files
- **🚀 Production-Ready Deployment**: Auto base URL detection, GitHub Pages integration, SEO optimization
- **🔧 Advanced SEO**: Comprehensive meta tags, Open Graph, Twitter Cards, JSON-LD structured data
- **📐 MathJax Integration**: Configurable LaTeX math rendering (v2/v3 support)
- **📝 Rich Markdown Support**: Customizable extensions (code blocks, tables, admonitions, etc.)
- **📊 Academic-Focused**: Publications (BibTeX), projects, news, talks, academic service
- **⚡ Type-Safe Configuration**: Built on ZenCFG for robust, validated configuration
- **🔗 Flexible Content Management**: Write in Markdown, manage data in Python
- **🏗️ Robust Build System**: Development/production modes, validation, error handling

## Quick Start

### Installation

```bash
pip install zenfolio
```

### Initialize a New Site

```bash
zenfolio init --content-dir my-site
```

This creates:
- `config.py` - Site configuration (name, affiliation, social links)
- `content.py` - Your content (news, projects, talks)
- `content/index.md` - Your bio and academic service
- `content/blog/` - Blog posts directory
- `static/` - Static assets (profile photo, etc.)
- `publications.bib` - Your publications in BibTeX format

### Build Your Site

```bash
# Development build (relative URLs)
zenfolio build --content-dir my-site --dev

# Production build (absolute URLs + deployment files)
zenfolio deploy --content-dir my-site

# Development server
zenfolio dev --content-dir my-site
```

### 🎯 It's That Simple!

ZenFolio's smart path system means you can focus on content, not configuration:

```python
# Just use strings - no complex path objects!
NewsItem(
    paper="https://arxiv.org/abs/2024.12345",  # External URL ✅
    slides="talks/my_slides.pdf",              # Local file ✅
    code="https://github.com/user/repo"        # GitHub URL ✅
)
```

Just put your local file in 
`my-site/_static/talks`.

## Configuration

### Site Configuration (`config.py`)

```python
from zenfolio.models import (
    Config, AuthorConfig, SiteConfig, SEOConfig, MathJaxConfig,
    PublicationConfig, HomepageButton
)

# Personal information
author_config = AuthorConfig(
    name="Your Name",
    title="Your Title", 
    affiliation="Your Institution",
    email="your.email@example.com",
    photo_path="profile.jpg",
    
    # Social links
    github="https://github.com/yourusername",
    scholar="https://scholar.google.com/citations?user=...",
    linkedin="https://linkedin.com/in/yourusername",
    twitter="https://twitter.com/yourusername",
    
    # Homepage buttons
    homepage_buttons=[
        HomepageButton(text="View Projects", url="projects.html", style="primary"),
        HomepageButton(text="View Publications", url="publications.html", style="secondary"),
    ],
    
    # Research interests (displayed as tags)
    interests=["AI", "Machine Learning", "Research Area"]
)

# Site settings
site_config = SiteConfig(
    title="Your Name | Academic Website",
    description="Your research focus and expertise...",
    base_url="https://yoursite.com",
    
    # Blog configuration
    blog_folder="blog",    # Default: look for posts in "blog/" directory
    # blog_folder="posts", # Custom: use "posts/" directory instead  
    # blog_folder=None,    # Disable: completely disable blog functionality
    
    # SEO configuration
    seo=SEOConfig(
        alumni_of="Your University",
        # Optional overrides...
    ),
    
    # MathJax for LaTeX rendering
    mathjax=MathJaxConfig(version="3"),
)

# Publication settings
publication_config = PublicationConfig(
    bib_path="publications.bib",
    highlight_author=["Your Name", "Y. Name"]  # Variations of your name
)

# Main configuration
config = Config(
    author=author_config,
    site=site_config,
    publications=publication_config
)
```

### Content Management

**News (`news.py`):**
```python
from zenfolio.models import NewsConfig, NewsItem

news_config = NewsConfig(items=[
    NewsItem(
        date="2024-01-15",
        content="Paper accepted at top conference!",
        highlight=True,  # Featured on homepage
        paper="https://arxiv.org/abs/...",
        slides="talks/presentation.pdf"
    )
])
```

**Projects (`projects.py`):**
```python
from zenfolio.models import ProjectsConfig, ProjectItem

projects_config = ProjectsConfig(items=[
    ProjectItem(
        title="My Research Project",
        description="Description of the project...",
        highlight=True,  # Featured on homepage
        github="https://github.com/username/project",
        paper="papers/project.pdf",
        demo="https://demo-site.com"
    )
])
```

## Path Handling

ZenFolio uses smart path detection to make managing files and links effortless. Simply use strings for all paths - no complex APIs to learn!

### How It Works

- **External URLs**: Detected automatically (starts with `http://`, `https://`, etc.)
- **Local Files**: Automatically resolved relative to your `static/` directory
- **Smart Context**: Images and links are handled appropriately for templates

### Examples

#### Author Configuration
```python
author = AuthorConfig(
    photo="profile.jpg",                    # 📸 Local file: static/profile.jpg
    cv="https://example.com/cv.pdf",        # 🌐 External URL: used as-is
    # OR use a local file:
    # cv="documents/cv.pdf",                # 📄 Local file: static/documents/cv.pdf
)
```

#### Content Items
```python
news_items = [
    NewsItem(
        content="New paper published!",
        paper="https://arxiv.org/abs/2024.12345",  # 🌐 External URL
        slides="talks/conference_slides.pdf",      # 📄 Local file in static/talks/
        code="https://github.com/user/project",    # 🌐 GitHub URL
    )
]

projects = [
    ProjectItem(
        title="Amazing Project",
        image="projects/screenshot.png",           # 📸 Local image in static/projects/
        github="https://github.com/user/repo",    # 🌐 GitHub URL
        paper="papers/project_paper.pdf",         # 📄 Local PDF in static/papers/
        demo="https://demo-site.com",             # 🌐 Live demo URL
    )
]
```

### File Organization

Organize your `static/` directory however makes sense for your content:

```
static/
├── profile.jpg              # Author photo
├── documents/
│   └── cv.pdf               # CV and documents
├── papers/
│   ├── paper1.pdf           # Research papers
│   └── supplementary.zip    # Additional materials
├── talks/
│   ├── slides-2024.pdf      # Presentation slides
│   └── handouts.pdf         # Talk materials
└── projects/
    ├── screenshot.png       # Project images
    └── demo.html           # Local demos
```

### Deployment Flexibility

The same paths work for both:
- **Local Development**: Relative URLs (`./static/file.pdf`)
- **Production**: Absolute URLs (`https://yoursite.com/static/file.pdf`)

### Supported Link Types

All content items support these optional link fields:
- `paper` - Research papers (PDF or external URL)
- `code` - Source code (GitHub, local files)
- `slides` - Presentation slides 
- `video` - Videos (YouTube, Vimeo, local files)
- `demo` - Live demos or interactive content
- `website` - Project websites
- `documentation` - Documentation links
- `materials` - Supplementary materials

## Smart Configuration

### 🎯 **Auto Base URL Detection**

ZenFolio automatically uses the right URLs for your deployment:

```python
# In config.py
site_config = SiteConfig(
    base_url="https://yoursite.com",  # Used automatically for production builds!
)
```

**Build Commands:**
```bash
zenfolio build                    # 🚀 Production: uses site.base_url (https://yoursite.com)
zenfolio build --dev              # 🔧 Development: uses relative URLs (./static/...)
zenfolio deploy                   # 🚀 Production: build + create .nojekyll + validate
zenfolio dev                      # 🔧 Development: build + serve with relative URLs
zenfolio serve                    # 📡 Serve existing build
zenfolio validate                 # ✅ Validate config and generated site
```

### ⚙️ **Configurable Markdown Extensions**

Customize markdown processing in your config:

```python
# In config.py
site_config = SiteConfig(
    # Customize which markdown extensions to use
    markdown_extensions=['fenced_code', 'codehilite', 'tables', 'admonition'],
    # Add more extensions like 'footnotes', 'toc', 'sane_lists', etc.
)
```

**Available Extensions:** Any [Python-Markdown extension](https://python-markdown.github.io/extensions/) including:
- `fenced_code` - GitHub-style code blocks
- `codehilite` - Syntax highlighting  
- `tables` - GitHub-style tables
- `admonition` - Note/warning boxes
- `footnotes` - Footnote support
- `toc` - Table of contents
- `sane_lists` - Better list handling

## 📊 Content Structure

- **🏠 Home Page**: Profile hero, bio, research interests, featured projects, recent publications, news
- **📄 Publications**: All publications grouped by year with search/filtering
- **🚀 Projects**: Research projects with links to code, demos, papers  
- **📰 News**: Updates, announcements, achievements with timeline layout
- **🎤 Talks**: Presentations, invited talks, keynotes
- **📝 Blog**: Personal blog posts, research notes, and Jupyter notebooks

## 🔧 Advanced Features

### 📓 Jupyter Notebook Support

ZenFolio natively renders Jupyter notebooks as blog posts:

```python
# In your blog directory
my_research.ipynb  # Automatically becomes a blog post!
```

Features:
- **Enhanced styling** with input/output cell differentiation
- **Frontmatter support** in first markdown cell
- **Image and video rendering** from notebook outputs
- **LaTeX math rendering** via MathJax
- **Clean HTML output** with anchor link removal

### 🔧 SEO & Meta Configuration

Advanced SEO with smart defaults:

```python
# In config.py
site_config = SiteConfig(
    seo=SEOConfig(
        # Essential (can't be auto-detected)
        alumni_of="Your University",
        
        # Optional overrides
        custom_knowledge_areas=["AI", "Machine Learning"],
        custom_publisher_name="Your Research Lab",
        custom_og_image="custom-social-image.jpg",
    )
)
```

Automatic generation of:
- **Open Graph** and **Twitter Card** meta tags
- **JSON-LD structured data** for Google Scholar
- **Canonical URLs** for SEO
- **Sitemap.xml** and **robots.txt**

### 📐 MathJax Configuration

Flexible LaTeX math rendering:

```python
# In config.py
site_config = SiteConfig(
    mathjax=MathJaxConfig(
        version="3",  # or "2"
        extensions=["TeX/AMSmath", "TeX/AMSsymbols"],
        # Custom CDN URL supported
    )
)
```

### 🎨 Theme System

**Tailwind Theme** (Default):
- Modern, responsive design
- Dark/light mode support
- Enhanced animations and interactions
- Beautiful typography and spacing

**Minimal Theme**:
- Clean, academic focus
- Lightweight and fast
- Easy to customize

### 🚀 Deployment & GitHub Actions

Built-in GitHub Actions workflow:

```yaml
# Automatically deploys to GitHub Pages
- name: Build Website
  run: python -m zenfolio deploy --content-dir . --theme tailwind --debug
```

Features:
- **Automatic deployment** to GitHub Pages
- **Build validation** with comprehensive checks
- **Static placeholder verification**
- **Custom domain support** (CNAME)
- **Artifact uploads** for debugging

## 🛠️ Customization

### Adding Content

1. **Bio**: Edit `index.md` in your content directory
2. **Publications**: Add entries to `publications.bib`
3. **News/Projects/Talks**: Edit respective `.py` files (`news.py`, `projects.py`, etc.)
4. **Blog Posts**: Add Markdown files or Jupyter notebooks to `blog/` directory
5. **Static Assets**: Place images, PDFs, etc. in `static/` directory

### Configuration Structure

```
my-site/
├── config.py           # Main site configuration
├── index.md           # Homepage bio content
├── publications.bib   # Academic publications
├── news.py           # News items and announcements
├── projects.py       # Research projects
├── service.py        # Academic service items
├── talks.py          # Presentations and talks
├── blog/             # Blog posts and notebooks
│   ├── post1.md
│   ├── research.ipynb
│   └── ...
└── static/           # Static assets
    ├── profile.jpg
    ├── images/
    ├── pdfs/
    └── ...
```

### Blog Features

**Markdown Posts:**
```markdown
---
title: "My Research Post"
date: "2024-01-15"
description: "A brief description"
image: "images/hero.jpg"  # Optional hero image
---

# Your content here...
```

**Jupyter Notebooks:**
- Add frontmatter in first markdown cell
- Automatic rendering of code, outputs, and visualizations
- Support for images, videos, and interactive content
- LaTeX math rendering

## 🔧 Development

### Installation from Source

```bash
git clone https://github.com/JeanKossaifi/zenfolio
cd zenfolio
pip install -e .
```

### Project Structure

```
zenfolio/
├── src/zenfolio/
│   ├── __init__.py
│   ├── zenfolio.py         # Main generator class
│   ├── cli.py              # Command line interface
│   ├── deploy.py           # Deployment utilities
│   ├── validators.py       # Site validation
│   ├── models/             # Configuration models
│   ├── parsers/            # Content parsers (Markdown, BibTeX, Jupyter)
│   ├── themes/             # Theme system (Minimal, Tailwind)
│   ├── templates/          # CLI init templates
│   └── utils.py            # Utility functions
├── setup.py
└── README.md
```

### Development Commands

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Build CSS assets (for Tailwind theme)
cd src/zenfolio/themes/tailwind
npm install
npm run build

# Development workflow
zenfolio dev --content-dir example-site
```

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [ZenCFG](https://github.com/JeanKossaifi/zencfg) for type-safe configuration
- Inspired by academic website generators like Jekyll Academic and Hugo Academic 