"""
Zen Minimal Theme for ZenFolio - World-Class Academic Design
v3.0 - Refined Typography, Enhanced Visual Impact, Professional Polish
"""

from pathlib import Path
from ..base_theme import BaseTheme
from ...utils import get_theme_directory

class MinimalTheme(BaseTheme):
    """World-class zen minimal academic theme with sophisticated aesthetics"""
    

    
    def _register_templates(self):
        """Register component templates - file-based with inline fallbacks"""
        # First, load any file-based templates (these take priority)
        file_templates = set()
        if self.template_dir.exists():
            for template_path in self.template_dir.glob("*.html.j2"):
                component_name = template_path.stem.replace(".html", "")
                try:
                    self.env.globals[component_name] = self.env.get_template(template_path.name)
                    file_templates.add(component_name)
                    if self.debug:
                        print(f"✅ Loaded file template: {component_name}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Failed to load template '{component_name}': {e}")
        
        # Then register inline templates for components not covered by files
        inline_templates = {
            # Core layout components
            'navbar': self.NAVBAR_TEMPLATE,
            'footer': self.FOOTER_TEMPLATE,
            'page_layout': self.PAGE_LAYOUT_TEMPLATE,
            'landing_page': self.LANDING_PAGE_TEMPLATE,
            'profile_hero': self.PROFILE_HERO_TEMPLATE,
            'bio_section': self.BIO_SECTION_TEMPLATE,
            'section': self.SECTION_TEMPLATE,
            'divider': self.DIVIDER_TEMPLATE,
            
            # Item templates
            'publication_item': self.PUBLICATION_ITEM_TEMPLATE,
            'project_item': self.PROJECT_ITEM_TEMPLATE,
            'news_item': self.NEWS_ITEM_TEMPLATE,
            'talk_item': self.TALK_ITEM_TEMPLATE,
            'blog_post_item': self.BLOG_POST_ITEM_TEMPLATE,
            'service_item': self.SERVICE_ITEM_TEMPLATE,
            
            # Page templates
            'blog_post_page': self.BLOG_POST_PAGE_TEMPLATE,
            'page': self.PAGE_TEMPLATE,
            
            # Enhanced service templates
            'service_section': self.SERVICE_SECTION_TEMPLATE,
            'service_section_header': self.SERVICE_SECTION_HEADER_TEMPLATE,
            'service_group': self.SERVICE_GROUP_TEMPLATE,
        }
        
        # Only register inline templates that don't have file equivalents
        for name, template in inline_templates.items():
            if name not in file_templates:
                self.env.globals[name] = self.env.from_string(template)
    

    
    def __init__(self, debug=False):
        self.template_dir = get_theme_directory(__file__) / "templates"
        super().__init__(template_dir=self.template_dir, debug=debug)
    
    def render_page(self, content: str, page_title: str = "", author_name: str = "",
                    site_description: str = "", base_url: str = "", **context) -> str:
        """Override base render_page to handle SEO and built_pages context"""
        # Make base_url available to the url_for and file global functions
        self.env.globals['base_url'] = base_url
        
        template = self.env.from_string(self.BASE_LAYOUT_TEMPLATE)
        # built_pages will be available in context
        navbar_html = self.render_component('navbar', author_name=author_name, base_url=base_url, **context)
        from datetime import datetime
        footer_html = self.render_component('footer', author_name=author_name, current_year=datetime.now().year)
        seo_head_html = self.render_component('seo_head', page_title=page_title, author_name=author_name, site_description=site_description, **context)
        # Render MathJax configuration if provided
        mathjax_config = context.get('mathjax_config')
        mathjax_html = self.render_component('mathjax', mathjax_config=mathjax_config) if mathjax_config else ""
        
        return template.render(
            content=content, page_title=page_title, author_name=author_name,
            site_description=site_description, base_url=base_url,
            navbar=navbar_html, footer=footer_html, seo_head=seo_head_html, mathjax_html=mathjax_html,
            include_navbar=True, **context
        )

    def write_css_file(self, output_dir):
        """Copy external CSS and JS files"""
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        # Copy the theme CSS file
        theme_css_path = get_theme_directory(__file__) / "css" / "theme.css"
        output_css_path = static_dir / "style.css"
        
        if theme_css_path.exists():
            import shutil
            shutil.copy2(theme_css_path, output_css_path)
        else:
            # Fallback: write basic CSS
            css_content = """/* Minimal theme styles - fallback */
body {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
    color: #333;
}
"""
            output_css_path.write_text(css_content)
        
        # Copy the theme JavaScript file  
        theme_js_path = get_theme_directory(__file__) / "js" / "theme.js"
        output_js_path = static_dir / "theme.js"
        
        if theme_js_path.exists():
            import shutil
            shutil.copy2(theme_js_path, output_js_path)
    


    # Unified Base Layout Template
    BASE_LAYOUT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if page_title %}{{ page_title }} · {% endif %}{{ author_name }}</title>
    <meta name="description" content="{% if meta_description %}{{ meta_description }}{% else %}{{ site_description }}{% endif %}">
    {% if seo_head %}{{ seo_head | safe }}{% endif %}
    {% if mathjax_html %}{{ mathjax_html | safe }}{% endif %}
    <link rel="stylesheet" href="{{ file('style.css') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    {% if include_navbar %}{{ navbar | safe }}{% endif %}
    
    <main>
        {{ content | safe }}
    </main>
    
    {% if include_navbar %}{{ footer | safe }}{% endif %}
    
    <script src="{{ file('theme.js') }}"></script>
