import pytest
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebug import App

from tests.fake import fake_group_message_event_v11

MUSIC_PLATFORMS = [
    ("NeteaseCloudMusic", "163"),
    ("QQMusic", "qq"),
    ("MiguMusic", "migu"),
    ("KugouMusic", "kugou"),
    ("KuwoMusic", "kuwo"),
]


@pytest.fixture
def music_metadata() -> dict[str, str]:
    return {
        "title": "示例歌曲",
        "content": "示例歌手 | 示例专辑",
        "url": "https://example.com/song",
        "audio": "https://example.com/song.mp3",
        "thumbnail": "https://example.com/cover.jpg",
    }


@pytest.fixture
def music_data(music_metadata: dict[str, str]) -> dict[str, str]:
    return {
        "url": music_metadata["url"],
        "audio": music_metadata["audio"],
        "title": music_metadata["title"],
        "content": music_metadata["content"],
        "image": music_metadata["thumbnail"],
    }


@pytest.mark.asyncio()
@pytest.mark.parametrize(("kind", "platform"), MUSIC_PLATFORMS)
@pytest.mark.parametrize("song_id", [None, ""])
async def test_onebot_music_share_without_id(
    app: App,
    kind: str,
    platform: str,
    song_id: str | None,
    music_metadata: dict[str, str],
    music_data: dict[str, str],
):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare, MusicShareKind

    card = MusicShare(kind=MusicShareKind(kind), id=song_id, **music_metadata)
    message = await UniMessage(card).export(adapter="OneBot V11", fallback=False)

    assert message == Message(MessageSegment("music", {"type": platform, **music_data}))


@pytest.mark.asyncio()
@pytest.mark.parametrize(("kind", "platform"), [*MUSIC_PLATFORMS, ("Custom", "qq")])
async def test_onebot_music_share_with_id(app: App, kind: str, platform: str, music_metadata: dict[str, str]):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare, MusicShareKind

    card = MusicShare(kind=MusicShareKind(kind), id="123", **music_metadata)
    message = await UniMessage(card).export(adapter="OneBot V11", fallback=False)

    assert message == Message(MessageSegment.music(platform, 123))


@pytest.mark.asyncio()
@pytest.mark.parametrize("kind", ["Custom", "custom", "Unknown"])
async def test_onebot_custom_music_share(
    app: App, kind: str, music_metadata: dict[str, str], music_data: dict[str, str]
):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare, MusicShareKind

    card = MusicShare(kind=MusicShareKind(kind), **music_metadata)
    message = await UniMessage(card).export(adapter="OneBot V11", fallback=False)

    assert message == Message(MessageSegment("music", {"type": "custom", "subtype": "qq", **music_data}))


def test_music_share_requires_kind(app: App, music_metadata: dict[str, str]):
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare

    with pytest.raises(TypeError, match="kind"):
        MusicShare(**music_metadata)


@pytest.mark.asyncio()
@pytest.mark.parametrize(("url", "audio"), [(None, "https://example.com/song.mp3"), ("https://example.com/song", None)])
async def test_onebot_music_share_metadata_fallback(app: App, url: str | None, audio: str | None):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare, MusicShareKind

    card = MusicShare(kind=MusicShareKind.KuwoMusic, url=url, audio=audio, summary="示例摘要")
    message = await UniMessage(card).export(adapter="OneBot V11", fallback=False)

    assert message == Message(
        MessageSegment(
            "music",
            {
                "type": "kuwo",
                "url": url or audio,
                "audio": audio or url,
                "title": "",
                "content": "示例摘要",
                "image": "",
            },
        )
    )


@pytest.mark.asyncio()
async def test_onebot_music_share_finish(app: App, music_metadata: dict[str, str], music_data: dict[str, str]):
    from nonebot_plugin_alconna import UniMessage, on_alconna
    from nonebot_plugin_alconna.builtins.uniseg.music_share import MusicShare, MusicShareKind

    card = MusicShare(kind=MusicShareKind.KuwoMusic, **music_metadata)
    matcher = on_alconna("music")

    @matcher.handle()
    async def _():
        await matcher.finish(UniMessage([card]))

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot(base=Bot, adapter=get_adapter(Adapter))
        event = fake_group_message_event_v11(message=Message("music"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message(MessageSegment("music", {"type": "kuwo", **music_data})))
        ctx.should_finished()
