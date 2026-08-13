"""Backward-compatible facade for the ZenFolio build pipeline."""

from pathlib import Path
from typing import Dict, List, Any, Optional, Sequence

from .build_context import BuildContext
from .collection_builder import CollectionBuilder
from .content import Content
from .content_processor import ContentProcessor
from .errors import ZenFolioBuildError
from .homepage_composer import HomepageComposer
from .output_manager import OutputManager
from .page_renderer import PageRenderer
from .parsers import parser_registry
from .routing import LEGACY_ROUTES as DEFAULT_LEGACY_ROUTES
from .routing import RouteRegistry
from .site_builder import SiteBuilder
from .theme_loader import load_theme
from .seo_utils import SEOGenerator
from zencfg import load_config_from_file

class ZenFolio:
    """Stable public API backed by focused build components."""

    LEGACY_ROUTES = DEFAULT_LEGACY_ROUTES
    
    def __init__(
        self,
        content_dir: Path = Path("."),
        theme_override: str = None,
        debug: bool = False,
        output_override: Optional[Path] = None,
    ):
        context = BuildContext.create(
            content_dir,
            theme_override=theme_override,
            output_override=output_override,
            debug=debug,
        )
        self.content_dir = context.content_dir
        self.config = context.config
        self.identity = context.identity
        self.site_type = context.site_type
        self.static_dir = context.static_dir
        self.output_dir = context.output_dir
        self.theme = context.theme
        self.theme_override = context.theme_override
        self.debug = context.debug
        self.output_override = output_override
        self.parser_registry = parser_registry
        
        # Initialize content loader
        self.content = Content(self.content_dir, self.config, debug)
        self.route_registry = RouteRegistry(self.config, self.content)
        self.output_manager = OutputManager(
            self.config,
            self.content_dir,
            self.static_dir,
            self.output_dir,
        )
        self.content_processor = ContentProcessor(
            self.config,
            self.theme,
            self.parser_registry,
            debug,
        )
        self.page_renderer = PageRenderer(
            self.config,
            self.identity,
            self.site_type,
            self.theme,
            self.content_processor.resolve_path,
            self.content_processor.resolve_item_paths,
            self._set_page_context,
        )
        self.homepage_composer = HomepageComposer(self)
        self.collection_builder = CollectionBuilder(self)
        self.site_builder = SiteBuilder(self)

        # Initialize SEO utilities and sitemap tracking
        self.seo_pages = []  # Track pages for sitemap generation
        self.navigation = []
        self.effective_base_url = ""
        self.generated_routes = set()
    

    
    def _resolve_path(self, path: str) -> str:
        return self.content_processor.resolve_path(path)
    
    def _process_static_placeholders(self, content: str, base_url: str = "") -> str:
        return self.content_processor.process_static_placeholders(
            content, base_url
        )
    

    def _load_theme(self, debug=False):
        return load_theme(
            self.config,
            self.content_dir,
            self.theme_override,
            debug,
        )

    def _validate_output_directory(self):
        self._sync_output_manager()
        self.output_manager.validate()

    def _sync_output_manager(self):
        """Keep mutable legacy facade paths reflected in the manager."""
        self.output_manager.content_dir = self.content_dir
        self.output_manager.static_dir = self.static_dir
        self.output_manager.output_dir = self.output_dir

    def _sync_page_renderer(self):
        """Keep mutable build state reflected in the renderer."""
        self.page_renderer.configure(
            self.output_dir,
            self.navigation,
            getattr(self, "built_pages", []),
            self.seo_pages,
            self.generated_routes,
        )

    def _navigation_key(self, item) -> str:
        return self.route_registry.navigation_key(item)

    def _configured_routes(self) -> Dict[str, str]:
        return self.route_registry.configured_routes()

    def _route_for(self, key: str) -> str:
        return self.route_registry.route_for(key)

    def _standalone_page_route(self, page_data: Dict[str, Any]) -> str:
        return self.route_registry.standalone_page_route(page_data)

    def _configure_navigation(self):
        self.navigation, self.built_pages = (
            self.route_registry.configure_navigation()
        )

    def _is_requested_page(self, *keys: str) -> bool:
        return self.route_registry.is_requested_page(*keys)

    def _page_base_url(self, route: str) -> str:
        return self.route_registry.page_base_url(
            route, self.effective_base_url
        )

    def _set_page_context(self, route: str) -> str:
        base_url = self._page_base_url(route)
        self.theme.set_render_context(base_url)
        return base_url
    



    def _process_items(self, items: List[Any], item_type: str, seo_generator: Optional['SEOGenerator'] = None) -> List[Dict[str, Any]]:
        return self.content_processor.process_items(
            items, item_type, seo_generator
        )
    
    def _process_service_items(self, items: List[Any], seo_generator: Optional['SEOGenerator'] = None) -> Dict[str, Any]:
        return self.content_processor.process_service_items(
            items, seo_generator
        )

    def _process_content_field(self, content: str, content_type: str, field_name: str) -> str:
        return self.content_processor.process_content_field(
            content, content_type, field_name
        )

    def _resolve_item_paths(self, item_dict: Dict[str, Any]) -> None:
        self.content_processor.resolve_item_paths(item_dict)

    def build(self, base_url: str = ""):
        return self.site_builder.build(base_url)
    
    def _copy_static_files(self):
        self._sync_output_manager()
        self.output_manager.copy_static_files()

    def _render_and_write_page(
        self,
        filename: str,
        content: str,
        page_title: str = "",
        base_url: str = "",
        seo_generator: Optional['SEOGenerator'] = None,
        page_type: str = "page",
        item_data: Optional[Dict[str, Any]] = None,
        structured_data_list: Optional[str] = None,
        **context,
    ):
        self._sync_page_renderer()
        self.page_renderer.render_and_write(
            filename,
            content,
            page_title=page_title,
            seo_generator=seo_generator,
            page_type=page_type,
            item_data=item_data,
            structured_data_list=structured_data_list,
            **context,
        )

    def _selected_publications(
        self, publications: Sequence[Dict[str, Any]], limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        return self.homepage_composer.selected_publications(
            publications, limit
        )

    def _prepare_blog_routes(self):
        self.homepage_composer.prepare_blog_routes()

    def _group_people(self, people: Sequence[Dict[str, Any]]):
        return self.homepage_composer.group_people(people)

    def _resolve_homepage_section(
        self,
        section_config: Any,
        publications: Sequence[Dict[str, Any]],
        seo_generator: Optional['SEOGenerator'],
    ) -> Dict[str, Any]:
        return self.homepage_composer.resolve_section(
            section_config, publications, seo_generator
        )

    def _build_configured_home_page(
        self,
        publications: List[Dict],
        base_url: str,
        seo_generator: Optional['SEOGenerator'],
    ):
        self.homepage_composer.build_configured(
            publications, base_url, seo_generator
        )

    def _build_home_page(self, publications: List[Dict], bio_data: Dict, base_url: str, seo_generator: Optional['SEOGenerator'] = None):
        self.homepage_composer.build(
            publications, bio_data, base_url, seo_generator
        )

    def _build_list_page(
        self,
        title: str,
        filename: str,
        items: List[Any],
        item_type: str,
        columns: int,
        base_url: str,
        layout: str = 'grid',
        group_by: Optional[str] = None,
        has_search: bool = False,
        seo_generator: Optional['SEOGenerator'] = None,
        scholar_stats: Optional[dict] = None,
        page_type: str = "page",
        intro: str = "",
        meta_description: str = "",
        filter_directions: Optional[List[str]] = None,
        grouped_items: Optional[List[Dict[str, Any]]] = None,
    ):
        self.collection_builder.build_list_page(
            title,
            filename,
            items,
            item_type,
            columns,
            base_url,
            layout=layout,
            group_by=group_by,
            has_search=has_search,
            seo_generator=seo_generator,
            scholar_stats=scholar_stats,
            page_type=page_type,
            intro=intro,
            meta_description=meta_description,
            filter_directions=filter_directions,
            grouped_items=grouped_items,
        )

    def _build_team_page(
        self, seo_generator: Optional['SEOGenerator'] = None
    ):
        self.collection_builder.build_team_page(seo_generator)

    def _build_blog_post_pages(self, blog_posts: List[Dict[str, Any]], base_url: str, seo_generator: Optional['SEOGenerator'] = None):
        self.collection_builder.build_blog_post_pages(
            blog_posts, base_url, seo_generator
        )

    def _build_pages(self, base_url: str = "", seo_generator: Optional['SEOGenerator'] = None):
        self.collection_builder.build_standalone_pages(
            base_url, seo_generator
        )
    
    def _generate_sitemap(self, seo_generator: 'SEOGenerator'):
        self.collection_builder.generate_sitemap(seo_generator)


def get_output_dir(
    content_dir: Path, output_override: Optional[Path] = None
) -> Path:
    """Get output directory from configuration"""
    content_dir = Path(content_dir).expanduser().resolve()
    try:
        config = load_config_from_file(content_dir, "config.py", "config")
        output_path = Path(output_override or config.output_path)
        return (
            output_path.expanduser().resolve()
            if output_path.is_absolute()
            else (content_dir / output_path).resolve()
        )
    except Exception:
        return (content_dir / (output_override or "_site")).resolve()


def build_site(
    content_dir: Path,
    theme_override: str = None,
    debug: bool = False,
    base_url: str = None,
    dev: bool = False,
    output_dir: Optional[Path] = None,
) -> bool:
    """Build the site with centralized error handling
    
    Returns:
        bool: True if build succeeded, False otherwise
    """
    try:
        ssg = ZenFolio(
            content_dir=content_dir,
            theme_override=theme_override,
            debug=debug,
            output_override=output_dir,
        )
        
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