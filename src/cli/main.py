import logging
import os
import sys

from src.engine.adapters.inbound import GitHubCLIAdapter, GitLabCLIAdapter

logger = logging.getLogger(__file__)


def _configure_logging() -> None:
    """Route all engine logs to stderr.

    Level is driven by ``THEMIS_LOG_LEVEL`` (default ``INFO``). Set it to
    ``DEBUG`` to surface the full LLM prompt and the raw LLM response.
    """
    level = os.environ.get("THEMIS_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )


def main(git_provider: str):
    _configure_logging()
    if git_provider == "gitlab":
        GitLabCLIAdapter().run()
    elif git_provider == "github":
        GitHubCLIAdapter().run()
    else:
        logger.error("Git provider unrecognized. Options: [gitlab | github]")
        sys.exit(1)
