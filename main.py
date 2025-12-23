#!/usr/bin/python3
"""
Crunchyroll Data Manager CLI.

Command-line interface for exporting Crunchyroll watchlists,
history, and custom lists to CSV files.

This is a Python rewrite of the original Google Apps Script implementation.
"""

import argparse
import csv
import getpass
import logging
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

from src.config import (
    CRUNCHYLIST_COLUMNS,
    CSV_DELIMITER,
    CSV_ENCODING,
    HISTORY_COLUMNS,
    LANGUAGES,
    WATCHLIST_COLUMNS,
)
from src.services import (
    CrunchyrollAPIError,
    CrunchyrollService,
    export_crunchylists_data,
    export_history_data,
    export_watchlist_data,
)
from src.utils import map_languages, setup_logger


load_dotenv()
logger = setup_logger(__name__)


class CrunchyrollCLI:
    """Command-line interface for Crunchyroll data management."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the CLI.

        Args:
            token: Optional Crunchyroll authorization token.
                  If not provided, will prompt user for it.
        """
        self.token = token or self._get_token()
        self.service = None

    def _get_token(self) -> str:
        """
        Get authorization token from environment or user input.

        Returns:
            Authorization token string

        Raises:
            ValueError: If no token is provided
        """
        # Try to get from environment variable
        token = os.getenv("CRUNCHYROLL_TOKEN")
        if token:
            logger.info("Using token from CRUNCHYROLL_TOKEN environment variable")
            return token

        # Prompt user for token
        token = getpass.getpass("Enter your Crunchyroll authorization token: ")
        if not token:
            raise ValueError("Authorization token is required")

        return token

    def _init_service(self) -> CrunchyrollService:
        """
        Initialize the Crunchyroll service.

        Returns:
            Initialized CrunchyrollService instance

        Raises:
            CrunchyrollAPIError: If service initialization fails
        """
        if self.service:
            return self.service

        self.service = CrunchyrollService(self.token, LANGUAGES)
        logger.info("Crunchyroll service initialized")
        return self.service

    def export_watchlist(self, output_file: str, columns: Optional[List[str]] = None):
        """
        Export watchlist to CSV file.

        Args:
            output_file: Path to output CSV file
            columns: List of columns to export. If None, exports all available.

        Raises:
            CrunchyrollAPIError: If API call fails
            IOError: If file write fails
        """
        try:
            service = self._init_service()
            account_id = service.get_account_id()
            logger.info(f"Account ID: {account_id}")

            # Use all columns if not specified
            if not columns:
                columns = list(WATCHLIST_COLUMNS.keys())

            logger.info(f"Exporting watchlist with columns: {columns}")
            rows = export_watchlist_data(service, account_id, columns)

            # Write to CSV
            self._write_csv(output_file, columns, rows)
            logger.info(f"Watchlist exported to {output_file}")

        except CrunchyrollAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except IOError as e:
            logger.error(f"File error: {e}")
            raise

    def export_history(self, output_file: str, columns: Optional[List[str]] = None):
        """
        Export watch history to CSV file.

        Args:
            output_file: Path to output CSV file
            columns: List of columns to export. If None, exports all available.

        Raises:
            CrunchyrollAPIError: If API call fails
            IOError: If file write fails
        """
        try:
            service = self._init_service()
            account_id = service.get_account_id()

            # Use all columns if not specified
            if not columns:
                columns = list(HISTORY_COLUMNS.keys())

            logger.info(f"Exporting history with columns: {columns}")
            rows = export_history_data(service, account_id, columns)

            # Write to CSV
            self._write_csv(output_file, columns, rows)
            logger.info(f"History exported to {output_file}")

        except CrunchyrollAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except IOError as e:
            logger.error(f"File error: {e}")
            raise

    def export_crunchylists(self, output_file: str, columns: Optional[List[str]] = None):
        """
        Export crunchylists to CSV file.

        Args:
            output_file: Path to output CSV file
            columns: List of columns to export. If None, exports all available.

        Raises:
            CrunchyrollAPIError: If API call fails
            IOError: If file write fails
        """
        try:
            service = self._init_service()
            account_id = service.get_account_id()

            # Use all columns if not specified
            if not columns:
                columns = list(CRUNCHYLIST_COLUMNS.keys())

            logger.info(f"Exporting crunchylists with columns: {columns}")
            rows = export_crunchylists_data(service, account_id, columns)

            # Write to CSV
            self._write_csv(output_file, columns, rows)
            logger.info(f"Crunchylists exported to {output_file}")

        except CrunchyrollAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except IOError as e:
            logger.error(f"File error: {e}")
            raise

    def show_all_columns(self):
        """Display all available columns for each data type."""
        print("\n" + "=" * 60)
        print("AVAILABLE COLUMNS FOR EXPORT")
        print("=" * 60)

        print("\nWATCHLIST COLUMNS:")
        for i, column in enumerate(WATCHLIST_COLUMNS.keys(), 1):
            print(f"  {i}. {column}")

        print("\nHISTORY COLUMNS:")
        for i, column in enumerate(HISTORY_COLUMNS.keys(), 1):
            print(f"  {i}. {column}")

        print("\nCRUNCHYLIST COLUMNS:")
        for i, column in enumerate(CRUNCHYLIST_COLUMNS.keys(), 1):
            print(f"  {i}. {column}")

        print("\n" + "=" * 60 + "\n")

    def get_anime_list(self, output_file: str):
        """
        Export complete anime catalog with language information.

        Args:
            output_file: Path to output CSV file

        Raises:
            CrunchyrollAPIError: If API call fails
            IOError: If file write fails
        """
        try:
            service = self._init_service()
            logger.info("Fetching complete anime catalog...")
            anime_list = service.get_anime_list()
            logger.info(f"Fetched {len(anime_list)} anime")

            # Process anime data
            columns = ["Title", "Link", "Code", "Audio Languages", "Subtitle Languages"]
            rows = []

            for anime in anime_list:
                title = anime.get("title", "")
                anime_type = anime.get("type", "")
                anime_code = anime.get("id", "")

                # Build link based on type
                if anime_type == "series":
                    link = f"https://www.crunchyroll.com/series/{anime_code}"
                elif anime_type == "movie_listing":
                    link = f"https://www.crunchyroll.com/watch/{anime_code}"
                else:
                    link = ""

                # Extract audio locales
                audio_languages = []
                try:
                    audio_codes = anime.get("series_metadata", {}).get("audio_locales", [])
                    audio_languages = map_languages(audio_codes, LANGUAGES)
                except (AttributeError, TypeError):
                    pass

                # Extract subtitle locales
                subtitle_languages = []
                try:
                    if anime_type == "series":
                        subtitle_codes = (
                            anime.get("series_metadata", {}).get("subtitle_locales", [])
                        )
                    else:
                        subtitle_codes = (
                            anime.get("movie_listing_metadata", {}).get(
                                "subtitle_locales", []
                            )
                        )
                    subtitle_languages = map_languages(subtitle_codes, LANGUAGES)
                except (AttributeError, TypeError):
                    pass

                row = [
                    title,
                    link,
                    anime_code,
                    ",".join(audio_languages),
                    ",".join(subtitle_languages),
                ]
                rows.append(row)

            # Write to CSV
            self._write_csv(output_file, columns, rows)
            logger.info(f"Anime list exported to {output_file}")

        except CrunchyrollAPIError as e:
            logger.error(f"API error: {e}")
            raise

    @staticmethod
    def _write_csv(filename: str, headers: List[str], rows: List[List]):
        """
        Write data to CSV file.

        Args:
            filename: Output file path
            headers: List of column headers
            rows: List of data rows
        """
        try:
            with open(filename, "w", newline="", encoding=CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=CSV_DELIMITER)
                writer.writerow(headers)
                writer.writerows(rows)
        except (UnicodeEncodeError, LookupError):
            # Fallback to utf-8 if the configured encoding fails
            logger.warning(f"Encoding {CSV_ENCODING} failed, falling back to utf-8")
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=CSV_DELIMITER)
                writer.writerow(headers)
                writer.writerows(rows)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Crunchyroll Data Manager - Export watchlist, history, and crunchylists"
    )

    parser.add_argument(
        "--token",
        help="Crunchyroll authorization token (or set CRUNCHYROLL_TOKEN env var)",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Export watchlist
    export_watchlist_parser = subparsers.add_parser(
        "export-watchlist", help="Export watchlist to CSV"
    )
    export_watchlist_parser.add_argument("output", help="Output CSV file path")
    export_watchlist_parser.add_argument(
        "--columns",
        help="Comma-separated list of columns to export (default: all)",
        default=None,
    )

    # Export history
    export_history_parser = subparsers.add_parser(
        "export-history", help="Export watch history to CSV"
    )
    export_history_parser.add_argument("output", help="Output CSV file path")
    export_history_parser.add_argument(
        "--columns",
        help="Comma-separated list of columns to export (default: all)",
        default=None,
    )

    # Export crunchylists
    export_crunchylists_parser = subparsers.add_parser(
        "export-crunchylists", help="Export crunchylists to CSV"
    )
    export_crunchylists_parser.add_argument("output", help="Output CSV file path")
    export_crunchylists_parser.add_argument(
        "--columns",
        help="Comma-separated list of columns to export (default: all)",
        default=None,
    )

    # Get anime list
    anime_list_parser = subparsers.add_parser(
        "get-anime-list", help="Export complete anime catalog"
    )
    anime_list_parser.add_argument("output", help="Output CSV file path")

    # Show columns
    columns_parser = subparsers.add_parser(
        "show-columns", help="Show all available columns"
    )

    args = parser.parse_args()

    # Execute commands
    try:
        if not args.command:
            parser.print_help()
            return 1

        cli = CrunchyrollCLI(token=args.token)

        if args.command == "export-watchlist":
            columns = (
                args.columns.split(",") if args.columns else None
            )
            cli.export_watchlist(args.output, columns=columns)

        elif args.command == "export-history":
            columns = (
                args.columns.split(",") if args.columns else None
            )
            cli.export_history(args.output, columns=columns)

        elif args.command == "export-crunchylists":
            columns = (
                args.columns.split(",") if args.columns else None
            )
            cli.export_crunchylists(args.output, columns=columns)

        elif args.command == "get-anime-list":
            cli.get_anime_list(args.output)

        elif args.command == "show-columns":
            cli.show_all_columns()

        logger.info("Command completed successfully")
        return 0

    except (CrunchyrollAPIError, IOError, ValueError) as e:
        logger.error(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
