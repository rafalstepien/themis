from abc import ABC, abstractmethod


class GitLabPort(ABC):

    @abstractmethod
    def get_mr_data(self):
        ...

    @abstractmethod
    def post_comment(self):
        ...
    
    @abstractmethod
    def get_file_content(self) -> str:
        ...
