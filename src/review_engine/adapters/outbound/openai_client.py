from src.review_engine.ports.outbound import LLMPort


class OpenAIClient(LLMPort):
    def __init__(self, token: str): ...

    def generate_code_review(self): ...
