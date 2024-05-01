from typing import Union, Optional
from datetime import datetime, timedelta

from tarina import lang
from nonebot.rule import Rule
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from arclet.alconna import Args, Option, Alconna, Subcommand
from nepattern import ANY, FLOAT, NUMBER, INTEGER, UnionPattern
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker
from nonebot.adapters.discord.commands.matcher import SlashCommandMatcher, on_slash_command
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

from nonebot_plugin_alconna import log
from nonebot_plugin_alconna.uniseg import At, AtAll
from nonebot_plugin_alconna.uniseg import Other, Reply
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import Image as UniImg
from nonebot_plugin_alconna.uniseg import Emoji as UniEmoji

Embed = SegmentPattern("embed", EmbedSegment, Other, MessageSegment.embed)
Sticker = SegmentPattern("sticker", StickerSegment, Other, MessageSegment.sticker)
Component = SegmentPattern("component", ComponentSegment, Other, MessageSegment.component)
Timestamp = SegmentPattern("timestamp", TimestampSegment, Other, MessageSegment.timestamp)
CustomEmoji = Emoji = SegmentPattern("emoji", CustomEmojiSegment, UniEmoji, MessageSegment.custom_emoji)
Image = SegmentPattern("attachment", AttachmentSegment, UniImg, MessageSegment.attachment)
MentionUser = SegmentPattern("mention_user", MentionUserSegment, At, MessageSegment.mention_user)
MentionChannel = SegmentPattern("mention_channel", MentionChannelSegment, At, MessageSegment.mention_channel)
MentionRole = SegmentPattern("mention_role", MentionRoleSegment, At, MessageSegment.mention_role)
MentionEveryone = SegmentPattern("mention_everyone", MentionEveryoneSegment, AtAll, MessageSegment.mention_everyone)
Reference = SegmentPattern("reference", ReferenceSegment, Reply, MessageSegment.reference)


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
        elif arg.value == ANY:
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
    if not opt.args.empty and opt.options:
        log(
            "WARNING",
            lang.require("nbp-alc", "log.discord_ambiguous_subcommand").format(name=opt.name),
        )
    if not opt.args.empty:
        return SubCommandOption(
            name=opt.name, description=opt.help_text, options=_translate_args(opt.args)  # type: ignore
        )
    return SubCommandGroupOption(
        name=opt.name,
        description=opt.help_text,
        options=[_translate_options(sub) for sub in opt.options],  # type: ignore
    )


def translate(
    alc: Alconna,
    internal_id: Optional[str] = None,
    rule: Union[Rule, T_RuleChecker, None] = None,
    permission: Union[Permission, T_PermissionChecker, None] = None,
    *,
    name_localizations: Optional[dict[str, str]] = None,
    description_localizations: Optional[dict[str, str]] = None,
    default_member_permissions: Optional[str] = None,
    dm_permission: Optional[bool] = None,
    default_permission: Optional[bool] = None,
    nsfw: Optional[bool] = None,
    handlers: Optional[list[Union[T_Handler, Dependent]]] = None,
    temp: bool = False,
    expire_time: Union[datetime, timedelta, None] = None,
    priority: int = 1,
    block: bool = True,
    state: Optional[T_State] = None,
    _depth: int = 0,
) -> type[SlashCommandMatcher]:
    if alc.prefixes != ["/"] or (not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")):
        raise ValueError(lang.require("nbp-alc", "error.discord_prefix"))
    allow_opt = [
        opt
        for opt in alc.options
        if opt.name not in set().union(*alc.namespace_config.builtin_option_name.values())  # type: ignore
    ]
    if not alc.args.empty and allow_opt:
        log(
            "WARNING",
            lang.require("nbp-alc", "log.discord_ambiguous_command").format(cmd=alc.path),
        )
    if not (options := _translate_args(alc.args)):
        options = [_translate_options(opt) for opt in allow_opt]
    buffer = {
        "name": alc.command,
        "description": alc.meta.description,
        "options": options,
        **locals(),
    }
    buffer["_depth"] += 1
    buffer.pop("alc")
    return on_slash_command(**buffer)
