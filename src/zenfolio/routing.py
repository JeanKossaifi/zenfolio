"""Public-route and navigation management for ZenFolio builds."""

from typing import Any, Dict, List, Set, Tuple, TypedDict

from .utils import is_external_url, normalize_route, route_depth


class NavigationEntry(TypedDict):
    key: str
    label: str
    route: str
    visible: bool
    external: bool


LEGACY_ROUTES = {
    "home": "/",
    "publications": "/publications.html",
    "projects": "/projects.html",
    "talks": "/talks.html",
    "news": "/news.html",
    "blog": "/blog.html",
    "updates": "/blog.html",
    "team": "/team.html",
    "people": "/team.html",
    "research": "/research.html",
}

COLLECTION_KEYS = {
    "publications",
    "projects",
    "talks",
    "news",
    "blog",
    "updates",
    "team",
    "people",
}


class RouteRegistry:
    """Resolve collection routes and derive navigation without rendering."""

    def __init__(self, config: Any, content: Any):
        self.config = config
        self.content = content
        self.navigation: List[NavigationEntry] = []
        self.built_pages: List[Tuple[str, str]] = []

    @staticmethod
    def navigation_key(item: Any) -> str:
        key = getattr(item, "key", None)
        if key:
            return str(key).strip().lower().replace(" ", "_")

        route = str(getattr(item, "route", ""))
        if route and not is_external_url(route):
            parts = [part for part in route.strip("/").split("/") if part]
            if parts:
                return (
                    parts[0][:-5]
                    if parts[0].endswith(".html")
                    else parts[0]
                )
        return str(getattr(item, "label", "")).strip().lower().replace(" ", "_")

    def configured_routes(self) -> Dict[str, str]:
        routes: Dict[str, str] = {}
        for item in getattr(self.config, "navigation", None) or []:
            key = self.navigation_key(item)
            route = str(item.route)
            if key and route and not is_external_url(route):
                routes[key] = normalize_route(route)

        if "updates" in routes:
            routes.setdefault("blog", routes["updates"])
        if "blog" in routes:
            routes.setdefault("updates", routes["blog"])
        if "team" in routes:
            routes.setdefault("people", routes["team"])
        if "people" in routes:
            routes.setdefault("team", routes["people"])
        return routes

    def route_for(self, key: str) -> str:
        configured = self.configured_routes()
        if key in configured:
            return configured[key]

        route = None
        if key == "publications":
            route = getattr(self.config.publications, "route", None)
        elif key == "projects" and self.config.projects:
            route = getattr(self.config.projects, "route", None)
        elif key == "talks" and self.config.talks:
            route = getattr(self.config.talks, "route", None)
        elif key in {"team", "people"} and self.config.people:
            route = getattr(self.config.people, "route", None)
        elif key == "research" and self.config.research_areas:
            route = getattr(self.config.research_areas, "route", None)
        elif key in {"blog", "updates"}:
            route = getattr(self.config.site, "blog_route", None)

        return (
            normalize_route(route)
            if route
            else LEGACY_ROUTES.get(key, f"/pages/{key}.html")
        )

    def standalone_page_route(self, page_data: Dict[str, Any]) -> str:
        slug = page_data["slug"]
        if page_data.get("route"):
            return normalize_route(page_data["route"])
        if slug == "research" and self.config.research_areas:
            return self.route_for("research")

        configured = self.configured_routes()
        if slug in configured and slug not in COLLECTION_KEYS:
            return configured[slug]
        return f"/pages/{slug}.html"

    def configure_navigation(
        self,
    ) -> Tuple[List[NavigationEntry], List[Tuple[str, str]]]:
        configured = getattr(self.config, "navigation", None)
        if configured is not None:
            navigation: List[NavigationEntry] = [
                {
                    "key": self.navigation_key(item),
                    "label": item.label,
                    "route": (
                        item.route
                        if is_external_url(item.route)
                        else normalize_route(item.route)
                    ),
                    "visible": bool(item.visible),
                    "external": is_external_url(item.route),
                }
                for item in configured
            ]
        else:
            navigation = [
                {
                    "key": "publications",
                    "label": "Publications",
                    "route": self.route_for("publications"),
                    "visible": True,
                    "external": False,
                }
            ]
            news_config = self.config.news
            merge_talks = bool(
                news_config and getattr(news_config, "merge_talks", False)
            )
            optional_collections = [
                ("projects", "Projects", self.config.projects),
            ]
            if not merge_talks:
                optional_collections.append(
                    ("talks", "Talks", self.config.talks)
                )
            optional_collections.extend(
                [
                    (
                        "news",
                        getattr(news_config, "title", "News"),
                        news_config,
                    ),
                    ("research", "Research", self.config.research_areas),
                    ("team", "Team", self.config.people),
                ]
            )
            for key, label, collection in optional_collections:
                if collection and getattr(collection, "items", None):
                    navigation.append(
                        {
                            "key": key,
                            "label": label,
                            "route": self.route_for(key),
                            "visible": True,
                            "external": False,
                        }
                    )
            if self.content.blog_posts and self.config.site.blog_folder:
                navigation.append(
                    {
                        "key": "blog",
                        "label": self.config.site.blog_label,
                        "route": self.route_for("blog"),
                        "visible": True,
                        "external": False,
                    }
                )

        built_pages = [
            (item["key"], item["label"])
            for item in navigation
            if item["visible"] and not item["external"]
        ]
        self.navigation = navigation
        self.built_pages = built_pages
        return navigation, built_pages

    def is_requested_page(self, *keys: str) -> bool:
        if getattr(self.config, "navigation", None) is None:
            return True
        aliases: Set[str] = set(keys)
        if aliases & {"blog", "updates"}:
            aliases.update({"blog", "updates"})
        if aliases & {"team", "people"}:
            aliases.update({"team", "people"})
        visible_keys = {
            item["key"] for item in self.navigation if item["visible"]
        }
        return bool(aliases & visible_keys)

    @staticmethod
    def page_base_url(route: str, effective_base_url: str) -> str:
        if effective_base_url and not is_external_url(effective_base_url):
            return effective_base_url
        return "../" * route_depth(route)
