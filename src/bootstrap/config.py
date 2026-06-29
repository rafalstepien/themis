from enum import StrEnum
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator
import yaml

logger = logging.getLogger(__name__)

THEMIS_DIR = ".themis-ai"
DEFAULT_CONFIG_PATH = f"{THEMIS_DIR}/config.yaml"

# Vendors reachable through their OpenAI-compatible endpoints.
OPENAI_BASE_URL = "https://api.openai.com/v1"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
ANTHROPIC_OPENAI_BASE_URL = "https://api.anthropic.com/v1/"

# Vendor shortcuts: convenience provider names that desugar to the single
# 'openai_compatible' protocol plus a default base_url. They are *sugar*, not
# protocol values — there is exactly one client.
#
# Lock-in note: these names are permanently bound to compat (Chat Completions)
# semantics. If a native protocol is ever added (e.g. Anthropic's own API), it
# must take a distinct '*_native' name; flipping 'anthropic' to mean native
# would break every existing config. Reserve '*_native' for that future.
_VENDOR_SHORTCUT_BASE_URLS = {
    "openai": OPENAI_BASE_URL,
    "gemini": GEMINI_OPENAI_BASE_URL,
    "anthropic": ANTHROPIC_OPENAI_BASE_URL,
}

RULES_SUBDIR = "rules"
RULES_FILENAME = "rule.json"
ARCHITECTURE_SUBDIR = "architecture"
ARCHITECTURE_FILENAME = "architecture.json"


def rule_file_path(module: str) -> str:
    return f"{THEMIS_DIR}/{RULES_SUBDIR}/{module}/{RULES_FILENAME}"


def architecture_file_path(module: str) -> str:
    return f"{THEMIS_DIR}/{ARCHITECTURE_SUBDIR}/{module}/{ARCHITECTURE_FILENAME}"


class LLMProvider(StrEnum):
    # Themis speaks one protocol: the OpenAI HTTP contract (Chat Completions).
    # This single value is the honest discriminator and the labelled extension
    # point — a second protocol would be added here. Vendor names (openai,
    # gemini, anthropic) are not protocols; they are shortcuts that desugar to
    # this value (see _VENDOR_SHORTCUT_BASE_URLS and LLMConfig).
    OPENAI_COMPATIBLE = "openai_compatible"


class ReviewConfig(BaseModel):
    max_file_chars: int = Field(default=60_000)
    max_changed_files: int = Field(default=50)
    modules: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str
    base_url: str | None = None
    # Set by desugaring, not by the user: a vendor shortcut is a cloud backend
    # and needs a key, whereas explicit 'openai_compatible' is the self-host
    # path and may be keyless. The token rule is decided here on the user's
    # original provider, before the shortcut collapses to openai_compatible.
    requires_token: bool = False

    @model_validator(mode="before")
    @classmethod
    def _desugar_vendor_shortcut(cls, data: Any) -> Any:
        """Expand a vendor shortcut into the openai_compatible protocol.

        ``openai`` / ``gemini`` / ``anthropic`` are convenience names: they map
        to ``openai_compatible`` plus the vendor's default ``base_url`` (which
        the user may still override) and are flagged as cloud (token required).
        Anything else is passed through untouched for the enum to validate.
        """
        if not isinstance(data, dict):
            return data

        data.pop("requires_token", None)  # internal flag, never user-supplied
        default_base_url = _VENDOR_SHORTCUT_BASE_URLS.get(data.get("provider"))
        if default_base_url is not None:
            data = {
                **data,
                "provider": LLMProvider.OPENAI_COMPATIBLE.value,
                "requires_token": True,
            }
            data.setdefault("base_url", default_base_url)
        return data

    @model_validator(mode="after")
    def _require_base_url_for_compatible(self) -> "LLMConfig":
        if self.provider is LLMProvider.OPENAI_COMPATIBLE and not self.base_url:
            raise ValueError("'base_url' is required when provider is 'openai_compatible'.")
        return self


class ThemisConfig(BaseModel):
    version: int
    test_mode: bool = Field(default=False)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    llm: LLMConfig

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> "ThemisConfig":
        with open(path, "r") as f:
            config = cls(**yaml.safe_load(f))
        if not config.review.modules:
            logger.warning(
                "No modules declared in config; per-module rules and "
                "architecture context cannot be loaded and reviews will not "
                "be module-scoped. Declare 'review.modules' in %s.",
                path,
            )
        return config
