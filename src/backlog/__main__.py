"""CLI entry point for backlog."""

import argparse
import sys

from backlog.i18n import load_locale, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


def main() -> None:
    # Parse --lang early (before app/cli imports, so t() is ready)
    lang_parser = argparse.ArgumentParser(add_help=False)
    lang_parser.add_argument("--lang", default=DEFAULT_LANGUAGE, choices=SUPPORTED_LANGUAGES)
    known, _ = lang_parser.parse_known_args()
    load_locale(known.lang)

    # Import AFTER load_locale so t() works in module-level code
    from backlog.app import BacklogApp
    from backlog.cli import run_cli

    # If first arg is "tui" or no args, launch TUI
    if len(sys.argv) < 2 or sys.argv[1] == "tui":
        BacklogApp().run()
        return

    run_cli()


if __name__ == "__main__":
    main()
