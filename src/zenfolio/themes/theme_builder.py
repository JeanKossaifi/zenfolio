"""
Theme builder for ZenFolio.

This module handles building theme assets (CSS, JS) using appropriate tools.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


class ThemeBuilder:
    """Handles building theme assets."""

    def __init__(self, theme_dir: Path, debug: bool = False):
        """Initialize theme builder.
        
        Args:
            theme_dir: Path to theme directory
            debug: Enable debug output
        """
        self.theme_dir = theme_dir
        self.debug = debug
        self.package_json = theme_dir / "package.json"
        self.node_modules = theme_dir / "node_modules"

    def _run_npm_command(self, command: str, cwd: Optional[Path] = None) -> bool:
        """Run an npm command.
        
        Args:
            command: Command to run (e.g., "install", "run build")
            cwd: Working directory (defaults to theme_dir)
            
        Returns:
            bool: True if command succeeded
        """
        try:
            # Use npm from PATH or local installation
            npm_path = "npm"
            if os.name == "nt":  # Windows
                npm_path = "npm.cmd"

            result = subprocess.run(
                [npm_path] + command.split(),
                cwd=str(cwd or self.theme_dir),
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.debug:
                print(f"📦 {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            if self.debug:
                print(f"❌ npm command failed: {e.stderr}")
            return False
        except Exception as e:
            if self.debug:
                print(f"❌ Error running npm: {e}")
            return False

    def _ensure_dependencies(self) -> bool:
        """Ensure all npm dependencies are installed.
        
        Returns:
            bool: True if dependencies are installed
        """
        if not self.package_json.exists():
            if self.debug:
                print("⚠️ No package.json found")
            return True  # Not a failure, just no dependencies needed
            
        if not self.node_modules.exists() or not self._has_all_dependencies():
            if self.debug:
                print("📦 Installing dependencies...")
            return self._run_npm_command("install")
            
        return True

    def _has_all_dependencies(self) -> bool:
        """Check if all dependencies from package.json are installed.
        
        Returns:
            bool: True if all dependencies are installed
        """
        try:
            import json
            with open(self.package_json) as f:
                package = json.load(f)
                
            deps = {
                **package.get("dependencies", {}),
                **package.get("devDependencies", {})
            }
            
            for dep in deps:
                if not (self.node_modules / dep).exists():
                    return False
            return True
            
        except Exception as e:
            if self.debug:
                print(f"❌ Error checking dependencies: {e}")
            return False

    def build_css(self) -> bool:
        """Build CSS assets.
        
        Returns:
            bool: True if build succeeded
        """
        if not self._ensure_dependencies():
            return False
            
        if self.debug:
            print("🎨 Building CSS...")
            
        return self._run_npm_command("run build-css")

    def build_js(self) -> bool:
        """Build JavaScript assets.
        
        Returns:
            bool: True if build succeeded
        """
        if not self._ensure_dependencies():
            return False
            
        if self.debug:
            print("📜 Building JavaScript...")
            
        return self._run_npm_command("run build-js")

    def build(self) -> bool:
        """Build all theme assets.
        
        Returns:
            bool: True if all builds succeeded
        """
        return self.build_css() and self.build_js()

    def watch(self) -> bool:
        """Start watching theme assets for changes.
        
        Returns:
            bool: True if watch mode started successfully
        """
        if not self._ensure_dependencies():
            return False
            
        if self.debug:
            print("👀 Watching for changes...")
            
        return self._run_npm_command("run watch")
