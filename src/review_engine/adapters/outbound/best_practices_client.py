from src.review_engine.ports.outbound.best_practices_port import BestPracticesPort


class BestPracticesClient(BestPracticesPort):
    def load_best_practices(self, applicable_technologies: list[str]) -> dict:
        """
        1. Identify best practices to check based on changed files
        2. Load applicable best practices from src/best_practices
        """
        return {}
