#!/usr/bin/env python
"""This is the main entrypoint for the CLI."""

import sys

import beartype
import fire

from stocktracer.cli import Cli


def main_cli(command: str = None) -> any:
    """Entry point for the packaging script.

    Args:
        command (str): alternative input for CLI arguments. Defaults to None.

    Returns:
        any: _description_
    """
    cli = Cli()
    try:
        return fire.Fire(component=cli, name="stocktracer", command=command)
    except Exception as app_exception:  # pylint: disable=broad-exception-caught
        try:
            if beartype.beartype(app_exception) is app_exception:
                # Beartype exceptions should be thrown, all others should just be printed
                raise app_exception
        except Exception:  # pylint: disable=broad-exception-caught
            # Not a beartype
            pass
        return app_exception


if __name__ == "__main__":
    sys.exit(main_cli())
