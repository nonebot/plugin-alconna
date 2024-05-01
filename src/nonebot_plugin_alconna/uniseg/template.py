import re
import functools
from string import Formatter
from typing_extensions import TypeAlias
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Union, TypeVar, Callable, Optional, cast

import _string  # type: ignore
from tarina.tools import gen_subclass

from .segment import Segment

if TYPE_CHECKING:
    from .message import UniMessage

FormatSpecFunc: TypeAlias = Callable[[Any], str]
FormatSpecFunc_T = TypeVar("FormatSpecFunc_T", bound=FormatSpecFunc)

_MAPPING = {cls.__name__: cls for cls in gen_subclass(Segment)}
_PATTERN = re.compile("(" + "|".join(_MAPPING.keys()) + r")\((.*)\)$")


def _eval(route: str, obj: Any):
    res = obj
    parts = re.split(r"\.|(\[.+\])|(\(.*\))", route)
    for part in parts[1:]:
        if not part:
            continue
        if part.startswith("_"):
            raise ValueError(route)
        if part.startswith("[") and part.endswith("]"):
            item = part[1:-1]
            if item[0] in ("'", '"') and item[-1] in ("'", '"'):
                res = res[item[1:-1]]
            elif ":" in item:
                res = res[slice(*(int(x) if x else None for x in item.split(":")))]
            else:
                res = res[int(item)]
        elif part.startswith("(") and part.endswith(")"):
            item = part[1:-1]
            if not item:
                res = res()
            else:
                _parts = item.split(",")
                _args = []
                _kwargs = {}
                for part in _parts:
                    part = part.strip()
                    if re.match(".+=.+", part):
                        k, v = part.split("=")
                        _kwargs[k] = v
                    else:
                        _args.append(part)
                res = res(*_args, **_kwargs)
        else:
            res = getattr(res, part)
    return res


class UniMessageTemplate(Formatter):
    """通用消息模板格式化实现类。

    参数:
        template: 模板
        factory: 消息类型工厂，默认为 `str`
    """

    def __init__(self, template: Union[str, "UniMessage[Any]"], factory: type["UniMessage[Any]"]) -> None:
        self.template = template
        self.factory = factory
        self.format_specs: dict[str, FormatSpecFunc] = {}

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

        # self.check_unused_args(used_args, args, kwargs)
        return full_message

    # def check_unused_args(
    #     self,
    #     used_args: Sequence[Union[str, int]],
    #     args: Sequence[Any],
    #     kwargs: Mapping[str, Any],
    # ) -> None:
    #     indexes = [i for i in used_args if isinstance(i, int)]
    #     if indexes and len(indexes) != len(args):
    #         raise ValueError(
    #             f"not all arguments converted during string formatting: "
    #             f"{[c for i, c in enumerate(args) if i not in indexes]}"
    #         )
    #     keys = [k for k in used_args if isinstance(k, str)]
    #     if keys and keys != list(kwargs.keys()):
    #         raise ValueError(
    #             f"not all arguments converted during string formatting: " f"{set(kwargs) - set(keys)}"
    #         )

    def _vformat(
        self,
        format_string: str,
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
        used_args: set[Union[int, str]],
        auto_arg_index: int = 0,
    ) -> tuple["UniMessage", int]:
        results: list = [self.factory()]

        for literal_text, field_name, format_spec, conversion in self.parse(format_string):
            # output the literal text
            if literal_text:
                results.append(literal_text)

            # if there's a field, output it
            if field_name is not None:
                if field_name == "" and format_spec and (mat := _PATTERN.match(format_spec)):
                    cls, parts = _MAPPING[mat[1]], mat[2].split(",")
                    _args = []
                    _kwargs = {}
                    for part in parts:
                        part = part.strip()
                        if part.startswith("$") and (key := part.split(".")[0]) in kwargs:
                            _args.append(_eval(part[1:], kwargs[key]))
                        elif re.match(".+=.+", part):
                            k, v = part.split("=")
                            if v in kwargs:
                                _kwargs[k] = kwargs[v]
                                used_args.add(v)
                            elif v.startswith("$") and (key := v.split(".")[0]) in kwargs:
                                _kwargs[k] = _eval(v[1:], kwargs[key])
                            else:
                                _kwargs[k] = v
                        elif part in kwargs:
                            _args.append(kwargs[part])
                            used_args.add(part)
                        else:
                            _args.append(part)
                    results.append(cls(*_args, **_kwargs))  # type: ignore
                    continue
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
                formatted_text = self.format_field(obj, format_spec) if format_spec else obj
                results.append(formatted_text)

        return functools.reduce(self._add, results), auto_arg_index

    def format_field(self, value: Any, format_spec: str) -> Any:
        formatter: Optional[FormatSpecFunc] = self.format_specs.get(format_spec)
        if formatter is None and format_spec in _MAPPING:
            formatter = _MAPPING[format_spec]  # type: ignore
        return super().format_field(value, format_spec) if formatter is None else formatter(value)

    def get_field(self, field_name, args, kwargs):
        first, rest = _string.formatter_field_name_split(field_name)

        obj = self.get_value(first, args, kwargs)

        return obj, first

    def _add(self, a: Any, b: Any) -> Any:
        try:
            return a + b
        except TypeError:
            return a + str(b)
