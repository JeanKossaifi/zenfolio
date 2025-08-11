"""
This module contains the development server for the ZenFolio website generator.
"""
import http.server
import socketserver
import webbrowser
import threading
import functools
from pathlib import Path

from .zenfolio import get_output_dir


def kill_existing_servers():
    """Kill any existing Python HTTP servers to prevent cache issues."""
    import subprocess
    try:
        result = subprocess.run(
            ["pkill", "-f", "python -m http.server"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("🧹 Killed existing HTTP servers")
    except Exception:
        pass


class RobustHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that gracefully handles broken pipe errors"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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


def serve_site(content_dir: Path, port: int = 8000, open_browser: bool = True):
    """Serve the generated website locally"""
    output_dir = get_output_dir(content_dir)
    if not output_dir.exists():
        print(f"❌ Output directory {output_dir} does not exist. Run 'zenfolio build' first.")
        return

    kill_existing_servers()

    serve_dir = output_dir.resolve()
    handler = functools.partial(RobustHTTPRequestHandler, directory=str(serve_dir))

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
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
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port with --port")
        else:
            print(f"❌ Failed to start server: {e}")
