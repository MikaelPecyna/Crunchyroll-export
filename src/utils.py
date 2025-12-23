"""
Utility functions for JSON extraction and data processing.

Provides helper functions for navigating nested JSON structures and extracting data
from Crunchyroll API responses.
"""

import csv
import logging
import os
from typing import Any, Dict, List, Optional


def get_nested_value(obj: Dict[str, Any], path: str, movie_keys: Dict[str, str] = None) -> Any:
    """
    Extract a value from a nested dictionary using dot notation.
    
    Handles special cases for movies vs. series where JSON structure differs.
    
    Args:
        obj: Dictionary to navigate
        path: Dot-separated path (e.g., "panel.episode_metadata.series_id")
        movie_keys: Optional mapping for movie-specific keys
        
    Returns:
        The value at the path, or empty string if not found
        
    Example:
        >>> data = {"panel": {"title": "Attack on Titan", "episode_metadata": {"series_id": "abc123"}}}
        >>> get_nested_value(data, "panel.episode_metadata.series_id")
        'abc123'
    """
    keys = path.split(".")
    current_obj = obj
    
    for key in keys:
        if not isinstance(current_obj, dict):
            return ""
        
        if key in current_obj:
            current_obj = current_obj[key]
        elif movie_keys and key in movie_keys:
            # Handle movie-specific key mapping
            movie_key = movie_keys[key]
            if isinstance(current_obj, dict) and movie_key in current_obj:
                current_obj = current_obj[movie_key]
            else:
                return ""
        else:
            return ""
    
    return current_obj


def extract_row_from_json(
    json_obj: Dict[str, Any],
    columns: List[str],
    column_mappings: Dict[str, str],
    movie_keys: Dict[str, str] = None,
    extra_fields: Dict[str, Any] = None
) -> List[Any]:
    """
    Extract a row of data from a JSON object based on column mappings.
    
    Args:
        json_obj: JSON object to extract from
        columns: List of column names to extract
        column_mappings: Mapping of column names to JSON paths
        movie_keys: Optional movie-specific key mappings
        extra_fields: Optional additional fields (e.g., for crunchylist title)
        
    Returns:
        List of extracted values for the row
        
    Example:
        >>> columns = ["Title", "Code"]
        >>> mappings = {"Title": "panel.title", "Code": "id"}
        >>> data = {"id": "abc", "panel": {"title": "Attack on Titan"}}
        >>> extract_row_from_json(data, columns, mappings)
        ['Attack on Titan', 'abc']
    """
    row = []
    extra_fields = extra_fields or {}
    
    for column in columns:
        if column in extra_fields:
            # Use pre-extracted field (e.g., crunchylist title)
            row.append(extra_fields[column])
        elif column in column_mappings:
            path = column_mappings[column]
            value = get_nested_value(json_obj, path, movie_keys)
            row.append(value)
        else:
            row.append("")
    
    return row


def validate_columns(
    provided_columns: List[str],
    valid_columns: Dict[str, str],
    sheet_name: str
) -> bool:
    """
    Validate that all provided columns exist in the valid columns mapping.
    
    Args:
        provided_columns: Columns from the sheet
        valid_columns: Valid column mappings
        sheet_name: Name of the sheet (for error messages)
        
    Returns:
        True if all columns are valid
        
    Raises:
        ValueError: If any column is invalid
    """
    for column in provided_columns:
        if column not in valid_columns:
            raise ValueError(f"[{sheet_name}] Column '{column}' is not a valid column name")
    return True


def map_languages(codes: List[str], language_mapping: Dict[str, str]) -> List[str]:
    """
    Map language codes to human-readable language names.
    
    Args:
        codes: List of language codes
        language_mapping: Mapping of language codes to names
        
    Returns:
        Sorted list of language names
    """
    languages = []
    for code in codes:
        if code in language_mapping:
            languages.append(language_mapping[code])
    
    return sorted(languages)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Global cache for anime code -> title mapping
_anime_cache: Optional[Dict[str, str]] = None


def load_anime_cache(anime_csv_path: str = None) -> Dict[str, str]:
    """
    Load anime codes and titles from CSV file into cache.
    
    Uses a global cache to avoid reloading the file multiple times.
    Looks for anime_code.csv in current or specified path.
    
    Args:
        anime_csv_path: Optional path to anime_code.csv file
        
    Returns:
        Dictionary mapping anime codes to titles
        
    Example:
        >>> cache = load_anime_cache()
        >>> cache.get("G1XHJV0KV")
        "Tis Time for "Torture," Princess"
    """
    global _anime_cache
    
    # Return cached data if already loaded
    if _anime_cache is not None:
        return _anime_cache
    
    # Determine file path
    if anime_csv_path is None:
        # Look in parent directory of this script (root of project)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        anime_csv_path = os.path.join(current_dir, "anime_code.csv")
    
    # Initialize empty cache
    _anime_cache = {}
    
    # Try to load the file
    if not os.path.exists(anime_csv_path):
        logger = setup_logger(__name__)
        logger.warning(f"Anime cache file not found: {anime_csv_path}")
        return _anime_cache
    
    try:
        with open(anime_csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support both "Code" and "Anime Code" column names
                code_key = "Code" if "Code" in row else "Anime Code"
                if row and code_key in row and "Title" in row:
                    code = row[code_key].strip()
                    title = row["Title"].strip()
                    if code:
                        _anime_cache[code] = title
        
        logger = setup_logger(__name__)
        logger.info(f"Loaded {len(_anime_cache)} anime titles from cache")
    except (IOError, csv.Error) as e:
        logger = setup_logger(__name__)
        logger.warning(f"Failed to load anime cache: {e}")
    
    return _anime_cache


def get_anime_title(anime_code: str, anime_cache: Dict[str, str] = None) -> str:
    """
    Get anime title from code using cache.
    
    Args:
        anime_code: The anime code (e.g., "G1XHJV0KV")
        anime_cache: Optional pre-loaded cache (otherwise loads on first use)
        
    Returns:
        Anime title or empty string if not found
        
    Example:
        >>> get_anime_title("G1XHJV0KV")
        "Tis Time for "Torture," Princess"
    """
    if not anime_code:
        return ""
    
    # Load cache if not provided
    if anime_cache is None:
        anime_cache = load_anime_cache()
    
    # Return title or empty string if not found
    return anime_cache.get(anime_code, "")
