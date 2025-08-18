"""
ZenFolio - Core generator class for academic websites
v3.4 - Corrected logic to ensure bio section is included on homepage.
"""

import shutil
import markdown
import textwrap
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .content import Content
from .parsers import parser_registry
from .themes import TailwindTheme, MinimalTheme
from .seo_utils import SEOGenerator
from .utils import resolve_directory_path, is_external_url, build_url
from zencfg import load_config_from_file

class ZenFolio:
    """ZenFolio - minimal and powerful academic website generator"""
    
    def __init__(self, content_dir: Path = Path("."), theme_override: str = None, debug: bool = False):
        self.content_dir = content_dir
        self.debug = debug
        
        # Load user config directly - ZenCFG handles validation
        self.config = load_config_from_file(self.content_dir / "config.py", "config")
        
        # Apply theme override if provided (before loading theme)
        if theme_override:
            self.config.theme = theme_override
        
        # Resolve paths using shared utilities
        self.static_dir = resolve_directory_path(self.config.static_path, self.content_dir)
        self.output_dir = resolve_directory_path(self.config.output_path, self.content_dir.parent)
        self.theme = self._load_theme(debug=debug)
        self.parser_registry = parser_registry
        
        # Initialize content loader
        self.content = Content(content_dir, self.config, debug)

        # Initialize SEO utilities and sitemap tracking
        self.seo_pages = []  # Track pages for sitemap generation
    

    
    def _resolve_path(self, path: str) -> str:
        """Resolve any path - external URLs as-is, local paths as clean filenames"""
        if is_external_url(path):
            return path  # External URL - use as-is
        else:
            # Local file - return clean filename, let templates handle URL generation
            return path.removeprefix('static/')
    
    def _process_static_placeholders(self, content: str, base_url: str = "") -> str:
        """Process {static} placeholders and relative image paths in content"""
        import re
        
        # First handle {static} placeholders
        if '{static}' in content:
            static_url = build_url(base_url, 'static')
            content = content.replace('{static}', static_url)
        
        # Handle relative image paths (images/filename.ext -> ../static/images/filename.ext)
        # This regex matches img src attributes with relative paths starting with "images/"
        def replace_relative_images(match):
            current_src = match.group(1)
            if not current_src.startswith(('http://', 'https://', '//', '../', 'data:', 'static/')):
                if current_src.startswith('images/'):
                    # Convert images/file.ext to proper static path
                    static_url = build_url(base_url, f'static/{current_src}')
                    return f'src="{static_url}"'
            return match.group(0)  # Return unchanged if not a relative image path
        
        # Apply the replacement to img src attributes
        content = re.sub(r'src="([^"]+)"', replace_relative_images, content)
        
        return content
    

    def _load_theme(self, debug=False):
        """Load theme based on configuration"""
        theme_name = self.config.theme.lower()
        if theme_name == "tailwind":
            return TailwindTheme(debug=debug)
        elif theme_name == "minimal":
            return MinimalTheme(debug=debug)
        else:
            print(f"⚠️  Unknown theme '{theme_name}', using 'tailwind' as fallback")
            return TailwindTheme(debug=debug)
    



    def _process_items(self, items: List[Any], item_type: str, seo_generator: Optional['SEOGenerator'] = None) -> List[Dict[str, Any]]:
        """Process items with optimized markdown rendering and path resolution"""
        if not items:
            return []
            
        processed = []
        markdown_keys = ['content', 'description', 'excerpt']
        
        for item in items:
            # Handle both dicts (from parsers) and ZenCFG objects (from config)
            if isinstance(item, dict):
                item_dict = item
            elif hasattr(item, 'to_dict'):
                item_dict = item.to_dict()
            else:
                item_dict = dict(item)
            
            # Store raw content before processing
            if 'content' in item_dict and 'content_raw' not in item_dict:
                item_dict['content_raw'] = item_dict['content']
            
            # Resolve path objects to URLs/file paths
            self._resolve_item_paths(item_dict)
            
            # Process content fields using appropriate parser processors
            content_type = item_dict.get('content_type', item_type)
            skip_content_processing = (item_type == 'blog_post_item') or (content_type == 'blog_post_item')
            for key in markdown_keys:
                value = item_dict.get(key)
                if value and isinstance(value, str):
                    # For blog posts, defer 'content' processing to the dedicated blog page pass
                    if skip_content_processing and key == 'content':
                        continue
                    # Skip markdown processing for service item descriptions (they should be plain text)
                    if item_type == 'service_item' and key == 'description':
                        continue
                    # Find appropriate processor for this content type
                    processed_content = self._process_content_field(value, content_type, key)
                    
                    # Note: Bold text highlighting removed - only timeline dot should pulse
                    
                    item_dict[key] = processed_content
            
            # Store template name separately to avoid conflict with item.type field
            item_dict['template_type'] = item_dict.get('template_name') or item_type
            
            
            # Pre-render the HTML for this item to avoid complex template calls
            if item_dict['template_type']:
                item_dict['rendered_html'] = self.theme.render_component(
                    item_dict['template_type'], 
                    item=item_dict,
                    seo_generator=seo_generator
                )
            
            # Generate schema if possible
            item_dict['rendered_schema'] = ''
            if seo_generator:
                if item_type == 'publication_item':
                    item_dict['rendered_schema'] = seo_generator.generate_scholarly_article_schema(item_dict)
                elif item_type == 'project_item':
                    item_dict['rendered_schema'] = seo_generator.generate_software_application_schema(item_dict)

            processed.append(item_dict)
        return processed
    
    def _process_service_items(self, items: List[Any], seo_generator: Optional['SEOGenerator'] = None) -> Dict[str, Any]:
        """Process academic service items, grouping them for structured display."""
        leadership_items = self._process_items(
            [item for item in items if item.category == 'leadership'], 'service_item', seo_generator
        )
        
        # Include all non-leadership items as review items (conference, journal, etc.)
        review_items = self._process_items(
            [item for item in items if item.category != 'leadership'], 'service_item', seo_generator
        )
        
        review_groups = {}
        for item in review_items:
            # Group by category (conference, journal, etc.)
            category = item.get('category', 'Reviewer')
            category_title = category.title() if category != 'conference' else 'Conference'
            if category_title not in review_groups:
                review_groups[category_title] = []
            review_groups[category_title].append(item)
            
        return {
            "leadership_items": leadership_items,
            "review_groups": review_groups
        }

    def _process_content_field(self, content: str, content_type: str, field_name: str) -> str:
        """
        Process a content field using the appropriate parser processor.
        
        Args:
            content: Raw content string to process
            content_type: Type of content (blog_post, page, notebook, etc.)
            field_name: Name of the field being processed
            
        Returns:
            Processed content string
        """
        # Find parsers that can handle this content type
        suitable_parsers = self.parser_registry.get_parsers_for_content_type(content_type)
        
        # Try to get a processor from each suitable parser
        for parser in suitable_parsers:
            processor = parser.get_content_processor(content_type)
            if processor:
                try:
                    return processor(content, self.config.site.markdown_extensions)
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Warning: Failed to process {field_name} with {parser.__class__.__name__}: {e}")
                    continue
        
        # Fallback to basic markdown processing
        try:
            normalized_content = textwrap.dedent(content).strip()
            return markdown.markdown(normalized_content, extensions=self.config.site.markdown_extensions)
        except Exception as e:
            if self.debug:
                print(f"⚠️  Warning: Failed to process {field_name} with fallback markdown: {e}")
            return content  # Return original content if all processing fails

    def _resolve_item_paths(self, item_dict: Dict[str, Any]) -> None:
        """Resolve path strings in content items - simple and consistent"""
        # Fields that might contain file paths or URLs
        path_fields = {'photo', 'image', 'paper', 'code', 'slides', 'video', 'website', 'demo', 
                      'release_notes', 'documentation', 'tutorial_page', 'materials', 'project_page', 
                      'github', 'cv'}
        
        for key, value in list(item_dict.items()):
            if key in path_fields and value and isinstance(value, str):
                try:
                    item_dict[key] = self._resolve_path(value)
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Warning: Failed to resolve path for {key}: {e}")
                    item_dict[key] = None

    def build(self, base_url: str = ""):
        """Build the static site"""
        print("🔨 Building ZenFolio academic website...")
        
        # Clean and create output directory
        if self.output_dir.exists(): 
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy static files
        print("📋 Copying static files...")
        self._copy_static_files()
        
        # Write theme assets (CSS and JS)
        print("🎨 Writing theme assets...")
        self.theme.write_css_file(self.output_dir)
        self.theme.write_js_file(self.output_dir)
        
        # Copy robots.txt to root if it exists
        robots_txt_source = self.static_dir / "robots.txt"
        if robots_txt_source.exists():
            shutil.copy2(robots_txt_source, self.output_dir / "robots.txt")
        
        # Parse content
        self.content.load()
        
        # Initialize SEO generator with configured base_url for absolute URLs
        seo_generator = SEOGenerator(self.config, self.config.site.base_url)
        
        # Build pages and track which ones exist for navigation
        print("🏗️ Building pages...")
        
        # Determine which pages will be built BEFORE building them
        built_pages = [('publications', 'Publications')]  # Always include publications
        
        if self.config.projects and hasattr(self.config.projects, 'items') and self.config.projects.items:
            built_pages.append(('projects', 'Projects'))
            
        if self.config.talks and hasattr(self.config.talks, 'items') and self.config.talks.items:
            built_pages.append(('talks', 'Talks'))
            
        if self.config.news and hasattr(self.config.news, 'items') and self.config.news.items:
            built_pages.append(('news', 'News'))
            
        if self.content.blog_posts and self.config.site.blog_folder:
            built_pages.append(('blog', 'Blog'))
        
        # Store built pages for navbar rendering (before building pages)
        self.built_pages = built_pages
        
        # Now build the pages
        self._build_home_page(self.content.publications, self.content.bio, base_url, seo_generator)
        self._build_list_page("Publications", "publications.html", self.content.publications, 'publication_item', 1, base_url, group_by='year', has_search=True, seo_generator=seo_generator)
        
        # Conditionally build pages only if content exists
        if self.config.projects and hasattr(self.config.projects, 'items') and self.config.projects.items:
            self._build_list_page("Projects", "projects.html", self.config.projects.items, 'project_item', 2, base_url, seo_generator=seo_generator)
        else:
            print("⏭️  Skipping Projects page (no content provided)")
            
        if self.config.talks and hasattr(self.config.talks, 'items') and self.config.talks.items:
            self._build_list_page("Talks", "talks.html", self.config.talks.items, 'talk_item', 1, base_url, seo_generator=seo_generator)
        else:
            print("⏭️  Skipping Talks page (no content provided)")
            
        if self.config.news and hasattr(self.config.news, 'items') and self.config.news.items:
            self._build_list_page("News", "news.html", self.config.news.items, 'news_item', 1, base_url, layout='timeline', seo_generator=seo_generator)
        else:
            print("⏭️  Skipping News page (no content provided)")
            
        if self.content.blog_posts and self.config.site.blog_folder:
            self._build_list_page("Blog", "blog.html", self.content.blog_posts, 'blog_post_item', 2, base_url, seo_generator=seo_generator)
            self._build_blog_post_pages(self.content.blog_posts, base_url, seo_generator)
        else:
            if not self.config.site.blog_folder:
                print("⏭️  Skipping Blog pages (blog disabled in configuration)")
            else:
                print("⏭️  Skipping Blog pages (no content provided)")
        
        self._build_pages(base_url, seo_generator)
        
        # Generate sitemap
        print("🗺️ Generating sitemap...")
        self._generate_sitemap(seo_generator)
        
        print(f"✅ Site built successfully in {self.output_dir}/")
        return True
    
    def _copy_static_files(self):
        """Copy static files with optimization for incremental builds"""
        target_static_dir = self.output_dir / "static"
        
        if not self.static_dir or not self.static_dir.exists():
            return
            
        if target_static_dir.exists():
            shutil.rmtree(target_static_dir)
        
        shutil.copytree(self.static_dir, target_static_dir)

    def _render_and_write_page(self, filename: str, content: str, page_title: str = "", base_url: str = "", 
                              seo_generator: Optional['SEOGenerator'] = None, page_type: str = "page", 
                              item_data: Optional[Dict[str, Any]] = None, 
                              structured_data_list: Optional[str] = None, **context):
        default_current_page = filename.split('.')[0]
        current_page = context.pop('current_page', default_current_page)
        
        # Process author config for template rendering
        author_data = self.config.author.to_dict()
        self._resolve_item_paths(author_data)
        
        # Generate SEO metadata if SEO generator is provided
        seo_context = {
            'canonical_url': None,
            'og_image': None,
            'meta_description': self.config.site.description,
            'structured_data': None
        }
        if structured_data_list:
            seo_context['structured_data'] = structured_data_list
        
        if seo_generator:
            # Add page to sitemap tracking (avoid duplicates)
            if not any(page['path'] == filename for page in self.seo_pages):
                priority = "1.0" if filename == "index.html" else "0.8" if filename in ["publications.html", "projects.html"] else "0.6"
                changefreq = "weekly" if filename == "index.html" else "monthly"
                
                self.seo_pages.append({
                    'path': filename,
                    'priority': priority,
                    'changefreq': changefreq,
                    'lastmod': datetime.now().strftime('%Y-%m-%d')
                })
            
            # Generate meta description
            meta_description = seo_generator.generate_meta_description(page_type, item_data)
            seo_context['meta_description'] = meta_description
            
            # Generate canonical URL
            if self.config.site.base_url:
                seo_context['canonical_url'] = seo_generator._build_url(filename)
                
            # Generate Open Graph image
            # Prioritize blog post image, fall back to author photo
            if page_type == "blog_post" and item_data and item_data.get('image'):
                seo_context['og_image'] = seo_generator._build_url(f"static/{item_data['image']}")
            elif hasattr(self.config.author, 'photo_path') and self.config.author.photo_path:
                seo_context['og_image'] = seo_generator._build_url(f"static/{self.config.author.photo_path}")
            
            # Generate structured data based on page type
            if not seo_context.get('structured_data'):
                if page_type == "homepage":
                    seo_context['structured_data'] = seo_generator.generate_person_schema()
                elif page_type == "blog_post" and item_data:
                    seo_context['structured_data'] = seo_generator.generate_blog_posting_schema(item_data)
        
        html = self.theme.render_page(
            content=content, page_title=page_title, author_name=self.config.author.name,
            site_description=self.config.site.description, base_url=base_url,
            current_page=current_page, author=author_data, built_pages=getattr(self, 'built_pages', []),
            site_seo=self.config.site.seo,  # Add SEO config to template context
            mathjax_config=self.config.mathjax,  # Add MathJax config to template context
            **seo_context, **context
        )
        (self.output_dir / filename).write_text(html, encoding='utf-8')

    def _build_home_page(self, publications: List[Dict], bio_data: Dict, base_url: str, seo_generator: Optional['SEOGenerator'] = None):
        hero_data = self.config.author.to_dict()
        self._resolve_item_paths(hero_data)
        
        # Enhance hero data with structured format for template
        hero_data.update({
            'photo': f"static/{hero_data.get('photo_path', 'profile.jpg')}",
            'actions': [
                {
                    'text': btn.text,
                    'url': btn.url,
                    'style': 'bg-gray-900 dark:bg-white text-white dark:text-gray-900' if btn.style == 'primary' else 'bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white',
                    'external': btn.url.startswith('http')
                }
                for btn in (self.config.author.homepage_buttons or [])
            ],
            'social_links': [
                {'url': hero_data.get('github'), 'icon': 'fab fa-github', 'label': 'GitHub'},
                {'url': hero_data.get('scholar'), 'icon': 'fas fa-graduation-cap', 'label': 'Google Scholar'},
                {'url': hero_data.get('linkedin'), 'icon': 'fab fa-linkedin', 'label': 'LinkedIn'},
                {'url': hero_data.get('twitter'), 'icon': 'fab fa-twitter', 'label': 'Twitter'},
            ]
        })
        # Filter out social links with no URL
        hero_data['social_links'] = [link for link in hero_data['social_links'] if link['url']]
        
        # Select publications for homepage: prioritize highlighted, then recent
        highlighted_pubs = [pub for pub in publications if pub.get('highlight', False)]
        recent_pubs = [pub for pub in publications if not pub.get('highlight', False)]
        
        # Get publication count from config (None = show all highlighted)
        pub_count = self.config.site.homepage_publications_count
        if pub_count is None:
            # Show all highlighted publications
            homepage_pubs = highlighted_pubs
        else:
            # Take up to pub_count publications: highlighted first, then fill with recent
            homepage_pubs = highlighted_pubs[:pub_count]
            if len(homepage_pubs) < pub_count:
                homepage_pubs.extend(recent_pubs[:pub_count - len(homepage_pubs)])
        
        # Update section title based on what we're showing
        pub_section_title = "Selected Publications" if highlighted_pubs else "Recent Publications"
        
        # Select highlighted projects/research for homepage
        highlighted_projects = [item for item in self.config.projects.items if getattr(item, 'highlight', False)]
        
        # This list declaratively controls the homepage layout AFTER the hero.
        sections = [
            {"id": "bio", "data": {
                "title": "About Me", 
                "layout": "bio",
                "content": markdown.markdown(bio_data.get('bio',''), extensions=self.config.site.markdown_extensions),
                "interests": hero_data.get('interests', [])
            }},
            {"id": "featured_work", "data": {
                "title": "Featured Work", "grid_cols": 2,
                "subtitle": "A selection of projects and research I'm particularly proud of.",
                "items": self._process_items(highlighted_projects, 'project_item', seo_generator=seo_generator),
                "view_all_link": {"url": "projects.html", "text": "View all projects"}
            }},
            {"id": "academic_service", "data": {
                "title": "Academic Service", 
                "layout": "service",
                "items": self._process_service_items(self.config.author.service, seo_generator=seo_generator),
            }},
            {"id": "recent_publications", "data": {
                "title": pub_section_title, "grid_cols": 1,
                "items": self._process_items(homepage_pubs, 'publication_item', seo_generator=seo_generator),
                "view_all_link": {"url": "publications.html", "text": "View all publications"}
            }},
            {"id": "recent_news", "data": {
                "title": "Recent News", "layout": "timeline",
                "items": self._process_items(
                    self.config.news.items[:self.config.site.homepage_news_count] if self.config.site.homepage_news_count is not None else self.config.news.items, 
                    'news_item',
                    seo_generator=seo_generator
                ),
                "view_all_link": {"url": "news.html", "text": "View all news"}
            }}
        ]
        
        # Filter sections with content and render them
        rendered_sections = []
        for section in sections:
            section_data = section['data']
            section_id = section['id']
            
            # Validate section has content before attempting to render
            has_content = bool(section_data.get('items') or section_data.get('content'))
            if not has_content:
                if self.debug:
                    print(f"⚠️ Skipping empty section: {section_id}")
                continue
                
            # Render the section
            section_html = self.theme.render_component('section', **section_data)
            
            # Validate the rendered HTML is not empty
            if not section_html or section_html.strip() == "":
                if self.debug:
                    print(f"⚠️ Section '{section_id}' rendered as empty HTML")
                    if section_data.get('items'):
                        print(f"   Items count: {len(section_data['items'])}")
                        first_item = section_data['items'][0] if section_data['items'] else None
                        if first_item and hasattr(first_item, 'get'):
                            print(f"   First item template_type: {first_item.get('template_type', 'unknown')}")
                            print(f"   First item rendered_html length: {len(first_item.get('rendered_html', ''))}")
                continue
                
            section_data['rendered_html'] = section_html
            rendered_sections.append(section_data)
            
        if self.debug:
            print(f"📊 Homepage sections: {len(sections)} defined, {len(rendered_sections)} rendered")
        
        # Render the landing page by passing the hero and the list of rendered sections
        content = self.theme.render_component(
            'landing_page', 
            hero=hero_data,
            sections=rendered_sections
        )
        self._render_and_write_page("index.html", content, page_title=self.config.site.title, base_url=base_url, 
                                   seo_generator=seo_generator, page_type="homepage")

    def _build_list_page(self, title: str, filename: str, items: List[Any], item_type: str, columns: int, base_url: str, layout: str = 'grid', group_by: Optional[str] = None, has_search: bool = False, seo_generator: Optional['SEOGenerator'] = None):
        """Generic function to build list pages (Publications, News, etc.)."""
        processed_items = self._process_items(items, item_type, seo_generator)
        
        # This data will be passed to the page_layout.html.j2 template
        page_data = {
            'title': title, 'columns': columns, 'layout': layout,
            'items': None, 'grouped_items': None, 'items_html': '', 'has_search': has_search
        }

        if group_by:
            # Group items by a key (e.g., 'year' for publications)
            grouped_items = {}
            for item in processed_items:
                key = item.get(group_by)
                if key:
                    if key not in grouped_items: grouped_items[key] = []
                    grouped_items[key].append(item)
            
            try: # Sort years numerically, descending
                sorted_keys = sorted(grouped_items.keys(), key=int, reverse=True)
            except (ValueError, TypeError): # Fallback for non-numeric keys
                sorted_keys = sorted(grouped_items.keys(), reverse=True)
                
            page_data['grouped_items'] = [{'group_name': key, 'items': grouped_items[key]} for key in sorted_keys]
        else:
            # For non-grouped pages, pre-render the HTML for each item
            page_data['items_html'] = "".join([item['rendered_html'] for item in processed_items])

        # Render the page content using the main page_layout template
        content = self.theme.render_component('page_layout', **page_data)
        
        # Determine page type for SEO
        page_type = "page"
        if "publication" in filename:
            page_type = "publications"

        # Extract all schemas and combine them
        all_schemas = [item['rendered_schema'] for item in processed_items if item.get('rendered_schema')]
        combined_schema = f"[{','.join(all_schemas)}]" if all_schemas else None

        self._render_and_write_page(
            filename, content, page_title=title,
            base_url=base_url, current_page=filename.split('.')[0],
            seo_generator=seo_generator, page_type=page_type,
            structured_data_list=combined_schema
        )

    def _build_blog_post_pages(self, blog_posts: List[Dict[str, Any]], base_url: str, seo_generator: Optional['SEOGenerator'] = None):
        blog_output_dir = self.output_dir / 'blog'
        blog_output_dir.mkdir(exist_ok=True)
        processed_posts = self._process_items(blog_posts, 'blog_post_item', seo_generator)
        
        for post in processed_posts:
            # Re-render content from raw source using appropriate processor
            content_type = post.get('content_type', 'blog_post')
            post['content'] = self._process_content_field(post['content_raw'], content_type, 'content')
            
            # Calculate relative base URL for nested blog page
            nested_base_url = self.theme._build_relative_url(base_url, depth=1)
            
            # Process {static} placeholders in content
            post['content'] = self._process_static_placeholders(post['content'], nested_base_url)
            
            content_html = self.theme.render_component('blog_post_page', item=post)
            
            self._render_and_write_page(
                f"blog/{post['slug']}.html", content_html, page_title=post['title'],
                base_url=nested_base_url, current_page='blog',
                seo_generator=seo_generator, page_type="blog_post", item_data=post
            )

    def _build_pages(self, base_url: str = "", seo_generator: Optional['SEOGenerator'] = None):
        """Build standalone pages from the loaded content."""
        if not self.content.pages:
            return
        
        # Create pages directory in output
        (self.output_dir / "pages").mkdir(exist_ok=True)
        
        for page_data in self.content.pages:
            slug = page_data['slug']
            title = page_data['title']
            
            # Process content using appropriate processor
            content_type = page_data.get('content_type', 'page')
            content_html = self._process_content_field(page_data['content'], content_type, 'content')
            
            # Create full HTML page with proper nested base URL
            nested_base_url = self.theme._build_relative_url(base_url, depth=1)
            
            # Process {static} placeholders in content
            content_html = self._process_static_placeholders(content_html, nested_base_url)
            
            # Render using page template
            page_content = self.theme.render_component('page', item={'content': content_html})
            self._render_and_write_page(
                f"pages/{slug}.html", page_content, page_title=title,
                base_url=nested_base_url, current_page='pages',
                seo_generator=seo_generator, page_type="page", item_data=page_data
            )
    
    def _generate_sitemap(self, seo_generator: 'SEOGenerator'):
        """Generate sitemap.xml file"""
        if not self.seo_pages:
            if self.debug:
                print("⚠️  Warning: No pages tracked for sitemap generation")
            return
            
        sitemap_xml = seo_generator.generate_sitemap_xml(self.seo_pages)
        sitemap_path = self.output_dir / "sitemap.xml"
        sitemap_path.write_text(sitemap_xml, encoding='utf-8')
        
        if self.debug:
            print(f"✅ Generated sitemap with {len(self.seo_pages)} pages")


