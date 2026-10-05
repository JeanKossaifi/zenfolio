import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

from zenfolio.server import DevelopmentBuilder, DevelopmentWatcher, _dev_build


def test_watcher_debounces_edits_and_retries_after_failed_build(tmp_path):
    source = tmp_path / "config.py"
    source.write_text("first", encoding="utf-8")
    outcomes = iter([False, True])
    builds = []

    def rebuild():
        builds.append(source.read_text())
        return next(outcomes)

    watcher = DevelopmentWatcher([tmp_path], tmp_path / "_site", rebuild)
    source.write_text("second edit", encoding="utf-8")
    assert watcher.poll(0) is None
    source.write_text("third edit, settled", encoding="utf-8")
    assert watcher.poll(0.2) is None
    assert watcher.poll(0.5) is None
    assert watcher.poll(0.7) is False
    assert watcher.poll(1.5) is None
    source.write_text("corrected edit", encoding="utf-8")
    assert watcher.poll(2) is None
    assert watcher.poll(2.5) is True
    assert builds == ["third edit, settled", "corrected edit"]


def test_watcher_tracks_new_deleted_content_and_external_assets(tmp_path):
    content = tmp_path / "content"
    external = tmp_path / "external-static"
    content.mkdir()
    external.mkdir()
    builds = []
    watcher = DevelopmentWatcher(
        [content, external], content / "_site", lambda: builds.append(True) or True
    )
    page = content / "pages" / "new.md"
    page.parent.mkdir()
    page.write_text("new page", encoding="utf-8")
    assert watcher.poll(0) is None
    assert watcher.poll(0.5) is True
    page.unlink()
    assert watcher.poll(1) is None
    assert watcher.poll(1.5) is True
    (external / "photo.svg").write_text("new asset", encoding="utf-8")
    assert watcher.poll(2) is None
    assert watcher.poll(2.5) is True
    assert len(builds) == 3


def test_watcher_ignores_outputs_and_dependency_caches(tmp_path):
    css = tmp_path / "themes" / "local" / "css"
    css.mkdir(parents=True)
    (css / "input.css").write_text("body {}", encoding="utf-8")
    (css.parent / "package.json").write_text('{"scripts": {"build": "compile"}}')
    watcher = DevelopmentWatcher([tmp_path], tmp_path / "_site", lambda: True)
    for directory in ["_site", ".git", "node_modules", "__pycache__",
                      ".pytest_cache", ".cache", ".site.zenfolio-stage-123",
                      ".site.zenfolio-backup-123"]:
        folder = tmp_path / directory
        folder.mkdir()
        (folder / "generated.txt").write_text("ignore", encoding="utf-8")
    (css / "theme.css").write_text("compiled", encoding="utf-8")
    (css / ".input.sha256").write_text("digest", encoding="utf-8")
    assert watcher.poll(0) is None
    assert watcher.poll(1) is None
    (css / "input.css").write_text("body {color: red}", encoding="utf-8")
    assert watcher.poll(2) is None
    assert watcher.poll(2.5) is True


def test_watcher_tracks_theme_css_without_a_compiler(tmp_path):
    css = tmp_path / "css"
    css.mkdir()
    (css / "input.css").write_text("body {}", encoding="utf-8")
    watcher = DevelopmentWatcher([tmp_path], tmp_path / "_site", lambda: True)
    (css / "theme.css").write_text("body {color:red}", encoding="utf-8")
    assert watcher.poll(0) is None
    assert watcher.poll(0.5) is True


def test_dev_reloads_imported_config_after_same_size_same_timestamp_edit(tmp_path):
    source = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures" / "personal", source)
    config = source / "config.py"
    config.write_text(
        config.read_text() + "\nfrom .settings import title\nconfig.site.title = title\n",
        encoding="utf-8",
    )
    settings = source / "settings.py"
    settings.write_text('title = "First title"\n', encoding="utf-8")
    timestamp = settings.stat().st_mtime_ns
    output = tmp_path / "output"
    builder = DevelopmentBuilder(source, output)
    assert builder()
    first = (output / "index.html").read_text()
    assert "First title" in first
    settings.write_text('title = "Other title"\n', encoding="utf-8")
    os.utime(settings, ns=(timestamp, timestamp))
    assert builder()
    assert "Other title" in (output / "index.html").read_text()
    config.write_text("invalid Python syntax!", encoding="utf-8")
    previous = (output / "index.html").read_bytes()
    assert builder() is False
    assert (output / "index.html").read_bytes() == previous


def test_dev_build_runs_local_theme_script_before_site_generation(tmp_path, monkeypatch):
    import zenfolio.server as server
    from zenfolio.build_context import BuildContext
    from zenfolio.themes import LocalTheme
    import zenfolio.zenfolio as facade

    theme_dir = tmp_path / "theme"
    theme_dir.mkdir()
    (theme_dir / "package.json").write_text(
        '{"scripts": {"build:css": "compile css", "build": "compile all"}}',
        encoding="utf-8",
    )
    theme = object.__new__(LocalTheme)
    theme.theme_dir = theme_dir
    context = SimpleNamespace(content_dir=tmp_path, static_dir=tmp_path / "static", theme=theme)
    monkeypatch.setattr(BuildContext, "create", lambda *args: context)
    monkeypatch.setattr(server.shutil, "which", lambda name: "/tools/npm")
    calls = []
    monkeypatch.setattr(server.subprocess, "run", lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(facade, "build_site", lambda *args, **kwargs: calls.append("site") or True)
    metadata = tmp_path / "watch.json"
    assert _dev_build(str(tmp_path), str(tmp_path / "out"), None, False, str(metadata))
    assert calls == [["/tools/npm", "run", "build:css"], "site"]
    assert str(theme_dir) in metadata.read_text()


def test_css_failure_prevents_site_publication(tmp_path, monkeypatch):
    import zenfolio.server as server
    from zenfolio.build_context import BuildContext
    from zenfolio.themes import LocalTheme
    import zenfolio.zenfolio as facade

    (tmp_path / "package.json").write_text('{"scripts": {"build": "broken"}}')
    theme = object.__new__(LocalTheme)
    theme.theme_dir = tmp_path
    context = SimpleNamespace(content_dir=tmp_path, static_dir=tmp_path / "static", theme=theme)
    monkeypatch.setattr(BuildContext, "create", lambda *args: context)
    monkeypatch.setattr(server.shutil, "which", lambda name: "/tools/npm")

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "npm")

    monkeypatch.setattr(server.subprocess, "run", fail)
    monkeypatch.setattr(facade, "build_site", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not build")))
    assert not _dev_build(str(tmp_path), str(tmp_path / "out"), None, False, str(tmp_path / "watch.json"))
    assert str(tmp_path) in (tmp_path / "watch.json").read_text()


def test_stopping_dev_interrupts_an_in_progress_worker():
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; print('ready', flush=True); time.sleep(60)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name == "posix",
    )
    try:
        assert process.stdout.readline() == b"ready\n"
        DevelopmentBuilder._stop_process(process)
        assert process.poll() is not None
        assert process.returncode != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()
