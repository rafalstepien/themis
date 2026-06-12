from abc import ABC, abstractmethod


class CodeRepresentationPort(ABC):

    """
    An interface for getting the actual Merge Request diff.
    In the MVP it will be plain diff (PlainDiffAdapter), later might switch to
    AST-based representation (ASTAdapter). This interface makes it easily replacable.
    """

    @abstractmethod
    def get_code(self):
        ...
