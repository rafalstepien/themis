import json
import logging
from pathlib import Path

from src.bootstrap.config import (
    ARCHITECTURE_FILENAME,
    ARCHITECTURE_SUBDIR,
    RULES_FILENAME,
    RULES_SUBDIR,
)
from src.review_engine.ports.outbound import ModuleContextPort

logger = logging.getLogger(__name__)


class LocalFileContextAdapter(ModuleContextPort):
    """Loads per-module rules and architecture context from the consumer repo.

    For example if the repo has a module src/payment, then this adapter will
        - load past MR rules from .themis-ai/rules/payment/rule.json
        - load architecture context from .themis-ai/architecture/payment/architecture.json

    The inner JSON shape is intentionally NOT pinned to a DTO: this content is
    produced by the (LLM-driven) Indexer and consumed only as LLM prompt
    material, so the payload is returned as freeform parsed JSON. Loading is
    lenient — a missing or malformed file is skipped (the module is simply
    omitted from the result) rather than failing the whole review.
    """

    def __init__(self, themis_dir: Path):
        self._themis_dir = themis_dir

    def load_rules(self, modules: list[str]) -> dict:
        return self._load(modules, RULES_SUBDIR, RULES_FILENAME)

    def load_architecture(self, modules: list[str]) -> dict:
        return self._load(modules, ARCHITECTURE_SUBDIR, ARCHITECTURE_FILENAME)

    def _load(self, modules: list[str], subdir: str, filename: str) -> dict:
        loaded: dict = {}
        for module in modules:
            key = Path(module).name
            path = self._themis_dir / subdir / key / filename
            payload = self._read_json(path)
            if payload is not None:
                loaded[key] = payload
        if modules and not loaded:
            logger.warning(
                "No %s context loaded for affected modules %s under %s; "
                "review will proceed without it",
                subdir,
                [Path(module).name for module in modules],
                self._themis_dir / subdir,
            )
        return loaded

    @staticmethod
    def _read_json(path: Path) -> dict | list | None:
        try:
            content = path.read_text()
        except FileNotFoundError:
            logger.debug("No context file at %s; skipping", path)
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Malformed JSON in %s; skipping", path)
            return None
