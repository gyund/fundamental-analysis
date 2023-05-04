#!/usr/bin/env python


import fire

from stocktracer.cli import Cli


def main_cli() -> any:
    """Entrypoint

    Returns:
        any: normal return values from main
    """
    cli = Cli()
    return fire.Fire(component=cli, name="stocktracer")


if __name__ == "__main__":
    main_cli()