</body>
</html>"""



    # Navigation with dynamic menu items
    NAVBAR_TEMPLATE = """<header class="site-header">
    <nav class="nav-container">
        <a href="{{ url_for('index.html') }}" class="nav-home">{{ author_name }}</a>
        <ul class="nav-links">
            {% for key, label in built_pages %}
            <li><a href="{{ url_for(key ~ '.html') }}" class="nav-link {% if current_page == key %}active{% endif %}">{{ label }}</a></li>
            {% endfor %}
        </ul>
    </nav>
</header>"""

    FOOTER_TEMPLATE = """<footer class="site-footer-main">
    <p>© {{ current_year }} {{ author_name }}. All rights reserved.</p>
</footer>"""





    PUBLICATION_ITEM_TEMPLATE = """<article class="card publication-card reveal-on-scroll">
    <h3 class="card-title">{{ item.title }}</h3>
    <p class="card-meta pub-authors">{{ item.authors | safe }}</p>
    <p class="card-meta pub-venue">{{ item.venue }}, {{ item.year }}</p>
    <div class="card-links">
    {% if item.links %}
        {% for link in item.links %}
        <a href="{{ link.url }}" class="pub-link">{{ link.label | safe }}</a>
        {% endfor %}
    {% endif %}
        <button class="cite-button" onclick="copyBibtex(this)" data-bibtex="{{ item.bibtex | e }}">
            <i class="fas fa-quote-left"></i> Cite
        </button>
    </div>
</article>"""



    NEWS_ITEM_TEMPLATE = """<article class="news-item reveal-on-scroll">
    <time class="news-date">{{ item.date }}</time>
    <div class="news-content">
        {{ item.content | safe }}
    <div class="news-links">
        {% if item.paper %}<a href="{{ item.paper }}" target="_blank" rel="noopener" class="news-link">Paper</a>{% endif %}
        {% if item.code %}<a href="{{ item.code }}" target="_blank" rel="noopener" class="news-link">Code</a>{% endif %}
        {% if item.website %}<a href="{{ item.website }}" target="_blank" rel="noopener" class="news-link">Website</a>{% endif %}
        {% if item.demo %}<a href="{{ item.demo }}" target="_blank" rel="noopener" class="news-link">Demo</a>{% endif %}
        {% if item.slides %}<a href="{{ item.slides }}" target="_blank" rel="noopener" class="news-link">Slides</a>{% endif %}
        {% if item.video %}<a href="{{ item.video }}" target="_blank" rel="noopener" class="news-link">Video</a>{% endif %}
    </div>
    </div>
