from abc import ABC, abstractmethod


class ModuleContextPort(ABC):
    """
    Allows to get per-module context from local files in the repo (eg. architecture rules
    or past merge request rules).
    """

    @abstractmethod
    def load_rules(self, modules: list[str]) -> dict: ...

    @abstractmethod
    def load_architecture(self, modules: list[str]) -> dict: ...
