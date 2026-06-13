"""Configuration for MetaScrub."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Maximum upload size in bytes (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# File extensions accepted by the scrubber
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "tiff", "webp",
    "docx",
    "mp3", "flac", "ogg", "m4a",
}

# Storage locations
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CLEANED_FOLDER = os.path.join(BASE_DIR, "cleaned")

# SQLite database location
DB_PATH = os.path.join(BASE_DIR, "db", "metascrub.db")

# Files older than this (in seconds) are auto-deleted from
# both UPLOAD_FOLDER and CLEANED_FOLDER by the background janitor.
AUTO_DELETE_AFTER_SECONDS = 3600

# How often (in seconds) the background janitor sweeps for expired files.
CLEANUP_INTERVAL_SECONDS = 300

# Audience flag - swap to "legal", "journalist", "hr" to retarget copy/branding.
AUDIENCE = "general"
