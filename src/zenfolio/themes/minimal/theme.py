"""Zen Minimal theme: a lightweight academic design with inline templates.

File templates in templates/ take priority; the inline template strings
below are fallbacks for components without a file equivalent.
"""

from datetime import datetime

from ..base_theme import BaseTheme
from ...utils import get_theme_directory

class MinimalTheme(BaseTheme):
    """Minimal academic theme with file-based templates and inline fallbacks."""

    def _register_templates(self):
        """Register component templates - file-based with inline fallbacks"""
        file_templates = self.register_file_templates()

        # Then register inline templates for components not covered by files
        inline_templates = {
            # Core layout components
            'navbar': self.NAVBAR_TEMPLATE,
            'footer': self.FOOTER_TEMPLATE,
            'page_layout': self.PAGE_LAYOUT_TEMPLATE,
            'landing_page': self.LANDING_PAGE_TEMPLATE,
            'profile_hero': self.PROFILE_HERO_TEMPLATE,
            'group_hero': self.GROUP_HERO_TEMPLATE,
            'section': self.SECTION_TEMPLATE,
            'divider': self.DIVIDER_TEMPLATE,

            # Item templates
            'publication_item': self.PUBLICATION_ITEM_TEMPLATE,
            'project_item': self.PROJECT_ITEM_TEMPLATE,
            'news_item': self.NEWS_ITEM_TEMPLATE,
            'talk_item': self.TALK_ITEM_TEMPLATE,
            'blog_post_item': self.BLOG_POST_ITEM_TEMPLATE,
            'service_item': self.SERVICE_ITEM_TEMPLATE,
            'person_item': self.PERSON_ITEM_TEMPLATE,
            'research_area_item': self.RESEARCH_AREA_ITEM_TEMPLATE,

            # Page templates
            'blog_post_page': self.BLOG_POST_PAGE_TEMPLATE,
            'page': self.PAGE_TEMPLATE,
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
        self.set_render_context(base_url)

        if self._compiled_base_layout is None:
            self._compiled_base_layout = self.env.from_string(
                self.BASE_LAYOUT_TEMPLATE
            )
        template = self._compiled_base_layout
        # The layout hardcodes include_navbar=True; drop a caller-supplied
        # value rather than raising a duplicate-keyword TypeError.
        context.pop('include_navbar', None)
        # built_pages will be available in context
        navbar_html = self.render_component('navbar', author_name=author_name, base_url=base_url, **context)
        footer_html = self.render_component(
            'footer',
            author_name=author_name,
            identity=context.get('identity'),
            current_year=datetime.now().year,
        )
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
    <link rel="stylesheet" href="{{ asset('style.css') }}">
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
    
    <script src="{{ asset('theme.js') }}"></script>
</body>
</html>"""



    # Navigation with dynamic menu items
    NAVBAR_TEMPLATE = """<header class="site-header">
    <nav class="nav-container">
        <a href="{{ url_for('/') }}" class="nav-home">{{ identity.name }}</a>
        <ul class="nav-links">
            {% for item in navigation if item.visible %}
            <li><a href="{{ url_for(item.route) }}" class="nav-link {% if current_page == item.key %}active{% endif %}" {% if item.external %}target="_blank" rel="noopener"{% endif %}>{{ item.label }}</a></li>
            {% endfor %}
        </ul>
    </nav>
</header>"""

    FOOTER_TEMPLATE = """<footer class="site-footer-main">
    <p>© {{ current_year }} {{ author_name }}. All rights reserved.</p>
</footer>"""





    PUBLICATION_ITEM_TEMPLATE = """<article class="card publication-card reveal-on-scroll">
    <h3 class="card-title">{{ item.title }}</h3>
    <p class="card-meta pub-authors">{{ item.highlighted_authors | safe }}</p>
    <p class="card-meta pub-venue">{{ item.venue }}, {{ item.year }}</p>
    <div class="card-links">
    {% if item.links %}
        {% for link in item.links %}
        <a href="{{ link.url }}" class="pub-link">{{ link.label }}</a>
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
    <h3 class="card-title"><a href="{{ url_for(item.route) }}">{{ item.title }}</a></h3>
    {% if item.excerpt %}
    <p class="card-content">{{ item.excerpt | safe }}</p>
    {% endif %}
    <a href="{{ url_for(item.route) }}" class="read-more">Read more <i class="fas fa-arrow-right"></i></a>
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
        {% if research_areas %}
        <section>
            <h2>Research directions</h2>
            <div class="grid-3">{% for area in research_areas %}{{ area.rendered_html | safe }}{% endfor %}</div>
        </section>
        {% endif %}
        {% if related_publications %}
        <section>
            <h2>Related publications</h2>
            <div class="list-container">{% for publication in related_publications %}{{ publication.rendered_html | safe }}{% endfor %}</div>
        </section>
        {% endif %}
        {% if related_projects %}
        <section>
            <h2>Public projects</h2>
            <div class="grid-2">{% for project in related_projects %}{{ project.rendered_html | safe }}{% endfor %}</div>
        </section>
        {% endif %}
</article>"""







    PAGE_LAYOUT_TEMPLATE = """<div class="container">
    <header class="page-header">
        <h1>{{ title }}</h1>
    </header>
    {% if intro %}<div class="page-intro">{{ intro | safe }}</div>{% endif %}
    
    {% if has_search %}
        {{ theme.render_component('search_filter_bar') }}
    {% endif %}
    
    {% if grouped_items %}
    <div class="grouped-content">
        {% for group in grouped_items %}
        <section class="group-section">
            <h2 class="year-heading">{{ group.get('title', group.get('group_name', '')) }}</h2>
            <div class="{% if layout == 'team' %}grid-3{% else %}list-container{% endif %}">
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

    LANDING_PAGE_TEMPLATE = """{{ theme.render_component(hero_component|default('profile_hero'), item=hero) }}
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
                    {% if item.actions|default([]) %}
                    {% for action in item.actions %}
                    {% set action_url = action.route if action.route is defined else action.url %}
                    {% set action_label = action.label if action.label is defined else action.text %}
                    <a href="{{ url_for(action_url) }}" class="{% if action.style == 'primary' %}primary-button{% else %}secondary-button{% endif %}">{{ action_label }}</a>
                    {% endfor %}
                    {% else %}
                    <a href="{{ url_for(item.publications_route|default('/publications.html')) }}" class="primary-button">View Publications</a>
                    <a href="mailto:{{ item.email }}" class="secondary-button">Get in Touch</a>
                    {% endif %}
                    {% if item.cv_path %}<a href="{{ item.cv_path }}" target="_blank" rel="noopener" class="primary-button">Download CV</a>{% endif %}
                </div>
            </div>
            {% if item.photo_path %}
            <div class="hero-photo">
                <img src="{{ asset(item.photo_path) }}" alt="{{ item.name }}" class="photo">
            </div>
            {% endif %}
        </div>
    </div>
</section>"""

    GROUP_HERO_TEMPLATE = """<section class="hero-section group-hero">
    <div class="container">
        {% if item.eyebrow %}<p class="hero-eyebrow">{{ item.eyebrow }}</p>{% endif %}
        <h1>{{ item.name }}</h1>
        {% if item.tagline %}<p class="hero-tagline">{{ item.tagline }}</p>{% endif %}
        {% if item.description %}<p>{{ item.description }}</p>{% endif %}
        {% if item.actions|default([]) %}
        <div class="hero-actions">
            {% for action in item.actions %}<a href="{{ url_for(action.route) }}" class="{% if action.style == 'primary' %}primary-button{% else %}secondary-button{% endif %}">{{ action.label }}</a>{% endfor %}
        </div>
        {% endif %}
        {% if item.hero_media and item.hero_media_approved %}
        <figure>
            <img src="{{ asset(item.hero_media) }}" alt="{{ item.hero_media_alt }}">
            {% if item.hero_media_caption %}<figcaption>{{ item.hero_media_caption }}</figcaption>{% endif %}
        </figure>
        {% endif %}
    </div>
</section>"""

    PERSON_ITEM_TEMPLATE = """<article class="card person-card">
    {% if item.photo %}<img src="{{ asset(item.photo) }}" alt="{{ item.photo_alt or item.name }}">{% endif %}
    <h3>{{ item.name }}</h3>
    {% if item.role %}<p class="card-meta">{{ item.role }}</p>{% endif %}
    {% if item.bio %}<div class="card-content">{{ item.bio | safe }}</div>{% endif %}
    {% if item.profile %}<a href="{{ item.profile }}">Profile →</a>{% endif %}
</article>"""

    RESEARCH_AREA_ITEM_TEMPLATE = """<article class="card research-area-card">
    {% if item.image %}<img src="{{ asset(item.image) }}" alt="{{ item.image_alt }}">{% endif %}
    <h3>{{ item.title }}</h3>
    <div class="card-content">{{ item.description | safe }}</div>
    {% if item.tags %}<p class="card-meta">{{ item.tags | join(' · ') }}</p>{% endif %}
</article>"""

    SECTION_TEMPLATE = """<section id="{{ section_id }}" data-section="{{ section_id }}" class="content-section{% if background|default(false) %} content-section-alt{% endif %}">
    <div class="container">
        <header class="section-header">
            <h2>{{ title }}</h2>
            {% if subtitle|default('') %}<p class="section-subtitle">{{ subtitle }}</p>{% endif %}
        </header>
        {% if content|default('') %}
        <div class="bio-content">{{ content | safe }}</div>
        {% endif %}
        {% if layout|default('grid') == 'bio' %}
        {% if interests|default([]) %}
        <div class="interests-section">
            <h3>Research Interests</h3>
            <div class="interests-list">
                {% for interest in interests %}<span class="interest-tag">{{ interest }}</span>{% endfor %}
            </div>
        </div>
        {% endif %}
        {% elif layout|default('grid') == 'service' %}
        <div class="service-list">
            {% for item in items.leadership_items|default([]) %}{{ item.rendered_html | safe }}{% endfor %}
            {% for role, role_items in (items.review_groups|default({})).items() %}
            <h3 class="service-section-title">{{ role }}</h3>
            {% for item in role_items %}{{ item.rendered_html | safe }}{% endfor %}
            {% endfor %}
        </div>
        {% elif steps|default([]) %}
        <div class="{% if grid_cols|default(1) == 2 %}grid-2{% elif grid_cols|default(1) >= 3 %}grid-3{% else %}list-container{% endif %}">
            {% for step in steps %}
            <article class="card">
                <h3>{{ step.title }}</h3>
                {% if step.description %}<p>{{ step.description }}</p>{% endif %}
            </article>
            {% endfor %}
        </div>
        {% elif layout|default('grid') == 'timeline' %}
        <div class="timeline-container">
            {% for item in items|default([]) %}{{ item.rendered_html | safe }}{% endfor %}
        </div>
        {% else %}
        <div class="{% if grid_cols|default(1) == 2 %}grid-2{% elif grid_cols|default(1) >= 3 %}grid-3{% else %}list-container{% endif %}">
            {% for item in items|default([]) %}{{ item.rendered_html | safe }}{% endfor %}
        </div>
        {% endif %}
        {% if actions|default([]) %}
        <div class="section-footer">
            {% for action in actions %}<a href="{{ url_for(action.route) }}">{{ action.label }} →</a>{% endfor %}
        </div>
        {% endif %}
        {% if view_all_link|default(false) %}
        <div class="section-footer">
            <a href="{{ url_for(view_all_link.url) }}" class="view-all-link">{{ view_all_link.text }} →</a>
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

    # CSS is now external - see css/theme.css
