from zenfolio.media_assets import prepare_talk_thumbnails, youtube_video_id
from zenfolio.models import TalkItem, TalksConfig


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
    talk = TalkItem(
        title="Talk",
        video="https://www.youtube.com/watch?v=cs1hOe5dVfk",
    )
    config = TalksConfig(items=[talk], cache_video_thumbnails=True)
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
    talk = TalkItem(
        title="Talk",
        video="https://youtu.be/cs1hOe5dVfk",
    )
    config = TalksConfig(items=[talk], cache_video_thumbnails=True)

    def fail_fetcher(url, timeout):
        raise OSError("offline")

    prepare_talk_thumbnails(tmp_path, config, fetcher=fail_fetcher)

    assert talk.thumbnail is None
    assert not (tmp_path / "static/images/talks/cs1hOe5dVfk.jpg").exists()
    assert "Using the theme fallback" in capsys.readouterr().out
