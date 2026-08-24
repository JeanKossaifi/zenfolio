import pytest

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
