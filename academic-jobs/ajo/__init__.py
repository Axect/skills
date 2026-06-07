"""academic-jobs: fetch valid postings from Academic Jobs Online."""

__version__ = "0.1.0"

# Shared filesystem locations.
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("AJO_DATA_DIR", Path.home() / ".local/share/academic-jobs"))
DB_PATH = DATA_DIR / "jobs.db"
CONFIG_PATH = DATA_DIR / "config.toml"

BASE_URL = "https://academicjobsonline.org"
