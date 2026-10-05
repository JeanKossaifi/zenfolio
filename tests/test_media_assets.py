from zenfolio.media_assets import prepare_talk_thumbnails, youtube_video_id
from zenfolio.models import TalkConfig, TalksConfig
from pathlib import Path
import shutil

import pytest


def test_youtube_video_id_supports_common_urls():
    assert (
        youtube_video_id("https://www.youtube.com/watch?v=cs1hOe5dVfk&t=5")
        == "cs1hOe5dVfk"
    )
    assert youtube_video_id("https://youtu.be/cs1hOe5dVfk") == "cs1hOe5dVfk"
    assert (
        youtube_video_id("https://youtube.com/embed/cs1hOe5dVfk")
        == "cs1hOe5dVfk"
    )
    assert youtube_video_id("https://example.com/video") is None


def test_prepare_talk_thumbnails_fetches_once_and_reuses_cache(tmp_path):
    talk = TalkConfig(
        title="TalkConfig",
        video="https://www.youtube.com/watch?v=cs1hOe5dVfk",
    )
    config = TalksConfig(talks=[talk], cache_video_thumbnails=True)
    calls = []

    def fetcher(url, timeout):
        calls.append((url, timeout))
        return b"\xff\xd8cached-jpeg"

    prepare_talk_thumbnails(tmp_path, config, fetcher=fetcher)

    target = tmp_path / "static/images/talks/cs1hOe5dVfk.jpg"
    assert target.read_bytes() == b"\xff\xd8cached-jpeg"
    assert talk.thumbnail == "images/talks/cs1hOe5dVfk.jpg"
    assert len(calls) == 1

    talk.thumbnail = None
    prepare_talk_thumbnails(
        tmp_path,
        config,
        fetcher=lambda *_: (_ for _ in ()).throw(AssertionError("refetched")),
    )

    assert talk.thumbnail == "images/talks/cs1hOe5dVfk.jpg"


def test_prepare_talk_thumbnails_leaves_fallback_on_download_failure(
    tmp_path, capsys
):
    talk = TalkConfig(
        title="TalkConfig",
        video="https://youtu.be/cs1hOe5dVfk",
    )
    config = TalksConfig(talks=[talk], cache_video_thumbnails=True)

    def fail_fetcher(url, timeout):
        raise OSError("offline")

    prepare_talk_thumbnails(tmp_path, config, fetcher=fail_fetcher)

    assert talk.thumbnail is None
    assert not (tmp_path / "static/images/talks/cs1hOe5dVfk.jpg").exists()
    assert "Using the theme fallback" in capsys.readouterr().out


@pytest.mark.parametrize("absolute", [False, True])
def test_build_reuses_thumbnails_from_configured_static_directory(tmp_path, absolute):
    from zenfolio.zenfolio import ZenFolio

    content = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/personal", content)
    assets = tmp_path / "external-assets" if absolute else content / "assets"
    (content / "static").rename(assets)
    thumbnail = assets / "images/talks/cs1hOe5dVfk.jpg"
    thumbnail.parent.mkdir(parents=True)
    thumbnail.write_bytes(b"\xff\xd8cached-jpeg")
    config_path = str(assets) if absolute else "assets"
    with (content / "config.py").open("a", encoding="utf-8") as config:
        config.write(f"\nconfig.static_path = {config_path!r}\n")
        config.write('''
from zenfolio.models import TalkConfig, TalksConfig
config.talks = TalksConfig(talks=[TalkConfig(
    title="Cached talk", video="https://youtu.be/cs1hOe5dVfk"
)])
''')
    builder = ZenFolio(content)
    assert builder.build()
    assert builder.config.talks.talks[0].thumbnail == "images/talks/cs1hOe5dVfk.jpg"
    assert (builder.output_dir / "static/images/talks/cs1hOe5dVfk.jpg").read_bytes() == thumbnail.read_bytes()
    assert not (content / "static").exists()


def test_thumbnail_download_uses_configured_static_directory(tmp_path):
    assets = tmp_path / "custom-assets"
    talk = TalkConfig(title="TalkConfig", video="https://youtu.be/cs1hOe5dVfk")
    config = TalksConfig(talks=[talk], cache_video_thumbnails=True)
    prepare_talk_thumbnails(
        tmp_path,
        config,
        static_dir=assets,
        fetcher=lambda *_: b"\xff\xd8downloaded-jpeg",
    )
    assert (assets / "images/talks/cs1hOe5dVfk.jpg").read_bytes() == b"\xff\xd8downloaded-jpeg"
    assert not (tmp_path / "static").exists()
