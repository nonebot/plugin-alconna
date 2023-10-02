# OutputType = Literal["help", "shortcut", "completion"]
# TConvert: TypeAlias = Callable[
#     [OutputType, str], Union[Message, UniMessage, Awaitable[Union[Message, UniMessage]]]
# ]

# TProvider: TypeAlias = Callable[
#     ["AlconnaRule", Event, T_State, Bot],
#     Union[Message, UniMessage, None, Awaitable[Union[Message, UniMessage, None]]],
# ]