</article>"""

    PROJECT_ITEM_TEMPLATE = """<article class="card project-card reveal-on-scroll">
    <h3 class="card-title">{{ item.title }}</h3>
    {% if item.category %}
    <div class="card-meta">
        <span class="category-tag">{{ item.category }}</span>
    </div>
    {% endif %}
    <div class="card-content">
        {{ item.description | safe }}
    </div>
    {% if item.collaborators %}
    <div class="card-meta">
        <strong>Collaborators:</strong> {{ item.collaborators | join(', ') }}
    </div>
    {% endif %}
    <div class="card-links">
        {% if item.github %}<a href="{{ item.github }}" target="_blank" rel="noopener" class="card-link">GitHub</a>{% endif %}
        {% if item.documentation %}<a href="{{ item.documentation }}" target="_blank" rel="noopener" class="card-link">Documentation</a>{% endif %}
        {% if item.paper %}<a href="{{ item.paper }}" target="_blank" rel="noopener" class="card-link">Paper</a>{% endif %}
        {% if item.website %}<a href="{{ item.website }}" target="_blank" rel="noopener" class="card-link">Website</a>{% endif %}
        {% if item.demo %}<a href="{{ item.demo }}" target="_blank" rel="noopener" class="card-link">Demo</a>{% endif %}
        {% if item.code %}<a href="{{ item.code }}" target="_blank" rel="noopener" class="card-link">Code</a>{% endif %}
    </div>
</article>"""



    TALK_ITEM_TEMPLATE = """<article class="card talk-card reveal-on-scroll">
    <h3 class="card-title">
        {{ item.title }}
        {% if item.type %}<span class="talk-type">{{ item.type }}</span>{% endif %}
    </h3>
    <p class="card-meta">
        {% if item.date %}<time>{{ item.date }}</time>{% endif %}
        {% if item.venue %} · <span class="talk-venue">{{ item.venue }}</span>{% endif %}
    </p>
    {% if item.description %}
    <div class="card-content">{{ item.description | safe }}</div>
    {% endif %}
    <div class="card-links">
        {% if item.slides %}<a href="{{ item.slides }}" target="_blank" rel="noopener" class="card-link">Slides</a>{% endif %}
        {% if item.video %}<a href="{{ item.video }}" target="_blank" rel="noopener" class="card-link">Video</a>{% endif %}
        {% if item.code %}<a href="{{ item.code }}" target="_blank" rel="noopener" class="card-link">Code</a>{% endif %}
        {% if item.materials %}<a href="{{ item.materials }}" target="_blank" rel="noopener" class="card-link">Materials</a>{% endif %}
        {% if item.demo %}<a href="{{ item.demo }}" target="_blank" rel="noopener" class="card-link">Demo</a>{% endif %}
    </div>
</article>"""

    BLOG_POST_ITEM_TEMPLATE = """<article class="card blog-preview reveal-on-scroll">
    <time class="card-meta">{{ item.date }}</time>
    <h3 class="card-title"><a href="{{ url_for('blog/' ~ item.slug ~ '.html') }}">{{ item.title }}</a></h3>
    {% if item.excerpt %}
    <p class="card-content">{{ item.excerpt }}</p>
    {% endif %}
    <a href="{{ url_for('blog/' ~ item.slug ~ '.html') }}" class="read-more">Read more <i class="fas fa-arrow-right"></i></a>
</article>"""

    BLOG_POST_PAGE_TEMPLATE = """<article class="blog-post">
    <header class="post-header">
        <h1>{{ item.title }}</h1>
        <time class="post-date">{{ item.date }}</time>
    </header>
    <div class="post-content">
        {{ item.content | safe }}
    </div>
