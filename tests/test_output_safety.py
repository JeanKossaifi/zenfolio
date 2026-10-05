import pytest
from pathlib import Path

from zenfolio.zenfolio import ZenFolio, ZenFolioBuildError


@pytest.mark.parametrize("target", ["content", "parent", "static"])
def test_rejects_unsafe_output_directories(personal_site_root, target):
    builder = ZenFolio(personal_site_root)
    targets = {
        "content": builder.content_dir,
        "parent": builder.content_dir.parent,
        "static": builder.static_dir,
    }
    builder.output_dir = targets[target]

    with pytest.raises(ZenFolioBuildError):
        builder._validate_output_directory()


def test_accepts_output_below_content_root(personal_site_root):
    builder = ZenFolio(personal_site_root)
    builder.output_dir = builder.content_dir / "_safe-output"

    builder._validate_output_directory()


def test_resolves_symlink_before_safety_check(personal_site_root):
    builder = ZenFolio(personal_site_root)
    symlink = builder.content_dir.parent / "output-link"
    symlink.symlink_to(builder.content_dir, target_is_directory=True)
    builder.output_dir = symlink

    with pytest.raises(ZenFolioBuildError):
        builder._validate_output_directory()


def test_refuses_existing_unmarked_output_directory(personal_site_root):
    builder = ZenFolio(personal_site_root)
    unrelated = builder.content_dir.parent / "other-project"
    unrelated.mkdir()
    (unrelated / "keep.txt").write_text("user data", encoding="utf-8")
    builder.output_dir = unrelated

    with pytest.raises(ZenFolioBuildError):
        builder._validate_output_directory()


def _files(directory):
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize("failure_stage", ["assets", "pages", "sitemap"])
def test_failed_rebuild_preserves_previous_output(
    personal_site_root, tmp_path, monkeypatch, failure_stage
):
    output = tmp_path / "site"
    builder = ZenFolio(personal_site_root, output_override=output)
    assert builder.build()
    previous = _files(output)

    def fail(*args, **kwargs):
        raise RuntimeError("deliberate build failure")

    if failure_stage == "assets":
        monkeypatch.setattr(builder.theme, "write_css_file", fail)
    else:
        method = "_build_pages" if failure_stage == "pages" else "_generate_sitemap"
        monkeypatch.setattr(builder, method, fail)
    with pytest.raises(RuntimeError, match="deliberate build failure"):
        builder.build()

    assert _files(output) == previous
    assert builder.output_dir == output
    assert builder.output_manager.output_dir == output
    assert builder.page_renderer.output_dir == output
    assert not list(tmp_path.glob(".site.zenfolio-*"))


def test_failed_first_build_does_not_publish_partial_site(
    personal_site_root, tmp_path, monkeypatch
):
    output = tmp_path / "site"
    builder = ZenFolio(personal_site_root, output_override=output)

    def fail(*args, **kwargs):
        raise RuntimeError("bad template")

    monkeypatch.setattr(builder, "_build_pages", fail)
    with pytest.raises(RuntimeError, match="bad template"):
        builder.build()
    assert not output.exists()
    assert not list(tmp_path.glob(".site.zenfolio-*"))


def test_failed_publication_restores_previous_output(
    personal_site_root, tmp_path, monkeypatch
):
    output = tmp_path / "site"
    builder = ZenFolio(personal_site_root, output_override=output)
    assert builder.build()
    previous = _files(output)
    replace = Path.replace

    def fail_staging_swap(path, target):
        if path.name.startswith(".site.zenfolio-stage-"):
            raise OSError("deliberate rename failure")
        return replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_staging_swap)
    with pytest.raises(OSError, match="deliberate rename failure"):
        builder.build()
    assert _files(output) == previous
    assert not list(tmp_path.glob(".site.zenfolio-*"))


def test_successful_rebuild_replaces_stale_files_and_keeps_override(
    personal_site_root, tmp_path
):
    output = tmp_path / "custom-output"
    builder = ZenFolio(personal_site_root, output_override=output)
    assert builder.build()
    (output / "stale.html").write_text("old page", encoding="utf-8")
    assert builder.build()
    assert (output / "index.html").is_file()
    assert (output / ".zenfolio-build").is_file()
    assert not (output / "stale.html").exists()
    assert builder.output_dir == output
    assert not list(tmp_path.glob(".custom-output.zenfolio-*"))


def test_publication_rechecks_destination_safety(personal_site_root, tmp_path):
    output = tmp_path / "site"
    builder = ZenFolio(personal_site_root, output_override=output)
    with pytest.raises(ZenFolioBuildError, match="not marked"):
        with builder.output_manager.staging() as staged:
            staged.reset()
            output.mkdir()
            (output / "user-data.txt").write_text("keep me", encoding="utf-8")
    assert (output / "user-data.txt").read_text() == "keep me"
    assert not list(tmp_path.glob(".site.zenfolio-*"))
