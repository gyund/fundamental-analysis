#!/usr/bin/env python
"""This is the main entrypoint for the CLI."""

import sys

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
    except Exception as e:
        # return e # No stack dump
        raise e  # stack dump


if __name__ == "__main__":
    sys.exit(main_cli())
