from abc import ABCMeta, abstractmethod

from .exporter import MessageExporter
from .constraint import SupportAdapter


class BaseLoader(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_adapter(cls) -> SupportAdapter: ...

    @classmethod
    @abstractmethod
    def get_exporter(cls) -> MessageExporter: ...
