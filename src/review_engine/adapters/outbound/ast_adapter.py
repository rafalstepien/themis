from src.review_engine.ports.outbound import CodeRepresentationPort


class ASTAdapter(CodeRepresentationPort):

    def get_code(self):
        ...
