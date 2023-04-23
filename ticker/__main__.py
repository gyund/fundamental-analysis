#!/usr/bin/env python


import fire
from ticker.cli import Cli

if __name__ == '__main__':
    cli = Cli()
    fire.Fire(
        component=cli,
        name="ticker"
    )