</article>"""





    PAGE_TEMPLATE = """<article class="page-content">
        {{ item.content | safe }}
</article>"""







    SEARCH_FILTER_BAR_TEMPLATE = """<div class="search-controls">
    <div class="search-box">
        <input type="text" id="search-input" placeholder="Search publications..." class="search-input">
    </div>
</div>"""

    PAGE_LAYOUT_TEMPLATE = """<div class="container">
    <header class="page-header">
        <h1>{{ title }}</h1>
    </header>
    
    {% if has_search %}
        {{ theme.render_component('search_filter_bar') }}
    {% endif %}
    
    {% if grouped_items %}
    <div class="grouped-content">
        {% for group in grouped_items %}
        <section class="group-section">
            <h2 class="year-heading">{{ group.group_name }}</h2>
            <div class="list-container">
                {% for item in group['items'] %}
                    {{ theme.render_component(item.template_type, item=item) }}
                {% endfor %}
            </div>
        </section>
        {% endfor %}
    </div>
    {% elif layout == 'timeline' %}
    <div class="timeline-container">
        {{ items_html | safe }}
    </div>
    {% else %}
    <div class="{% if columns == 2 %}grid-2{% elif columns >= 3 %}grid-3{% else %}list-container{% endif %}">
        {{ items_html | safe }}
    </div>
    {% endif %}
</div>"""

    LANDING_PAGE_TEMPLATE = """{{ theme.render_component('profile_hero', item=hero) }}
{{ theme.render_component('bio_section', bio_content=bio_content, interests=hero.interests) }}
{{ theme.render_component('divider') }}
{% for section in sections %}
    {% if not loop.first %}
        {{ theme.render_component('divider') }}
    {% endif %}
    {{ section.rendered_html | safe }}
{% endfor %}"""

    PROFILE_HERO_TEMPLATE = """<section class="hero-section">
    <div class="container">
        <div class="hero-content">
            <div class="hero-text">
                <h1>{{ item.name }}</h1>
                {% if item.tagline %}<p class="hero-tagline">{{ item.tagline }}</p>{% endif %}
                <div class="hero-actions">
                    <a href="publications.html" class="primary-button">View Publications</a>
                    <a href="mailto:{{ item.email }}" class="secondary-button">Get in Touch</a>
                    {% if item.cv_path %}<a href="{{ item.cv_path }}" target="_blank" rel="noopener" class="primary-button">Download CV</a>{% endif %}
                </div>
            </div>
            {% if item.photo_path %}
            <div class="hero-photo">
                <img src="static/{{ item.photo_path }}" alt="{{ item.name }}" class="photo">
            </div>
            {% endif %}
        </div>
    </div>
</section>"""

    BIO_SECTION_TEMPLATE = """<section class="bio-section">
    <div class="container">
        <h2>About Me</h2>
        <div class="bio-content">
            {{ bio_content | safe }}
        </div>
        {% if interests %}
        <div class="interests-section">
            <h3>Research Interests</h3>
            <div class="interests-list">
                {% for interest in interests %}
                <span class="interest-tag">{{ interest }}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</section>"""

    SECTION_TEMPLATE = """<section class="content-section">
    <div class="container">
        <header class="section-header">
            <h2>{{ title }}</h2>
            {% if subtitle|default('') %}<p class="section-subtitle">{{ subtitle }}</p>{% endif %}
        </header>
        {% if layout|default('grid') == 'timeline' %}
        <div class="timeline-container">
            {% for item in items %}{{ theme.render_component(item.template_type, item=item) }}{% endfor %}
        </div>
        {% else %}
        <div class="{% if grid_cols == 2 %}grid-2{% elif grid_cols >= 3 %}grid-3{% else %}list-container{% endif %}">
            {% for item in items %}{{ theme.render_component(item.template_type, item=item) }}{% endfor %}
        </div>
        {% endif %}
        {% if view_all_link|default(false) %}
        <div class="section-footer">
            <a href="{{ view_all_link.url }}" class="view-all-link">{{ view_all_link.text }} →</a>
        </div>
        {% endif %}
    </div>
