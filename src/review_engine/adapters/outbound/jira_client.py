from src.review_engine.ports.outbound import BusinessContextPort


class JiraClient(BusinessContextPort):
    def __init__(self, token: str): ...

    def get_business_context(self, ticket_id: str) -> str:
        return ""
