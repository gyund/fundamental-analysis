#!/usr/bin/env python


import fire

from stocktracer.cli import Cli


def main_cli() -> any:
    """Entrypoint

    Returns:
        any: normal return values from main
    """
    cli = Cli()
    try:
        return fire.Fire(component=cli, name="stocktracer")
    except Exception as e:
        return e

if __name__ == "__main__":
    exit(main_cli())
