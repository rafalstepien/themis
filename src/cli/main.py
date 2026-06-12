
from enum import StrEnum

import click

from src.review_engine.adapters.inbound.cli_adapter import ReviewEngineCLIAdapter


class RunMode(StrEnum):
    ENGINE = "engine"
    INDEXER = "indexer"


@click.command()
@click.option('--mode', default="engine", help='The mode in which the script is run (engine | indexer)')
def main(mode: str):
    if mode == RunMode.ENGINE:
        ReviewEngineCLIAdapter().run()
    elif mode == RunMode.INDEXER:
        raise NotImplementedError

if __name__ == "__main__":
    main()
