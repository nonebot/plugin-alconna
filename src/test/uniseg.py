from nonebot_plugin_alconna.argv import FallbackSegment
from nonebot_plugin_alconna import Text, Other, Segment, UniMessage

print(Other(FallbackSegment.text("123")))
print(Segment())
print(Text("123"))
print(UniMessage([Other(FallbackSegment.text("123")), Segment(), Text("123")]))
print(repr(UniMessage([Other(FallbackSegment.text("123")), Segment(), Text("123")])))

print(UniMessage.template("{} {}").format("hello", Other(FallbackSegment.text("123"))))

print(repr(UniMessage.template("{:Emoji(0)}").format("123")))
