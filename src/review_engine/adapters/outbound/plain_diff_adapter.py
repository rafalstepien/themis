from src.review_engine.ports.outbound import CodeRepresentationPort


class PlainDiffAdapter(CodeRepresentationPort):

    def get_code(self): ...
