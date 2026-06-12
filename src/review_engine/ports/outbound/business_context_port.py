from abc import ABC, abstractmethod


class BusinessContextPort(ABC):
    ...

    @abstractmethod
    def get_business_context(self): ...
