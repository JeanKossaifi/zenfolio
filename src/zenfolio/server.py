"""
This module contains the development server for the ZenFolio website generator.
"""
import errno
import http.server
import socketserver
import webbrowser
import threading
import functools
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Callable, Iterable, Optional

from .zenfolio import get_output_dir


class ThreadedHTTPServer(socketserver.ThreadingTCPServer):
    """Concurrent dev server.

    The previous ``socketserver.TCPServer`` handled one request at a time, so a
    single idle keep-alive socket blocked every other request. Browsers open
    several parallel connections per host, which was enough to wedge the server
    until those connections timed out.
    """

    daemon_threads = True
    allow_reuse_address = True


class RobustHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that gracefully handles broken pipe errors"""

    def log_message(self, format, *args):
        """Override to suppress verbose logging"""
        message = format % args
        if "Broken pipe" not in message and "Connection reset" not in message:
            super().log_message(format, *args)

    def finish(self):
        """Override to handle broken pipe errors gracefully"""
        try:
            super().finish()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def handle_one_request(self):
        """Override to handle broken pipe errors during request processing"""
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            pass


class DevelopmentWatcher:
    """Poll source files and rebuild once edits have settled.

    No dependency or platform-specific file-event backend is required. Output,
    package installations, and generated CSS/cache files are excluded so a
    successful build cannot trigger an endless rebuild loop.
    """

    ignored_directories = {
        ".git", ".hg", ".svn", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
        ".zenfolio-cache", ".venv", "venv",
    }

    def __init__(
        self,
        paths: Iterable[Path],
        output_dir: Path,
        rebuild: Callable[[], bool],
        debounce: float = 0.4,
        poll_interval: float = 0.3,
    ):
        self.paths = paths
        self.output_dir = output_dir.resolve()
        self.rebuild = rebuild
        self.debounce = debounce
        self.poll_interval = poll_interval
        self.previous = self.snapshot()
        self.changed_at = None

    def _ignored(self, path: Path) -> bool:
        if path.name in self.ignored_directories:
            return True
        if ".zenfolio-stage-" in path.name or ".zenfolio-backup-" in path.name:
            return True
        if path.name in {".input.sha256", ".DS_Store"} or path.suffix == ".pyc":
            return True
        if path.name == "theme.css" and (path.parent / "input.css").is_file():
            package_file = path.parent.parent / "package.json"
            try:
                scripts = json.loads(package_file.read_text(encoding="utf-8")).get("scripts", {})
                if "build:css" in scripts or "build" in scripts:
                    return True
            except (OSError, ValueError):
                pass
        resolved = path.resolve()
        return resolved == self.output_dir or self.output_dir in resolved.parents

    def snapshot(self):
        state = {}
        for root in list(self.paths):
            root = Path(root)
            if self._ignored(root):
                continue
            if root.is_file():
                candidates = [root]
            else:
                candidates = []
                for directory, subdirs, files in os.walk(root):
                    parent = Path(directory)
                    subdirs[:] = [
                        name for name in subdirs
                        if not self._ignored(parent / name)
                    ]
                    candidates.extend(parent / name for name in files)
            for path in candidates:
                if self._ignored(path):
                    continue
                try:
                    stat = path.stat()
                    state[str(path.resolve())] = (stat.st_mtime_ns, stat.st_size)
                except OSError:
                    # Editors can remove/replace a file between walk and stat.
                    continue
        return state

    def poll(self, now: Optional[float] = None) -> Optional[bool]:
        now = time.monotonic() if now is None else now
        current = self.snapshot()
        if current != self.previous:
            self.previous = current
            self.changed_at = now
        if self.changed_at is None or now - self.changed_at < self.debounce:
            return None
        self.changed_at = None
        print("🔄 Source changed; rebuilding...")
        try:
            success = self.rebuild()
        except Exception as error:
            print(f"❌ Rebuild failed: {error}")
            success = False
        if success:
            print("✅ Rebuilt. Refresh your browser to see the changes.")
        else:
            print("⚠️ Rebuild failed; keeping the last successful site. "
                  "Watching for the next edit.")
        return success

    def run(self, stop: threading.Event) -> None:
        while not stop.wait(self.poll_interval):
            self.poll()


def _dev_build(
    content_dir: str,
    output_dir: str,
    theme_override: Optional[str],
    debug: bool,
    metadata_path: str,
) -> bool:
    """Subprocess entry point: load current config, build local CSS, build site."""
    from .build_context import BuildContext
    from .themes import LocalTheme
    from .zenfolio import build_site

    try:
        context = BuildContext.create(
            Path(content_dir), theme_override, Path(output_dir), debug
        )
        watch_paths = [context.content_dir, context.static_dir]
        if isinstance(context.theme, LocalTheme):
            watch_paths.append(context.theme.theme_dir)
        # Keep watching a newly configured external theme even if its CSS
        # script fails: fixing that source must be enough to retry the build.
        Path(metadata_path).write_text(
            json.dumps([str(path) for path in watch_paths]), encoding="utf-8"
        )
        if isinstance(context.theme, LocalTheme):
            theme_dir = context.theme.theme_dir
            package_file = theme_dir / "package.json"
            if package_file.is_file():
                package = json.loads(package_file.read_text(encoding="utf-8"))
                scripts = package.get("scripts", {})
                script = next(
                    (name for name in ("build:css", "build") if name in scripts),
                    None,
                )
                if script:
                    npm = shutil.which("npm")
                    if not npm:
                        raise RuntimeError(
                            "This local theme has a CSS build script, but npm "
                            "is unavailable. Install Node.js/npm to use dev."
                        )
                    print(f"🎨 Building local theme assets with npm run {script}...", flush=True)
                    subprocess.run([npm, "run", script], cwd=theme_dir, check=True)
        return build_site(
            Path(content_dir), theme_override, debug,
            dev=True, output_dir=Path(output_dir),
        )
    except Exception as error:
        print(f"❌ Development build failed: {error}", flush=True)
        if debug:
            import traceback
            traceback.print_exc()
        return False


class DevelopmentBuilder:
    """Rebuild in a fresh process so imported config modules cannot go stale."""

    def __init__(self, content_dir, output_dir, theme_override=None, debug=False):
        self.content_dir = Path(content_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.theme_override = theme_override
        self.debug = debug
        self.watch_paths = {self.content_dir}
        self.cancelled = threading.Event()

    @staticmethod
    def _stop_process(process) -> None:
        """Interrupt the worker (and its CSS child), allowing staging cleanup."""
        if process.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGINT)
            else:
                process.terminate()
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait()

    def __call__(self) -> bool:
        if self.cancelled.is_set():
            return False
        with tempfile.TemporaryDirectory(prefix="zenfolio-dev-") as temporary:
            metadata = Path(temporary) / "watch-paths.json"
            arguments = {
                "content_dir": str(self.content_dir),
                "output_dir": str(self.output_dir),
                "theme_override": self.theme_override,
                "debug": self.debug,
                "metadata_path": str(metadata),
            }
            environment = os.environ.copy()
            # A separate bytecode location also avoids Python's second-level
            # .pyc timestamps reusing a same-size edit from the previous run.
            environment["PYTHONPYCACHEPREFIX"] = str(Path(temporary) / "bytecode")
            try:
                process = subprocess.Popen(
                    [sys.executable, "-B", "-c",
                     "import json,sys; from zenfolio.server import _dev_build; "
                     "sys.exit(0 if _dev_build(**json.loads(sys.argv[1])) else 1)",
                    json.dumps(arguments)],
                    env=environment,
                    start_new_session=os.name == "posix",
                )
            except OSError as error:
                print(f"❌ Could not start development build: {error}")
                return False
            try:
                while process.poll() is None:
                    if self.cancelled.wait(0.1):
                        self._stop_process(process)
                        return False
            except BaseException:
                self._stop_process(process)
                raise
            if metadata.is_file():
                self.watch_paths.update(
                    Path(path) for path in json.loads(metadata.read_text(encoding="utf-8"))
                )
            return process.returncode == 0


def develop_site(
    content_dir: Path,
    port: int = 8000,
    open_browser: bool = True,
    output_dir: Path = None,
    host: str = "127.0.0.1",
    theme_override: str = None,
    debug: bool = False,
) -> bool:
    """Build, serve, and watch edits; keep serving the last good build on error."""
    content_dir = Path(content_dir).expanduser().resolve()
    output_dir = get_output_dir(content_dir, output_dir)
    rebuild = DevelopmentBuilder(content_dir, output_dir, theme_override, debug)
    if not rebuild() and not (output_dir / ".zenfolio-build").is_file():
        print("❌ No successful build is available to serve. Fix the errors and restart dev.")
        return False
    watcher = DevelopmentWatcher(rebuild.watch_paths, output_dir, rebuild)
    stop = threading.Event()
    thread = threading.Thread(target=watcher.run, args=(stop,), daemon=True)
    thread.start()
    print("👀 Watching content, config, templates, and static assets. "
          "Refresh your browser after a rebuild.")
    try:
        return serve_site(
            content_dir, port, open_browser, output_dir=output_dir, host=host
        )
    finally:
        stop.set()
        rebuild.cancelled.set()
        thread.join(timeout=6)


def serve_site(
    content_dir: Path,
    port: int = 8000,
    open_browser: bool = True,
    output_dir: Path = None,
    host: str = "127.0.0.1",
) -> bool:
    """Serve the generated website locally.

    Returns True if the server ran and stopped normally, False on failure,
    so callers can propagate a meaningful exit code.
    """
    output_dir = get_output_dir(content_dir, output_dir)
    if not output_dir.exists():
        print(f"❌ Output directory {output_dir} does not exist. Run 'zenfolio build' first.")
        return False

    serve_dir = output_dir.resolve()
    handler = functools.partial(RobustHTTPRequestHandler, directory=str(serve_dir))

    # Note: ThreadedHTTPServer is IPv4-only, so IPv6 hosts like ::1 will fail
    # to bind and are reported by the OSError handler below.
    if host not in ("127.0.0.1", "localhost"):
        print(f"⚠️  Serving on {host}: the site is reachable from other machines on the network")

    try:
        with ThreadedHTTPServer((host, port), handler) as httpd:
            display_host = "localhost" if host in ("127.0.0.1", "") else host
            url = f"http://{display_host}:{port}"
            print(f"🌐 Serving website at {url}")
            print(f"📁 Serving files from {serve_dir}")
            print("🛑 Press Ctrl+C to stop the server")

            if open_browser:
                def open_browser_delayed():
                    import time
                    time.sleep(1)
                    webbrowser.open(url)

                threading.Thread(target=open_browser_delayed, daemon=True).start()

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            print(f"❌ Port {port} is already in use. Try a different port with --port")
        else:
            print(f"❌ Failed to start server: {e}")
        return False
    return True
