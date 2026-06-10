"""hep-rumor-mill: analyze the HEP-theory postdoc rumor mill and offer-holders' records."""

__version__ = "0.1.0"

import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("PRM_DATA_DIR", Path.home() / ".local/share/hep-rumor-mill"))
DB_PATH = DATA_DIR / "rumor.db"

# InspireHEP author/literature, OpenAlex, Semantic Scholar all serve clean public JSON.
USER_AGENT = "hep-rumor-mill/0.1 (academic job-market research; contact via local user)"
