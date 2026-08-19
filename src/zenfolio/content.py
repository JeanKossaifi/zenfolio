"""
This module defines the content model for the ZenFolio website generator.
It handles loading, parsing, and organizing all content from the user's content directory.
"""
import markdown
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .parsers import BibtexParser, parser_registry
from .models.content_models import BlogPost, Page, Bio


class Content:
    """A class to represent the website's content."""

    def __init__(self, content_dir: Path, config: Any, debug: bool = False):
        self.content_dir = content_dir
        self.config = config
        self.debug = debug
        self.parser_registry = parser_registry

        self.bio: Dict[str, Any] = {}
        self.publications: List[Dict[str, Any]] = []
        self.blog_posts: List[Dict[str, Any]] = []
        self.pages: List[Dict[str, Any]] = []

    def load(self):
        """Load all content from the content directory."""
        print("📝 Parsing content...")
        self.bio = self._safe_parse_bio_data()
        self.publications = self._safe_parse_publications()
        self.blog_posts = self._safe_parse_blog_posts()
        self.pages = self._safe_parse_pages()

    def _safe_parse_bio_data(self):
        """Safely parse bio data with error handling"""
        try:
            identity = (
                getattr(self.config, "identity", None)
                or getattr(self.config, "author", None)
            )
            index_path = self.content_dir / "index.md"
            parser = self.parser_registry.get_parser_for_file(index_path)
            
            if parser:
                raw_data = parser.parse_file(index_path)
                if raw_data:
                    bio_data = raw_data.get('metadata', {}).copy()
                    bio_data['bio'] = raw_data.get('content', '')
                    # Use interests from config if available
                    if identity is not None and hasattr(identity, 'interests'):
                        bio_data['interests'] = identity.interests
                    else:
                        bio_data.setdefault('interests', [])
                    
                    bio = Bio(**bio_data)
                    return bio.to_dict()
            
            # If no bio data found, use config data
            if identity is not None:
                return {
                    'bio': '',  # Empty bio content
                    'interests': identity.interests if hasattr(identity, 'interests') else [],
                    'title': identity.title if hasattr(identity, 'title') else '',
                    'affiliation': identity.affiliation if hasattr(identity, 'affiliation') else '',
                }
            
            if self.debug:
                print("⚠️  Warning: No suitable parser found for index.md, using empty bio data")
            return Bio().to_dict()
            
        except FileNotFoundError:
            if self.debug:
                print("⚠️  Warning: index.md not found, using empty bio data")
            return Bio().to_dict()
        except Exception as e:
            if self.debug:
                print(f"⚠️  Warning: Failed to parse index.md: {e}")
            return Bio().to_dict()

    def _safe_parse_publications(self):
        """Safely parse publications with error handling"""
        try:
            if Path(self.config.publications.bib_path).is_absolute():
                bibtex_file_path = Path(self.config.publications.bib_path)
            else:
                bibtex_file_path = self.content_dir / self.config.publications.bib_path
            
            if not bibtex_file_path or not bibtex_file_path.exists():
                if self.debug:
                    print(f"⚠️  Warning: BibTeX file not found, using empty publications")
                return []
            
            bibtex_parser = BibtexParser(self.config.publications.highlight_author)
            return bibtex_parser.parse_file(bibtex_file_path)
        except Exception as e:
            if self.debug:
                print(f"⚠️  Warning: Failed to parse publications: {e}")
            return []

    def _safe_parse_blog_posts(self):
        """Safely parse blog posts with error handling using extensible parser system"""
        try:
            # Check if blog is disabled in configuration
            if not self.config.site.blog_folder:
                if self.debug:
                    print("⚠️  Blog disabled in configuration (site.blog_folder = None)")
                return []
            
            blog_dir = self.content_dir / self.config.site.blog_folder
            if not blog_dir.exists():
                if self.debug:
                    print(f"⚠️  Warning: blog directory '{self.config.site.blog_folder}' not found, using empty blog posts")
                return []
            
            all_raw_posts = []
            blog_parsers = self.parser_registry.get_parsers_for_content_type('blog_post')
            
            for parser in blog_parsers:
                try:
                    raw_posts = parser.parse_directory(blog_dir, 'blog_post')
                    for raw_post in raw_posts:
                        if 'metadata' in raw_post:
                            flattened_post = raw_post['metadata'].copy()
                            flattened_post['content'] = raw_post.get('content', '')
                            flattened_post['content_type'] = raw_post.get('content_type', 'markdown')
                            all_raw_posts.append(flattened_post)
                        else:
                            all_raw_posts.append(raw_post)
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Warning: Parser {parser.__class__.__name__} failed: {e}")
                    continue
            
            seen_slugs = set()
            unique_posts = []
            for post in all_raw_posts:
                slug = post.get('slug')
                if slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                    unique_posts.append(post)
            
            validated_posts = []
            for raw_post in unique_posts:
                try:
                    blog_post = BlogPost(**raw_post, content_raw=raw_post.get('content', ''))
                    post_data = blog_post.to_dict()
                    plain_text = re.sub(
                        r"<[^>]+>",
                        " ",
                        str(raw_post.get("content", "")),
                    )
                    word_count = len(re.findall(r"\b[\w'-]+\b", plain_text))
                    post_data["reading_minutes"] = max(
                        1,
                        math.ceil(word_count / 220),
                    )
                    validated_posts.append(post_data)
                except Exception as e:
                    if self.debug:
                        print(f"⚠️  Warning: Failed to validate blog post {raw_post.get('slug', 'unknown')}: {e}")
                    continue
            
            def blog_date_key(post):
                value = post.get("date", "")
                if isinstance(value, datetime):
                    return (1, value.date().isoformat())
                if isinstance(value, date):
                    return (1, value.isoformat())
                text = str(value or "").strip()
                try:
                    normalized = datetime.fromisoformat(
                        text.replace("Z", "+00:00")
                    ).date().isoformat()
                    return (1, normalized)
                except ValueError:
                    return (0, text)

            return sorted(
                validated_posts,
                key=blog_date_key,
                reverse=True,
            )
        except Exception as e:
            print(f"⚠️  Warning: Failed to parse blog posts: {e}")
            return []

    def _safe_parse_pages(self):
        """Build standalone pages from pages/ directory"""
        pages_dir = self.content_dir / "pages"
        if not pages_dir.exists():
            return []
        
        parsed_pages = []
        for file_path in pages_dir.iterdir():
            if not file_path.is_file() or file_path.name.startswith(('_', '.')):
                continue
            
            parser = self.parser_registry.get_parser_for_file(file_path)
            if not parser:
                if self.debug:
                    print(f"⚠️  Warning: No parser found for {file_path}")
                continue
            
            raw_data = parser.parse_file(file_path)
            if not raw_data:
                continue
            
            if 'metadata' in raw_data:
                raw_page_data = raw_data['metadata'].copy()
                raw_page_data['content'] = raw_data.get('content', '')
            else:
                raw_page_data = raw_data
            
            raw_page_data.setdefault('title', raw_page_data.get('slug', file_path.stem).replace('-', ' ').title())
            raw_page_data.setdefault('slug', file_path.stem)
            raw_page_data.setdefault('content_type', raw_data.get('content_type', 'markdown'))
            
            try:
                page = Page(**raw_page_data)
                parsed_pages.append(page.to_dict())
            except Exception as e:
                if self.debug:
                    print(f"⚠️  Warning: Failed to validate page {file_path}: {e}")
                continue
        return parsed_pages
