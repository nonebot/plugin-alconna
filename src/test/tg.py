from arclet.alconna import Args, Alconna

from nonebot_plugin_alconna.adapters.telegram import Bold, Underline

msg = "/com" + Bold("mand some_arg") + " " + Underline("some_arg") + " some_arg"

alc = Alconna(
    "/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", str]
)

print(alc.parse(msg))
print(alc.parse(msg).some_arg.type)
print(alc.parse(msg).some_arg1.type)

msg1 = "/command " + Bold("foo bar baz")

alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

print(alc1.parse(msg1))
