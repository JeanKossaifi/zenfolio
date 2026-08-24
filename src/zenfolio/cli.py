"""
Command line interface for ZenFolio - academic website generator
"""

import argparse
from pathlib import Path
import sys

from .zenfolio import build_site
from .server import serve_site
from .validators import validate_site, validate_generated_site
from .init import init_site
from .deploy import create_github_pages_files
from .zenfolio import get_output_dir


def port_number(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(
            f"port must be between 1 and 65535, got {port}"
        )
    return port


def cli():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="ZenFolio - Beautiful, minimal, powerful academic website generator"
    )
    parser.add_argument(
        'command',
        choices=['build', 'init', 'serve', 'dev', 'validate', 'deploy'],
        help="Command to run: 'init' creates a new site, 'build' generates HTML, 'serve' starts local server, 'dev' builds and serves, 'validate' checks config and content, 'deploy' prepares GitHub Pages deployment"
    )
    parser.add_argument(
        '--content-dir',
        type=Path,
        default=Path("."),
        help="Directory containing content files (default: current directory)"
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help="Override the output directory configured by the site (relative paths resolve against --content-dir)"
    )
    parser.add_argument(
        '--port',
        type=port_number,
        default=8000,
        help="Port to serve the website on (default: 8000)"
    )
    parser.add_argument(
        '--host',
        type=str,
        default="127.0.0.1",
        help="Host for the dev server (default: 127.0.0.1; use 0.0.0.0 to expose on the network)"
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help="Don't automatically open browser when serving"
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help="Base URL for deployment. If not specified, uses site.base_url from config for production builds. Use --dev for relative URLs."
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help="Development mode: use relative URLs for local debugging (automatic in 'dev' command)"
    )
    parser.add_argument(
        '--theme',
        type=str,
        help="Built-in or configured site-local theme name"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable template debugging mode (shows undefined variable errors)"
    )

    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_site(args.content_dir)
    elif args.command == 'validate':
        print("🔍 Validating site configuration and content...")
        config_valid = validate_site(args.content_dir, args.output_dir)
        
        # Also validate generated site if it exists
        output_dir = get_output_dir(args.content_dir, args.output_dir)
        if output_dir.exists():
            print("\n🔍 Validating generated site...")
            site_valid = validate_generated_site(
                args.content_dir, args.debug, args.output_dir
            )
            if not config_valid or not site_valid:
                sys.exit(1)
        else:
            print("💡 Run 'build' or 'deploy' first to validate generated site")
            if not config_valid:
                sys.exit(1)
    elif args.command == 'build':
        # Build the site using centralized error handling
        success = build_site(
            args.content_dir,
            args.theme,
            args.debug,
            args.base_url,
            args.dev,
            output_dir=args.output_dir,
        )
        if not success:
            sys.exit(1)
    elif args.command == 'serve':
        ok = serve_site(
            args.content_dir,
            args.port,
            not args.no_browser,
            output_dir=args.output_dir,
            host=args.host,
        )
        if not ok:
            sys.exit(1)
    elif args.command == 'dev':
        # Development mode: build then serve with fresh server
        print("🚀 Development mode: Building and serving...")

        # Build the site using centralized error handling (force dev=True)
        success = build_site(
            args.content_dir,
            args.theme,
            args.debug,
            args.base_url,
            dev=True,
            output_dir=args.output_dir,
        )
        if not success:
            print("❌ Build failed. Cannot start development server.")
            sys.exit(1)
        
        print("✅ Build complete, starting server...")
        ok = serve_site(
            args.content_dir,
            args.port,
            not args.no_browser,
            output_dir=args.output_dir,
            host=args.host,
        )
        if not ok:
            sys.exit(1)
    elif args.command == 'deploy':
        # Always build first, then create deployment files
        print("🔨 Building site for deployment...")
        if not validate_site(args.content_dir, args.output_dir):
            print("❌ Source validation failed. Deployment stopped.")
            sys.exit(1)
        
        # Theme assets are now built directly during site generation
        
        success = build_site(
            args.content_dir,
            args.theme,
            args.debug,
            args.base_url,
            dev=False,
            output_dir=args.output_dir,
        )
        if not success:
            print("❌ Build failed. Cannot prepare deployment.")
            sys.exit(1)
        
        # Create deployment files first
        create_github_pages_files(args.content_dir, args.output_dir)
        
        # Then validate the complete deployment package
        print("🔍 Validating generated site...")
        validation_passed = validate_generated_site(
            args.content_dir,
            args.debug,
            args.output_dir,
            production=True,
        )
        if not validation_passed:
            print("❌ Site validation failed. Fix the issues above before deploying.")
            sys.exit(1)


if __name__ == "__main__":
    cli() 