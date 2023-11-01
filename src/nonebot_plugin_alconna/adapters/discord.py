from datetime import datetime, timedelta
from typing import Dict, List, Type, Union, Optional

from tarina import lang
from nonebot.rule import Rule
from nonebot.adapters import Event
from nonebot.adapters.discord import Bot
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from arclet.alconna import Args, Option, Alconna, Subcommand
from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker
from nonebot.adapters.discord.commands.storage import _application_command_storage
from nonebot.adapters.discord.api.types import MessageFlag, InteractionCallbackType
from nonebot.internal.matcher.matcher import current_bot, current_event, current_matcher
from nepattern import FLOAT, NUMBER, INTEGER, AnyOne, BasePattern, PatternModel, UnionPattern
from nonebot.adapters.discord.commands.matcher import (
    SlashCommandMatcher,
    ApplicationCommandConfig,
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
    parse_message,
)
from nonebot.adapters.discord.api import (
    MessageGet,
    RoleOption,
    UserOption,
    NumberOption,
    OptionChoice,
    StringOption,
    BooleanOption,
    ChannelOption,
    IntegerOption,
    SnowflakeType,
    AnyCommandOption,
    AttachmentOption,
    SubCommandOption,
    MentionableOption,
    InteractionResponse,
    SubCommandGroupOption,
    ApplicationCommandType,
    ApplicationCommandOptionType,
    ApplicationCommandInteractionDataOption,
)

from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import Image as UniImg
from nonebot_plugin_alconna import Extension, UniMessage, log
from nonebot_plugin_alconna.matcher import _M, AlconnaMatcher

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
    if alc.prefixes != ["/"] or (
        not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")
    ):
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


class DiscordSlashExtension(Extension):
    application_command: ApplicationCommandConfig

    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "adapters.discord:DiscordSlashExtension"

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
        self.using = False

    def post_init(self, alc: Alconna) -> None:
        if alc.prefixes != ["/"] or (
            not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")
        ):
            return
        self.using = True
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
        self.application_command = config

    def validate(self, bot, event: Event) -> bool:
        if not self.using:
            return False
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return False
        if (
            event.data.name != self.application_command.name
            or event.data.type != self.application_command.type
        ):
            return False
        if not event.data.guild_id and self.application_command.guild_ids is None:
            return True
        return bool(
            event.data.guild_id
            and self.application_command.guild_ids
            and event.data.guild_id in self.application_command.guild_ids
        )

    async def message_provider(self, event: Event, state: T_State, bot, use_origin: bool = False):
        if not isinstance(event, ApplicationCommandInteractionEvent):
            return
        data = event.data
        cmd = f"/{data.name}"

        def _handle_options(options: List[ApplicationCommandInteractionDataOption]):
            for opt in options:
                if opt.type in (
                    ApplicationCommandOptionType.SUB_COMMAND,
                    ApplicationCommandOptionType.SUB_COMMAND_GROUP,
                ):
                    yield f"{opt.name}"
                    if opt.options:
                        yield from _handle_options(opt.options)
                else:
                    yield f"{opt.value}"

        if data.options:
            cmd += " "
            cmd += " ".join(_handle_options(data.options))

        return Message(cmd.rstrip())

    @classmethod
    async def send_deferred_response(cls) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.create_interaction_response(
            interaction_id=event.id,
            interaction_token=event.token,
            response=InteractionResponse(type=InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE),
        )

    @classmethod
    async def send_response(cls, message: _M, fallback: bool = False):
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        return await matcher.send(message, fallback)

    @classmethod
    async def get_response(cls) -> MessageGet:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        return await bot.get_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
        )

    async def edit_response(
        self,
        message: _M,
        fallback: bool = False,
    ) -> None:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        await bot.edit_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
            **message_data,
        )

    @classmethod
    async def delete_response(cls) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.delete_origin_interaction_response(
            application_id=bot.application_id,
            interaction_token=event.token,
        )

    async def send_followup_msg(
        self,
        message: _M,
        fallback: bool = False,
        flags: Optional[MessageFlag] = None,
    ) -> MessageGet:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        if flags:
            message_data["flags"] = int(flags)
        return await bot.create_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            **message_data,
        )

    @classmethod
    async def get_followup_msg(cls, message_id: SnowflakeType):
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        return await bot.get_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
        )

    async def edit_followup_msg(
        self,
        message_id: SnowflakeType,
        message: _M,
        fallback: bool = False,
    ) -> MessageGet:
        matcher: AlconnaMatcher = current_matcher.get()  # type: ignore
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        _message = await matcher.executor.send_wrapper(bot, event, matcher.convert(message))
        if isinstance(_message, UniMessage):
            message_data = parse_message(await _message.export(bot, fallback))  # type: ignore
        else:
            message_data = parse_message(_message)  # type: ignore
        return await bot.edit_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
            **message_data,
        )

    @classmethod
    async def delete_followup_msg(cls, message_id: SnowflakeType) -> None:
        event = current_event.get()
        bot = current_bot.get()
        if not isinstance(event, ApplicationCommandInteractionEvent) or not isinstance(bot, Bot):
            raise ValueError("Invalid event or bot")
        await bot.delete_followup_message(
            application_id=bot.application_id,
            interaction_token=event.token,
            message_id=message_id,
        )


__extension__ = DiscordSlashExtension
