from src.review_engine.ports.outbound import ModuleContextPort


class LocalFileContextAdapter(ModuleContextPort):
    def load_rules(self, modules: list[str]) -> dict:
        return {}

    def load_architecture(self, modules: list[str]) -> dict:
        return {}
