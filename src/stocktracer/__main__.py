#!/usr/bin/env python


import fire

from stocktracer.cli import Cli


def main_cli(command=None) -> any:
    """Entrypoint

    Returns:
        any: normal return values from main
    """
    cli = Cli()
    try:
        return fire.Fire(component=cli, name="stocktracer", command=command)
    except Exception as e:
        # return e # No stack dump
        raise e  # stack dump


if __name__ == "__main__":
    exit(main_cli())
