"""
Crunchyroll API service module.

Handles all API communication with Crunchyroll for exporting
watchlists, history, and custom lists.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from src.config import (
    CRUNCHYROLL_API_BASE_URL,
    CRUNCHYLIST_COLUMNS,
    HISTORY_COLUMNS,
    USER_AGENT,
    WATCHLIST_COLUMNS,
    movie_keys,
)
from src.utils import (
    extract_row_from_json,
    get_anime_title,
    load_anime_cache,
    map_languages,
    setup_logger,
    validate_columns,
)


logger = setup_logger(__name__)


class CrunchyrollAPIError(Exception):
    """Exception raised for API communication errors."""

    pass


class CrunchyrollService:
    """Service for interacting with Crunchyroll API."""

    def __init__(self, token: str, languages_mapping: Dict[str, str] = None):
        """
        Initialize the Crunchyroll service.

        Args:
            token: Authorization token for Crunchyroll API
            languages_mapping: Mapping of language codes to names
        """
        self.token = token
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Authorization": token,
        }
        self.languages_mapping = languages_mapping or {}
        self.account_id = None

    def _make_request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        mute_http_exceptions: bool = False,
    ) -> str:
        """
        Make an HTTP request to Crunchyroll API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            payload: Optional JSON payload for POST requests
            mute_http_exceptions: If True, return error response text instead of raising

        Returns:
            Response text as string

        Raises:
            CrunchyrollAPIError: If request fails (unless mute_http_exceptions=True)
        """
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.text

        except RequestException as e:
            if mute_http_exceptions:
                logger.warning(f"API request failed (muted): {e}")
                return ""
            raise CrunchyrollAPIError(f"API request failed: {e}") from e

    def get_account_id(self) -> str:
        """
        Get the account ID for the authenticated user.

        Returns:
            Account ID string

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        if self.account_id:
            return self.account_id

        url = f"{CRUNCHYROLL_API_BASE_URL}/accounts/v1/me"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            self.account_id = data["account_id"]
            return self.account_id
        except (json.JSONDecodeError, KeyError) as e:
            raise CrunchyrollAPIError(f"Failed to parse account ID: {e}") from e

    def get_watchlist(self, account_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Fetch the user's watchlist.

        Args:
            account_id: User's account ID
            limit: Maximum number of anime to fetch (default 500)

        Returns:
            List of watchlist items (JSON objects)

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        url = f"{CRUNCHYROLL_API_BASE_URL}/content/v2/discover/{account_id}/watchlist?order=desc&n={limit}"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            return data.get("data", [])
        except json.JSONDecodeError as e:
            raise CrunchyrollAPIError(f"Failed to parse watchlist: {e}") from e

    def get_history(self, account_id: str, page_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch the user's watch history.

        Args:
            account_id: User's account ID
            page_size: Number of items per page (default 1000)

        Returns:
            List of history items (JSON objects)

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        url = f"{CRUNCHYROLL_API_BASE_URL}/content/v2/{account_id}/watch-history?page_size={page_size}"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            return data.get("data", [])
        except json.JSONDecodeError as e:
            raise CrunchyrollAPIError(f"Failed to parse history: {e}") from e

    def get_crunchylists(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all custom crunchylists.

        Args:
            account_id: User's account ID

        Returns:
            List of crunchylist metadata (contains list_id and title)

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        url = f"{CRUNCHYROLL_API_BASE_URL}/content/v2/{account_id}/custom-lists"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            return data.get("data", [])
        except json.JSONDecodeError as e:
            raise CrunchyrollAPIError(f"Failed to parse crunchylists: {e}") from e

    def get_crunchylist_items(
        self, account_id: str, list_id: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch items in a specific crunchylist.

        Args:
            account_id: User's account ID
            list_id: ID of the crunchylist

        Returns:
            List of items in the crunchylist

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        url = f"{CRUNCHYROLL_API_BASE_URL}/content/v2/{account_id}/custom-lists/{list_id}"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            return data.get("data", [])
        except json.JSONDecodeError as e:
            raise CrunchyrollAPIError(f"Failed to parse crunchylist items: {e}") from e

    def get_anime_list(self, start: int = 0, limit: int = 1500) -> List[Dict[str, Any]]:
        """
        Fetch the complete anime catalog from Crunchyroll.

        Args:
            start: Starting index for pagination
            limit: Maximum number of anime to fetch

        Returns:
            List of anime in the catalog

        Raises:
            CrunchyrollAPIError: If API call fails
        """
        url = f"{CRUNCHYROLL_API_BASE_URL}/content/v2/discover/browse?start={start}&n={limit}&sort_by=alphabetical"
        response_text = self._make_request("GET", url)

        try:
            data = json.loads(response_text)
            return data.get("data", [])
        except json.JSONDecodeError as e:
            raise CrunchyrollAPIError(f"Failed to parse anime list: {e}") from e


def export_watchlist_data(
    service: CrunchyrollService, account_id: str, columns: List[str]
) -> List[List[Any]]:
    """
    Export watchlist data from Crunchyroll.

    Args:
        service: Initialized CrunchyrollService instance
        account_id: User's account ID
        columns: List of column names to export

    Returns:
        List of rows (each row is a list of values)

    Raises:
        ValueError: If column names are invalid
        CrunchyrollAPIError: If API call fails
    """
    # Validate columns
    validate_columns(columns, WATCHLIST_COLUMNS, "Watch List")

    # Load anime title cache for enrichment
    anime_cache = load_anime_cache()
    logger.info(f"Loaded {len(anime_cache)} anime titles for enrichment")

    # Add "Anime Title" column if "Series ID" is present
    if "Series ID" in columns and "Anime Title" not in columns:
        columns.append("Anime Title")

    # Fetch data from API
    watchlist_json = service.get_watchlist(account_id)
    logger.info(f"Fetched {len(watchlist_json)} items from watchlist")

    # Extract rows and enrich with anime titles
    rows = []
    for item in watchlist_json:
        row = extract_row_from_json(item, columns, WATCHLIST_COLUMNS, movie_keys)
        # Enrich row with anime title if "Series ID" column exists
        if "Series ID" in columns:
            series_id_idx = columns.index("Series ID")
            series_id = row[series_id_idx]
            anime_title = get_anime_title(series_id, anime_cache)
            # Add anime title as new column value
            if "Anime Title" in columns:
                anime_title_idx = columns.index("Anime Title")
                # Ensure row has enough elements
                while len(row) <= anime_title_idx:
                    row.append("")
                row[anime_title_idx] = anime_title
        rows.append(row)

    logger.info(f"Extracted {len(rows)} rows from watchlist (enriched with anime titles)")
    return rows


def export_history_data(
    service: CrunchyrollService, account_id: str, columns: List[str]
) -> List[List[Any]]:
    """
    Export history data from Crunchyroll.

    Args:
        service: Initialized CrunchyrollService instance
        account_id: User's account ID
        columns: List of column names to export

    Returns:
        List of rows (each row is a list of values)

    Raises:
        ValueError: If column names are invalid
        CrunchyrollAPIError: If API call fails
    """
    # Validate columns
    validate_columns(columns, HISTORY_COLUMNS, "History")

    # Load anime title cache for enrichment
    anime_cache = load_anime_cache()
    logger.info(f"Loaded {len(anime_cache)} anime titles for enrichment")

    # Add "Anime Title" column if "Series ID" is present
    if "Series ID" in columns and "Anime Title" not in columns:
        columns.append("Anime Title")

    # Fetch data from API
    history_json = service.get_history(account_id)
    logger.info(f"Fetched {len(history_json)} items from history")

    # Extract rows and enrich with anime titles
    rows = []
    for item in history_json:
        row = extract_row_from_json(item, columns, HISTORY_COLUMNS, movie_keys)
        # Enrich row with anime title if "Series ID" column exists
        if "Series ID" in columns:
            series_id_idx = columns.index("Series ID")
            series_id = row[series_id_idx]
            anime_title = get_anime_title(series_id, anime_cache)
            # Add anime title as new column value
            if "Anime Title" in columns:
                anime_title_idx = columns.index("Anime Title")
                # Ensure row has enough elements
                while len(row) <= anime_title_idx:
                    row.append("")
                row[anime_title_idx] = anime_title
        rows.append(row)

    logger.info(f"Extracted {len(rows)} rows from history (enriched with titles)")
    return rows


def export_crunchylists_data(
    service: CrunchyrollService, account_id: str, columns: List[str]
) -> List[List[Any]]:
    """
    Export crunchylists data from Crunchyroll.

    Args:
        service: Initialized CrunchyrollService instance
        account_id: User's account ID
        columns: List of column names to export

    Returns:
        List of rows (each row is a list of values)

    Raises:
        ValueError: If column names are invalid
        CrunchyrollAPIError: If API call fails
    """
    # Validate columns
    validate_columns(columns, CRUNCHYLIST_COLUMNS, "Crunchylist")

    # Load anime title cache for enrichment
    anime_cache = load_anime_cache()
    logger.info(f"Loaded {len(anime_cache)} anime titles for enrichment")

    # Add "Anime Title" column if "Series ID" is present
    if "Series ID" in columns and "Anime Title" not in columns:
        columns.append("Anime Title")

    # Fetch crunchylist metadata
    crunchylists = service.get_crunchylists(account_id)
    logger.info(f"Fetched {len(crunchylists)} crunchylists")

    # Extract rows for each item in each crunchylist
    rows = []
    for crunchylist in crunchylists:
        list_id = crunchylist.get("list_id")
        list_title = crunchylist.get("title", "")

        # Fetch items in this crunchylist
        items = service.get_crunchylist_items(account_id, list_id)

        for item in items:
            extra_fields = {"List Name": list_title}
            row = extract_row_from_json(
                item,
                columns,
                CRUNCHYLIST_COLUMNS,
                movie_keys,
                extra_fields=extra_fields,
            )
            # Enrich row with anime title if "Series ID" column exists
            if "Series ID" in columns:
                series_id_idx = columns.index("Series ID")
                series_id = row[series_id_idx]
                anime_title = get_anime_title(series_id, anime_cache)
                # Add anime title as new column value
                if "Anime Title" in columns:
                    anime_title_idx = columns.index("Anime Title")
                    # Ensure row has enough elements
                    while len(row) <= anime_title_idx:
                        row.append("")
                    row[anime_title_idx] = anime_title
            rows.append(row)

    logger.info(f"Extracted {len(rows)} rows from crunchylists (enriched with anime titles)")
    return rows
