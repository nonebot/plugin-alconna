import re
import functools
from string import Formatter
from typing_extensions import TypeAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Set,
    Dict,
    Type,
    Tuple,
    Union,
    Mapping,
    TypeVar,
    Callable,
    Optional,
    Sequence,
    cast,
)

from .segment import Segment

if TYPE_CHECKING:
    from .message import UniMessage

FormatSpecFunc: TypeAlias = Callable[[Any], str]
FormatSpecFunc_T = TypeVar("FormatSpecFunc_T", bound=FormatSpecFunc)


class UniMessageTemplate(Formatter):
    """通用消息模板格式化实现类。

    参数:
        template: 模板
        factory: 消息类型工厂，默认为 `str`
    """

    def __init__(self, template: Union[str, "UniMessage"], factory: Type["UniMessage"]) -> None:
        self.template = template
        self.factory = factory
        self.format_specs: Dict[str, FormatSpecFunc] = {}

    def __repr__(self) -> str:
        return f"UniMessageTemplate({self.template!r})"

    def add_format_spec(self, spec: FormatSpecFunc_T, name: Optional[str] = None) -> FormatSpecFunc_T:
        name = name or spec.__name__
        if name in self.format_specs:
            raise ValueError(f"Format spec {name} already exists!")
        self.format_specs[name] = spec
        return spec

    def format(self, *args, **kwargs):
        """根据传入参数和模板生成消息对象"""
        return self._format(args, kwargs)

    def format_map(self, mapping: Mapping[str, Any]):
        """根据传入字典和模板生成消息对象, 在传入字段名不是有效标识符时有用"""
        return self._format([], mapping)

    def _format(self, args: Sequence[Any], kwargs: Mapping[str, Any]):
        full_message = self.factory()
        used_args, arg_index = set(), 0

        if isinstance(self.template, str):
            msg, arg_index = self._vformat(self.template, args, kwargs, used_args, arg_index)
            full_message += msg
        elif isinstance(self.template, self.factory):
            template = cast("UniMessage[Segment]", self.template)
            for seg in template:
                if not seg.is_text():
                    full_message += seg
                else:
                    msg, arg_index = self._vformat(str(seg), args, kwargs, used_args, arg_index)
                    full_message += msg
        else:
            raise TypeError("template must be a string or instance of UniMessage!")

        self.check_unused_args(list(used_args), args, kwargs)
        return full_message

    def check_unused_args(
        self,
        used_args: Sequence[Union[str, int]],
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
    ) -> None:
        indexes = [i for i in used_args if isinstance(i, int)]
        if indexes and len(indexes) != len(args):
            raise ValueError(
                f"not all arguments converted during string formatting: "
                f"{[c for i, c in enumerate(args) if i not in indexes]}"
            )
        keys = [k for k in used_args if isinstance(k, str)]
        if keys and keys != list(kwargs.keys()):
            raise ValueError(
                f"not all arguments converted during string formatting: " f"{set(kwargs) - set(keys)}"
            )

    def _vformat(
        self,
        format_string: str,
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
        used_args: Set[Union[int, str]],
        auto_arg_index: int = 0,
    ) -> Tuple["UniMessage", int]:
        results = [self.factory()]

        for literal_text, field_name, format_spec, conversion in self.parse(format_string):
            # output the literal text
            if literal_text:
                results.append(literal_text)

            # if there's a field, output it
            if field_name or not format_spec:
                # this is some markup, find the object and do
                #  the formatting
                # handle arg indexing when empty field_names are given.
                if field_name == "":
                    if auto_arg_index is False:
                        raise ValueError(
                            "cannot switch from manual field specification to " "automatic field numbering"
                        )
                    field_name = str(auto_arg_index)
                    auto_arg_index += 1
                elif field_name.isdigit():
                    if auto_arg_index:
                        raise ValueError(
                            "cannot switch from manual field specification to " "automatic field numbering"
                        )
                    # disable auto arg incrementing, if it gets
                    # used later on, then an exception will be raised
                    auto_arg_index = False

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion) if conversion else obj

                # format the object and append to the result
                if not format_spec:
                    formatted_text = obj
                elif formatter := self.format_specs.get(format_spec):
                    formatted_text = formatter(obj)
                else:
                    for subcls in Segment.__subclasses__():
                        if format_spec == subcls.__name__:  # type: ignore
                            formatted_text = obj if isinstance(obj, subcls) else subcls(obj)  # type: ignore
                            break
                    else:
                        formatted_text = self.format_field(obj, format_spec)

                results.append(formatted_text)
            else:
                for cls in Segment.__subclasses__():
                    if not (mat := re.match(rf"{cls.__name__}\((.+)\)", format_spec)):
                        continue
                    parts = mat[1].split(",")
                    _args = []
                    _kwargs = {}
                    for part in parts:
                        if part.isdigit():
                            _args.append(args[int(part)])
                            used_args.add(int(part))
                        elif part in kwargs:
                            _kwargs[part] = kwargs[part]
                            used_args.add(part)
                        elif re.match(".+=.+", part):
                            k, v = part.split("=")
                            _kwargs[k] = v
                        else:
                            _kwargs[part] = part
                    results.append(cls(*_args, **_kwargs))  # type: ignore
                    break

        return functools.reduce(self._add, results), auto_arg_index

    def _add(self, a: Any, b: Any) -> Any:
        try:
            return a + b
        except TypeError:
            return a + str(b)
