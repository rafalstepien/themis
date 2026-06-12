from src.review_engine.ports.outbound import BusinessContextPort


class JiraClient(BusinessContextPort):
    def __init__(self, token): ...

    def get_business_context(self): ...
