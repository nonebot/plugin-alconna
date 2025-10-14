from abc import ABCMeta, abstractmethod

from .builder import MessageBuilder
from .constraint import SupportAdapter
from .exporter import MessageExporter
from .target import TargetFetcher


class BaseLoader(metaclass=ABCMeta):
    @abstractmethod
    def get_adapter(self) -> SupportAdapter: ...

    @abstractmethod
    def get_builder(self) -> MessageBuilder: ...

    @abstractmethod
    def get_exporter(self) -> MessageExporter: ...

    def get_fetcher(self) -> TargetFetcher:
        raise NotImplementedError
