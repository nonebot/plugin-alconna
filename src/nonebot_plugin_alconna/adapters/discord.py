from datetime import datetime, timedelta
from typing import Dict, List, Type, Union, Optional

from nonebot.rule import Rule
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from nonebot.adapters import Message as BaseMessage
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker
from nonebot.adapters.discord.commands.matcher import SlashCommandMatcher, on_slash_command
from nepattern import FLOAT, NUMBER, INTEGER, AnyOne, BasePattern, PatternModel, UnionPattern
from arclet.alconna import Args, Option, Alconna, Subcommand, argv_config, set_default_argv_type
from nonebot.adapters.discord.api import (
    RoleOption,
    UserOption,
    NumberOption,
    OptionChoice,
    StringOption,
    BooleanOption,
    ChannelOption,
    IntegerOption,
    AnyCommandOption,
    AttachmentOption,
    SubCommandOption,
    MentionableOption,
    SubCommandGroupOption,
)
from nonebot.adapters.discord.message import (
    Message,
    EmbedSegment,
    MessageSegment,
    StickerSegment,
    ComponentSegment,
    ReferenceSegment,
    TimestampSegment,
    AttachmentSegment,
    CustomEmojiSegment,
    MentionRoleSegment,
    MentionUserSegment,
    MentionChannelSegment,
    MentionEveryoneSegment,
)

from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import Image as UniImg


class DiscordMessageArgv(MessageArgv):
    ...


set_default_argv_type(DiscordMessageArgv)
argv_config(
    DiscordMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)


Text = str
Embed = SegmentPattern("embed", EmbedSegment, MessageSegment.embed)
Sticker = SegmentPattern("sticker", StickerSegment, MessageSegment.sticker)
Component = SegmentPattern("component", ComponentSegment, MessageSegment.component)
Timestamp = SegmentPattern("timestamp", TimestampSegment, MessageSegment.timestamp)
Emoji = SegmentPattern("emoji", CustomEmojiSegment, MessageSegment.custom_emoji)
Image = SegmentPattern("attachment", AttachmentSegment, MessageSegment.attachment)
MentionUser = SegmentPattern("mention_user", MentionUserSegment, MessageSegment.mention_user)
MentionChannel = SegmentPattern("mention_channel", MentionChannelSegment, MessageSegment.mention_channel)
MentionRole = SegmentPattern("mention_role", MentionRoleSegment, MessageSegment.mention_role)
MentionEveryone = SegmentPattern("mention_everyone", MentionEveryoneSegment, MessageSegment.mention_everyone)
Reference = SegmentPattern("reference", ReferenceSegment, MessageSegment.reference)


MentionID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="MentionUser",
                accepts=[MentionUser],
                converter=lambda _, x: int(x.data["user_id"]),
            ),
            BasePattern(
                r"@(\d+)",
                model=PatternModel.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=[str],
                converter=lambda _, x: int(x[1]),
            ),
            INTEGER,
        ]
    )
    @ "mention_id"
)
"""
内置类型，允许传入提醒元素(Mention)或者'@xxxx'式样的字符串或者数字, 返回数字
"""


def _translate_args(args: Args) -> list[AnyCommandOption]:
    result = []
    for arg in args:
        if isinstance(arg.value, UnionPattern):
            if all(isinstance(x, str) for x in arg.value.base):
                result.append(
                    StringOption(
                        name=arg.name,
                        description=arg.notice or arg.name,
                        required=not arg.optional,
                        choices=[OptionChoice(name=x, value=x) for x in arg.value.base],  # type: ignore  # noqa: E501
                    )
                )
            elif all(isinstance(x, int) for x in arg.value.base):
                result.append(
                    IntegerOption(
                        name=arg.name,
                        description=arg.notice or arg.name,
                        required=not arg.optional,
                        choices=[
                            OptionChoice(name=str(x), value=x) for x in arg.value.base  # type: ignore  # noqa: E501
                        ],
                    )
                )
            elif all(isinstance(x, float) for x in arg.value.base):
                result.append(
                    NumberOption(
                        name=arg.name,
                        description=arg.notice or arg.name,
                        required=not arg.optional,
                        choices=[
                            OptionChoice(name=str(x), value=x) for x in arg.value.base  # type: ignore  # noqa: E501
                        ],
                    )
                )
            else:
                result.append(
                    StringOption(
                        name=arg.name,
                        description=arg.notice or arg.name,
                        required=not arg.optional,
                        choices=[OptionChoice(name=str(x), value=str(x)) for x in arg.value.base],
                    )
                )
            continue
        elif arg.value == AnyOne:
            result.append(
                StringOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value == INTEGER:
            result.append(
                IntegerOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value in (FLOAT, NUMBER):
            result.append(
                NumberOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value.origin is str:
            result.append(
                StringOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value.origin is bool:
            result.append(
                BooleanOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value == Image or arg.value.origin == UniImg:
            result.append(
                AttachmentOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value == MentionUser:
            result.append(
                UserOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value == MentionChannel:
            result.append(
                ChannelOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value == MentionRole:
            result.append(
                RoleOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        elif arg.value.origin is At:
            result.append(
                MentionableOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
        else:
            result.append(
                StringOption(
                    name=arg.name,
                    description=arg.notice or arg.name,
                    required=not arg.optional,
                )
            )
    return result


def _translate_options(opt: Union[Option, Subcommand]) -> Union[SubCommandGroupOption, SubCommandOption]:
    if isinstance(opt, Option):
        return SubCommandOption(
            name=opt.name,
            description=opt.help_text,
            options=_translate_args(opt.args),  # type: ignore
        )
    res = SubCommandGroupOption(
        name=opt.name,
        description=opt.help_text,
        options=[_translate_options(sub) for sub in opt.options],  # type: ignore
    )
    res.options.extend(_translate_args(opt.args))  # type: ignore
    return res


def translate(
    alc: Alconna,
    internal_id: Optional[str] = None,
    rule: Union[Rule, T_RuleChecker, None] = None,
    permission: Union[Permission, T_PermissionChecker, None] = None,
    *,
    name_localizations: Optional[Dict[str, str]] = None,
    description_localizations: Optional[Dict[str, str]] = None,
    default_member_permissions: Optional[str] = None,
    dm_permission: Optional[bool] = None,
    default_permission: Optional[bool] = None,
    nsfw: Optional[bool] = None,
    handlers: Optional[List[Union[T_Handler, Dependent]]] = None,
    temp: bool = False,
    expire_time: Union[datetime, timedelta, None] = None,
    priority: int = 1,
    block: bool = True,
    state: Optional[T_State] = None,
    _depth: int = 0,
) -> Type[SlashCommandMatcher]:
    buffer = {
        "name": alc.command,
        "description": alc.meta.description,
        "options": [_translate_options(opt) for opt in alc.options],
        **locals(),
    }
    buffer["_depth"] += 1
    buffer.pop("alc")
    buffer["options"].extend(_translate_args(alc.args))
    return on_slash_command(**buffer)
