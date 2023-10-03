from datetime import datetime, timedelta
from typing import Dict, List, Type, Union, Optional

from nonebot.rule import Rule
from tarina.const import Empty
from nonebot.adapters import Event
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from arclet.alconna import Args, Option, Alconna, Subcommand
from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker
from nonebot.adapters.discord.commands.storage import _application_command_storage
from nepattern import FLOAT, NUMBER, INTEGER, AnyOne, BasePattern, PatternModel, UnionPattern
from nonebot.adapters.discord.commands.matcher import (
    SlashCommandMatcher,
    ApplicationCommandConfig,
    ApplicationCommandMatcher,
    on_slash_command,
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
    ApplicationCommandType,
    ApplicationCommandOptionType,
    ApplicationCommandInteractionDataOption,
)

from nonebot_plugin_alconna import Extension
from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import Image as UniImg

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


def _translate_args(args: Args) -> List[AnyCommandOption]:
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
    if opt.args is not Empty:
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


class DiscordExtension(Extension, ApplicationCommandMatcher):
    priority = 10
    application_command: ApplicationCommandConfig

    def __init__(
        self,
        internal_id: Optional[str] = None,
        name_localizations: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        description_localizations: Optional[Dict[str, str]] = None,
        default_member_permissions: Optional[str] = None,
        dm_permission: Optional[bool] = None,
        default_permission: Optional[bool] = None,
        nsfw: Optional[bool] = None,
    ):
        self.internal_id = internal_id
        self.name_localizations = name_localizations
        self.description = description
        self.description_localizations = description_localizations
        self.default_member_permissions = default_member_permissions
        self.dm_permission = dm_permission
        self.default_permission = default_permission
        self.nsfw = nsfw
        super().__init__()

    def post_init(self, alc: Alconna) -> None:
        if not (options := _translate_args(alc.args)):
            options = [
                _translate_options(opt)
                for opt in alc.options
                if opt.name not in alc.namespace_config.builtin_option_name
            ]
        config = ApplicationCommandConfig(
            type=ApplicationCommandType.CHAT_INPUT,
            name=alc.command,
            name_localizations=self.name_localizations,
            description=self.description or alc.meta.description,
            description_localizations=self.description_localizations,
            options=options,  # type: ignore
            default_member_permissions=self.default_member_permissions,
            dm_permission=self.dm_permission,
            default_permission=self.default_permission,
            nsfw=self.nsfw,
        )
        _application_command_storage[self.internal_id or config.name] = config
        self.config = config

    def validate(self, bot, event: Event) -> bool:
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return False
        if event.data.name != self.config.name or event.data.type != self.config.type:
            return False
        if not event.data.guild_id and self.config.guild_ids is None:
            return True
        return event.data.guild_id and self.config.guild_ids and event.data.guild_id in self.config.guild_ids

    async def message_provider(self, event: Event, state: T_State, bot, use_origin: bool = False):
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return
        data = event.data
        cmd = f"/{data.name}"

        def _handle_option(opt: ApplicationCommandInteractionDataOption):
            if opt.type in (
                ApplicationCommandOptionType.SUB_COMMAND,
                ApplicationCommandOptionType.SUB_COMMAND_GROUP,
            ):
                yield f"{opt.name}"
                if opt.options:
                    for o in opt.options:
                        yield from _handle_option(o)
            else:
                yield f"{opt.value}"

        if data.options:
            cmd += " "
            for opt in data.options:
                cmd += " ".join(_handle_option(opt)) + " "
        return Message(cmd.rstrip())
