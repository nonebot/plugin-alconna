from abc import ABCMeta, abstractmethod

from .target import TargetFetcher
from .builder import MessageBuilder
from .exporter import MessageExporter
from .constraint import SupportAdapter


class BaseLoader(metaclass=ABCMeta):
    @abstractmethod
    def get_adapter(self) -> SupportAdapter: ...

    @abstractmethod
    def get_builder(self) -> MessageBuilder: ...

    @abstractmethod
    def get_exporter(self) -> MessageExporter: ...

    def get_fetcher(self) -> TargetFetcher:
        raise NotImplementedError
