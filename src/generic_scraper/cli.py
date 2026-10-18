"""Command-line interface for generic_scraper."""

from __future__ import annotations

import argparse

from generic_scraper.config import ScraperType
from generic_scraper.errors import ScraperError
from generic_scraper.logging_config import configure_logging
from generic_scraper.scraper import Scraper


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser for the `generic-scraper` CLI."""
    parser = argparse.ArgumentParser(prog="generic-scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch a URL and print its parsed title.")
    fetch_parser.add_argument("url", help="URL to fetch.")
    fetch_parser.add_argument(
        "--config", default=None, help="Path to a YAML ScraperType config file."
    )
    fetch_parser.add_argument(
        "--engine", default=None, help="Override the scraper engine (e.g. requests, playwright)."
    )
    fetch_parser.add_argument(
        "--processing-type", default=None, help="Override the processing/parser type."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `generic-scraper` console script."""
    configure_logging()

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.config:
            config = ScraperType.from_file(args.config)
        else:
            config = ScraperType.empty()

        if args.engine is not None:
            config.scraper_engine = args.engine
        if args.processing_type is not None:
            config.processing_type = args.processing_type

        scraper = Scraper(config)
        document = scraper.fetch(args.url)
        print(document.title)
    except (ScraperError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
