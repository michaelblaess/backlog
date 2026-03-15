"""CLI entry point for backlog."""

import argparse
import sys

from backlog.i18n import load_locale, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

# CLI subcommands (everything that is NOT tui)
CLI_COMMANDS = {"add", "list", "show", "update", "note", "delete", "summary", "share", "export"}


def main() -> None:
    # Parse --lang early (before app/cli imports, so t() is ready)
    lang_parser = argparse.ArgumentParser(add_help=False)
    lang_parser.add_argument("--lang", default=DEFAULT_LANGUAGE, choices=SUPPORTED_LANGUAGES)
    known, remaining = lang_parser.parse_known_args()
    load_locale(known.lang)

    # Import AFTER load_locale so t() works in module-level code
    from backlog.app import BacklogApp
    from backlog.cli import run_cli

    # Launch TUI if no CLI subcommand given
    has_cli_command = any(arg in CLI_COMMANDS for arg in remaining)
    if not has_cli_command:
        BacklogApp().run()
        return

    run_cli()


if __name__ == "__main__":
    main()
