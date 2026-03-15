"""CLI entry point for backlog."""

import argparse
import sys

from backlog.cli import run_cli
from backlog.app import BacklogApp


def main() -> None:
    # If first arg is "tui" or no args, launch TUI
    if len(sys.argv) < 2 or sys.argv[1] == "tui":
        BacklogApp().run()
        return

    run_cli()


if __name__ == "__main__":
    main()