def get_output_dir(content_dir: Path) -> Path:
    """Get output directory from configuration"""
    try:
        config = load_config_from_file(content_dir / "config.py", "config")
        return resolve_directory_path(config.output_path, content_dir.parent)
    except Exception:
        return Path("_site")


class ZenFolioBuildError(Exception):
    """Custom exception for ZenFolio build failures"""
    pass


def build_site(content_dir: Path, theme_override: str = None, debug: bool = False, base_url: str = None, dev: bool = False) -> bool:
    """Build the site with centralized error handling
    
    Returns:
        bool: True if build succeeded, False otherwise
    """
    try:
        ssg = ZenFolio(content_dir=content_dir, theme_override=theme_override, debug=debug)
        
        if dev:
            final_base_url = ""
            if debug:
                print("🔧 Development mode: using relative URLs")
        elif base_url is not None:
            final_base_url = base_url
            if debug:
                print(f"🔧 Using explicit base URL: {final_base_url}")
        else:
            final_base_url = ssg.config.site.base_url
            if debug:
                print(f"🔧 Using site.base_url as base URL: {final_base_url}")
        
        success = ssg.build(base_url=final_base_url)
        
        if not success:
            raise ZenFolioBuildError("Build process reported failure")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Try: pip install -r requirements.txt")
        return False
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("💡 Check that all required files exist")
        return False
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        print("💡 Check file permissions")
        return False
    except ZenFolioBuildError as e:
        print(f"❌ Build failed: {e}")
        print("💡 Check the errors above for details")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        print("💡 Run with --debug for more details")
        return False