</section>"""

    DIVIDER_TEMPLATE = """<div class="divider"></div>"""

    SERVICE_ITEM_TEMPLATE = """<div class="service-item">
    <div class="service-content">
        <div class="service-title">
            {% if item.url %}<a href="{{ item.url }}" target="_blank" rel="noopener" class="service-link">{{ item.description }}</a>{% else %}{{ item.description }}{% endif %}{% if item.venue %} · <em class="service-venue">{{ item.venue }}</em>{% endif %}
        </div>
        {% if item.subtitle %}<div class="service-subtitle">{{ item.subtitle }}</div>{% endif %}
    </div>
    <span class="service-date">{{ item.date }}</span>
</div>"""

    SERVICE_SECTION_TEMPLATE = """<section class="content-section service-section">
    <div class="container">
        <header class="section-header">
            <h2>{{ title }}</h2>
            {% if subtitle is defined and subtitle %}<p class="section-subtitle">{{ subtitle }}</p>{% endif %}
        </header>
        
        {# Check if items is structured (new format) or list (old format) #}
        {% if items.leadership_items is defined %}
        
        {# New structured format - Leadership & Editorial Section #}
        {% if items.leadership_items %}
        <h3 class="service-section-title">Leadership & Editorial</h3>
        {% for item in items.leadership_items %}
        <div class="service-item leadership-item">
            <div class="service-content">
                <div class="service-title">
                    {% if item.url %}<a href="{{ item.url }}" target="_blank" rel="noopener" class="service-link">{{ item.description }}</a>{% else %}{{ item.description }}{% endif %}{% if item.venue %} · <em class="service-venue">{{ item.venue }}</em>{% endif %}
                </div>
                {% if item.subtitle %}<div class="service-subtitle">{{ item.subtitle }}</div>{% endif %}
            </div>
            <span class="service-date">{{ item.date }}</span>
        </div>
        {% endfor %}
        {% endif %}
        
        {# Peer Review Section #}
        {% if items.review_groups %}
        <h3 class="service-section-title">Peer Review</h3>
        
        {# Render each role group #}
        {% for role, role_items in items.review_groups.items() %}
        <div class="service-group">
            <div class="service-group-header">
                <span class="service-role">{{ role }}:</span>
                <div class="service-tags">
                    {% for item in role_items %}
                    <span class="service-tag{% if item.highlight %} service-tag-highlight{% endif %}">
                        <span class="service-venue">{{ item.venue }}</span>
                        {% if item.highlight %}<span class="service-highlight">{{ item.highlight|title }}</span>{% endif %}
                        <span class="service-date">{{ item.date }}</span>
                    </span>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
        {% endif %}
        
        {% else %}
        
        {# Fallback to simple list format #}
        <div class="service-list">
            {% for item in items %}
            <div class="service-item">
                <div class="service-content">
                    <div class="service-title">
                        {% if item.url %}<a href="{{ item.url }}" target="_blank" rel="noopener" class="service-link">{{ item.description }}</a>{% else %}{{ item.description }}{% endif %}{% if item.venue %} · <em class="service-venue">{{ item.venue }}</em>{% endif %}
                    </div>
                    {% if item.subtitle %}<div class="service-subtitle">{{ item.subtitle }}</div>{% endif %}
                </div>
                <span class="service-date">{{ item.date }}</span>
            </div>
            {% endfor %}
        </div>
        
        {% endif %}
    </div>
</section>"""

    SERVICE_SECTION_HEADER_TEMPLATE = """<h3 class="service-section-title">{{ title }}</h3>"""

    SERVICE_GROUP_TEMPLATE = """<div class="service-group">
    <div class="service-group-header">
        <span class="service-role">{{ title }}:</span>
        <div class="service-tags">
            {% for venue in venues %}
            <span class="service-tag{% if venue.highlight %} service-tag-highlight{% endif %}">
                <span class="service-venue">{{ venue.venue }}</span>
                {% if venue.highlight %}<span class="service-highlight">{{ venue.highlight|title }}</span>{% endif %}
                <span class="service-date">{{ venue.date }}</span>
            </span>
            {% endfor %}
        </div>
    </div>
</div>"""

    SEO_HEAD_TEMPLATE = """<!-- Enhanced SEO Meta Tags -->
{% if canonical_url is defined and canonical_url %}<link rel="canonical" href="{{ canonical_url }}">{% endif %}
<meta property="og:title" content="{% if page_title %}{{ page_title }} · {% endif %}{{ author_name }}">
<meta property="og:description" content="{% if meta_description is defined and meta_description %}{{ meta_description }}{% else %}{{ site_description }}{% endif %}">
<meta property="og:type" content="website">
{% if canonical_url is defined and canonical_url %}<meta property="og:url" content="{{ canonical_url }}">{% endif %}
{% if og_image is defined and og_image %}<meta property="og:image" content="{{ og_image }}">{% endif %}
<meta name="twitter:card" content="{{ site_seo.twitter_card_type }}">
<meta name="twitter:title" content="{% if page_title %}{{ page_title }} · {% endif %}{{ author_name }}">
<meta name="twitter:description" content="{% if meta_description is defined and meta_description %}{{ meta_description }}{% else %}{{ site_description }}{% endif %}">
{% if canonical_url is defined and canonical_url %}<meta name="twitter:url" content="{{ canonical_url }}">{% endif %}
{% if og_image is defined and og_image %}<meta name="twitter:image" content="{{ og_image }}">{% endif %}
{% if author and author.twitter %}
<meta name="twitter:creator" content="@{{ author.twitter.split('/')[-1] }}">
{% endif %}
{% if structured_data is defined and structured_data %}
<script type="application/ld+json">
{{ structured_data | safe }}
</script>
{% endif %}"""

    # MathJax template component (parity with Tailwind)
    MATHJAX_TEMPLATE = """<!-- MathJax for LaTeX math rendering -->
{% if mathjax_config.version == "2" %}
    <!-- MathJax v2 Configuration -->
    <script type="text/x-mathjax-config">
        MathJax.Hub.Config({
            tex2jax: {
                inlineMath: {{ mathjax_config.inline_math | tojson }},
                displayMath: {{ mathjax_config.display_math | tojson }},
                processEscapes: {{ mathjax_config.process_escapes | lower }},
                processEnvironments: {{ mathjax_config.process_environments | lower }},
                skipTags: {{ mathjax_config.skip_html_tags | tojson }},
                ignoreClass: "{{ mathjax_config.ignore_html_class }}",
                processClass: "{{ mathjax_config.process_html_class }}"
            },
            TeX: {
                extensions: {{ mathjax_config.extensions | tojson }}
            }
        });
    </script>
    <script src="{% if mathjax_config.cdn_url %}{{ mathjax_config.cdn_url }}{% else %}https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML{% endif %}"></script>
{% else %}
    <!-- MathJax v3 Configuration -->
    <script>
        MathJax = {
            tex: {
                inlineMath: {{ mathjax_config.inline_math | tojson }},
                displayMath: {{ mathjax_config.display_math | tojson }},
                processEscapes: {{ mathjax_config.process_escapes | lower }},
                processEnvironments: {{ mathjax_config.process_environments | lower }},
                packages: {{ mathjax_config.extensions | tojson }}
            },
            options: {
                skipHtmlTags: {{ mathjax_config.skip_html_tags | tojson }},
                ignoreHtmlClass: '{{ mathjax_config.ignore_html_class }}',
                processHtmlClass: '{{ mathjax_config.process_html_class }}'
            }
        };
    </script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="{% if mathjax_config.cdn_url %}{{ mathjax_config.cdn_url }}{% else %}https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js{% endif %}"></script>
{% endif %}"""

    # CSS is now external - see css/theme.css
