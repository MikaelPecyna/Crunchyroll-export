"""
Configuration for Crunchyroll data export tool.

Maps column names to JSON paths in Crunchyroll API responses.
Based on the original Google Apps Script implementation.
"""

# Watchlist column mappings
WATCHLIST_COLUMNS = {
    "Anime Code": "id",
    "Title": "panel.title",
    "Type": "panel.type",
    "Series ID": "panel.episode_metadata.series_id",
    "Episode Number": "panel.episode_metadata.episode_number",
    "Duration": "panel.duration_ms",
    "Rating": "panel.rating",
    "Description": "panel.description",
    "Images": "panel.images",
}

# History column mappings
HISTORY_COLUMNS = {
    "Anime Code": "id",
    "Title": "panel.title",
    "Type": "panel.type",
    "Series ID": "panel.episode_metadata.series_id",
    "Episode Number": "panel.episode_metadata.episode_number",
    "Last Watched": "last_watch_date",
    "Duration": "panel.duration_ms",
    "Description": "panel.description",
}

# Crunchylist column mappings
CRUNCHYLIST_COLUMNS = {
    "List Name": "title",
    "Anime Code": "id",
    "Title": "panel.title",
    "Type": "panel.type",
    "Description": "panel.description",
}

# Movie keys mapping
# Movies use different JSON structure than series
movie_keys = {
    "episode_metadata": "movie_listing_metadata",
    "series_id": "movie_id",
    "series_title": "title",
}

# Crunchyroll API configuration
CRUNCHYROLL_API_BASE_URL = "https://www.crunchyroll.com"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Language codes mapping
LANGUAGES = {
    "ja-JP": "Japanese",
    "en-US": "English",
    "en-IN": "English (India)",
    "id-ID": "Bahasa Indonesia",
    "ms-MY": "Bahasa Melayu",
    "ca-ES": "Català",
    "de-DE": "Deutsch",
    "es-419": "Español (América Latina)",
    "es-ES": "Español (España)",
    "fr-FR": "Français",
    "it-IT": "Italiano",
    "pl-PL": "Polski",
    "pt-BR": "Português (Brasil)",
    "pt-PT": "Português (Portugal)",
    "vi-VN": "Tiếng Việt",
    "tr-TR": "Türkçe",
    "ru-RU": "Русский",
    "ar-SA": "العربية",
    "hi-IN": "हिंदी",
    "ta-IN": "தமிழ்",
    "te-IN": "తెలుగు",
    "zh-CN": "中文 (普通话)",
    "zh-HK": "中文 (粵語)",
    "zh-TW": "中文 (國語)",
    "ko-KR": "한국어",
    "th-TH": "ไทย"
}

# CSV export configuration
CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM for cross-platform compatibility
CSV_DELIMITER = ","
