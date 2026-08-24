"""
This module contains the development server for the ZenFolio website generator.
"""
import errno
import http.server
import socketserver
import webbrowser
import threading
import functools
from pathlib import Path

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
