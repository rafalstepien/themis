from enum import StrEnum
import logging
import os

import click

from src.review_engine.adapters.inbound.cli_adapter import ReviewEngineCLIAdapter


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


class RunMode(StrEnum):
    ENGINE = "engine"
    INDEXER = "indexer"


@click.command()
@click.option(
    "--mode", default="engine", help="The mode in which the script is run (engine | indexer)"
)
def main(mode: str):
    _configure_logging()
    if mode == RunMode.ENGINE:
        ReviewEngineCLIAdapter().run()
    elif mode == RunMode.INDEXER:
        raise NotImplementedError


if __name__ == "__main__":
    main()
