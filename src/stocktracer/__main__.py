#!/usr/bin/env python
"""This is the main entrypoint for the CLI."""

import sys
from typing import Optional

import beartype.roar
import fire

from stocktracer.cli import Cli


def main_cli(command: Optional[str] = None) -> str | int | None:
    """Entry point for the packaging script.

    Args:
        command (Optional[str]): alternative input for CLI arguments. Defaults to None.

    Returns:
        str | int | None: exit code
    """
    cli = Cli()

    # Since we're running with Fire, we need to return None to avoid chaining
    Cli.return_results = False
    try:
        return fire.Fire(component=cli, name="stocktracer", command=command)
    except Exception as app_exception:  # pylint: disable=broad-exception-caught
        if isinstance(app_exception, beartype.roar.BeartypeException):
            raise app_exception
        return str(app_exception)


if __name__ == "__main__":
    sys.exit(main_cli())
