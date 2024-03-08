import re
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.kaiheila.message import Card
from nonebot.adapters.kaiheila.message import Quote
from nonebot.adapters.kaiheila import Bot as KaiheilaBot
from nonebot.adapters.kaiheila.event import MessageEvent
from nonebot.adapters.kaiheila.message import File as FileSegment
from nonebot.adapters.kaiheila.message import Audio as AudioSegment
from nonebot.adapters.kaiheila.message import Image as ImageSegment
from nonebot.adapters.kaiheila.message import Video as VideoSegment
from nonebot.adapters.kaiheila.message import Mention, KMarkdown, MentionAll, MentionHere, MentionRole, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Emoji, Hyper, Image, Reply, Video

CHN = re.compile(r"\(chn\)(?P<id>.+?)\(chn\)")
EMJ = re.compile(r"\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]")
EMJ1 = re.compile(r":(?P<id>.+?):")
NO_CHN = re.compile(r"\[\(chn\)(?P<id>.+?)\(chn\)\]\(.+\)")
NO_EMJ = re.compile(r"\[\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]\]\(.+\)")
NO_EMJ1 = re.compile(r"\[:(?P<id>.+?):\]\(.+\)")


class KookMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kook

    def preprocess(self, source: Message[MessageSegment]) -> Message[MessageSegment]:
        res = source.__class__()
        for index, unit in enumerate(source):
            if not unit.is_text():
                res.append(unit)
                continue
            if unit.type == "text":
                text = unit.data["text"]
                if not text.strip():
                    if not index or index == len(source) - 1:
                        continue
                    if not (source[index - 1]).is_text() or not (source[index + 1]).is_text():
                        continue
                if res and res[-1].type == "text":
                    res[-1].data["text"] = f"{res[-1].data['text']}{text}"
                else:
                    res.append(unit)
                continue
            if TYPE_CHECKING:
                assert isinstance(unit, KMarkdown)
            content = unit.data["content"]
            mats = {}
            spans = {}
            for mat in CHN.finditer(content):
                mats[mat.start()] = MessageSegment("mention_channel", {"channel_id": mat.group("id")})
                spans[mat.start()] = mat.end()
            for mat in EMJ.finditer(content):
                mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id"), "name": mat.group("name")})
                spans[mat.start()] = mat.end()
            for mat in EMJ1.finditer(content):
                mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id")})
                spans[mat.start()] = mat.end()
            for mat in NO_CHN.finditer(content):
                if mat.start() + 1 in spans:
                    del spans[mat.start() + 1]
                    del mats[mat.start() + 1]
            for mat in NO_EMJ.finditer(content):
                if mat.start() + 1 in spans:
                    del spans[mat.start() + 1]
                    del mats[mat.start() + 1]
            for mat in NO_EMJ1.finditer(content):
                if mat.start() + 1 in spans:
                    del spans[mat.start() + 1]
                    del mats[mat.start() + 1]
            if not mats:
                res.append(MessageSegment.KMarkdown(content))
                continue
            text = ""
            in_mat = False
            current = 0
            for _index, char in enumerate(content):
                if _index in spans:
                    in_mat = True
                    current = _index
                    if text:
                        res.append(MessageSegment.text(text))
                        text = ""
                    res.append(mats[_index])
                    continue
                if _index >= spans[current]:
                    in_mat = False
                if not in_mat:
                    text += char
            if text:
                res.append(MessageSegment.text(text))
        return res

    @build("kmarkdown")
    def kmarkdown(self, seg: KMarkdown):
        content = seg.data["content"]
        if content.startswith("(met)") and (end := content.find("(met)", 5)) >= 0:
            user_id = content[5:end]
            if user_id not in ("here", "all"):
                return At("user", user_id)
            return AtAll(user_id == "here")
        if content.startswith("(emj)"):
            mat = re.search(r"\(emj\)(?P<name>[^()\[\]]+)\(emj\)\[(?P<id>[^\[\]]+)\]", content)
            if mat:
                return Emoji(mat["id"], mat["name"])
        if content.startswith(":") and (mat := re.search(r":(?P<id>[^:]+):", content)):
            return Emoji(mat["id"])
        return Text(seg.data["content"]).mark(0, len(seg.data["content"]), "markdown")

    @build("mention")
    def mention(self, seg: Mention):
        return At("user", str(seg.data["user_id"]))

    @build("mention_channel")
    def mention_channel(self, seg: MessageSegment):
        return At("channel", str(seg.data["channel_id"]))

    @build("mention_role")
    def mention_role(self, seg: MentionRole):
        return At("role", str(seg.data["role_id"]))

    @build("mention_all")
    def mention_all(self, seg: MentionAll):
        return AtAll()

    @build("mention_here")
    def mention_here(self, seg: MentionHere):
        return AtAll(True)

    @build("emoji")
    def emoji(self, seg: MessageSegment):
        if "name" in seg.data:
            return Emoji(seg.data["id"], seg.data["name"])
        return Emoji(seg.data["id"])

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(url=seg.data["file_key"])

    @build("video")
    def video(self, seg: VideoSegment):
        return Video(url=seg.data["file_key"])

    @build("audio")
    def audio(self, seg: AudioSegment):
        return Audio(url=seg.data["file_key"])

    @build("file")
    def file(self, seg: FileSegment):
        return File(
            id=seg.data["file_key"],
            name=seg.data.get("file_name", seg.data.get("title")),
        )

    @build("quote")
    def quote(self, seg: Quote):
        return Reply(seg.data["msg_id"], origin=seg)

    @build("card")
    def card(self, seg: Card):
        return Hyper("json", seg.data["content"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
            assert isinstance(bot, KaiheilaBot)

        api = "directMessage_view" if event.__event__ == "message.private" else "message_view"
        message = await bot.call_api(
            api,
            msg_id=event.msg_id,
            **({"chat_code": event.event.code} if event.__event__ == "message.private" else {}),
        )
        if message.quote:
            return Reply(message.quote.id_, origin=message.quote)
