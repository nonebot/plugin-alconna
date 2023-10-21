from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, Card, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.message import MessageSegment


class KookMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.kaiheila.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Kaiheila"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if "markdown" in seg.style:
            return ms.KMarkdown(seg.text)
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.flag == "role":
            return ms.KMarkdown(f"(rol){seg.target}(rol)")
        elif seg.flag == "channel":
            return ms.KMarkdown(f"(chn){seg.target}(chn)")
        else:
            return ms.KMarkdown(f"(met){seg.target}(met)")

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.KMarkdown(f"(met){'here' if seg.here else 'all'}(met)")

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.name:
            return ms.KMarkdown(f"(emj){seg.name}(emj)[{seg.id}]")
        else:
            return ms.KMarkdown(f":{seg.id}:")

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila.bot import Bot as KBot

            assert isinstance(bot, KBot)
        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.audio,
            "audio": ms.audio,
            "video": ms.video,
            "file": ms.file,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)
        elif seg.path or seg.raw:
            file_key = await bot.upload_file(seg.path or seg.raw_bytes)
            return method(file_key)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def card(self, seg: Card, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "xml":
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="kook", seg=seg, target="Card")
            )
        return ms.Card(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id)
