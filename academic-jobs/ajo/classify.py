"""Country/region inference, preference matching, and eligibility red-flag detection.

These are heuristics over free text (institution strings, posting descriptions). They are
deliberately conservative: a wrong country code or a missed flag should never silently drop a
posting. Country/region feed the preferred/excluded filters and report grouping; flags surface
eligibility traps (female-only, fresh-PhD limits, nationality/visa, military service, pending
funding, senior rank, recycled postings) that this skill repeatedly had to catch by hand.
"""

from __future__ import annotations

import re
from datetime import datetime

# --------------------------------------------------------------------------- #
# country / region inference
# --------------------------------------------------------------------------- #
# Each entry: substring (lowercase) -> (ISO2 country, region). Order matters only in that the
# first match wins; more specific tokens are listed before broad country names. Regions use:
# Europe, Asia, North America, South America, Oceania, Africa, Middle East.
_REGION_OF = {}  # ISO2 -> region, filled from the table below

# fmt: off
COUNTRY_TABLE: list[tuple[str, str, str]] = [
    # --- Korea ---
    ("korea", "KR", "Asia"), ("daejeon", "KR", "Asia"), ("seoul", "KR", "Asia"),
    ("yonsei", "KR", "Asia"), ("kaist", "KR", "Asia"), ("postech", "KR", "Asia"),
    ("kias", "KR", "Asia"), ("apctp", "KR", "Asia"), ("ibs", "KR", "Asia"),
    ("sungkyunkwan", "KR", "Asia"), ("gwangju", "KR", "Asia"), ("ulsan", "KR", "Asia"),
    # --- Germany ---
    ("germany", "DE", "Europe"), ("münchen", "DE", "Europe"), ("munich", "DE", "Europe"),
    ("karlsruhe", "DE", "Europe"), ("freiburg", "DE", "Europe"), ("dortmund", "DE", "Europe"),
    ("mainz", "DE", "Europe"), ("heidelberg", "DE", "Europe"), ("hamburg", "DE", "Europe"),
    ("desy", "DE", "Europe"), ("aachen", "DE", "Europe"), ("bonn", "DE", "Europe"),
    ("wuppertal", "DE", "Europe"), ("dresden", "DE", "Europe"), ("berlin", "DE", "Europe"),
    ("max planck", "DE", "Europe"), ("max-planck", "DE", "Europe"), ("garching", "DE", "Europe"),
    ("göttingen", "DE", "Europe"), ("goettingen", "DE", "Europe"), ("bochum", "DE", "Europe"),
    ("tübingen", "DE", "Europe"), ("würzburg", "DE", "Europe"),
    # --- Japan ---
    ("japan", "JP", "Asia"), ("tokyo", "JP", "Asia"), ("kyoto", "JP", "Asia"),
    ("riken", "JP", "Asia"), ("ithems", "JP", "Asia"), ("ipmu", "JP", "Asia"),
    ("osaka", "JP", "Asia"), ("tohoku", "JP", "Asia"), ("kek", "JP", "Asia"),
    ("nagoya", "JP", "Asia"), ("tsukuba", "JP", "Asia"), ("okinawa", "JP", "Asia"),
    ("oist", "JP", "Asia"), ("yukawa", "JP", "Asia"), ("kavli ipmu", "JP", "Asia"),
    # --- China / HK / Taiwan ---
    ("hong kong", "HK", "Asia"), ("hkust", "HK", "Asia"),
    ("taiwan", "TW", "Asia"), ("tsing hua", "TW", "Asia"), ("academia sinica", "TW", "Asia"),
    ("china", "CN", "Asia"), ("beijing", "CN", "Asia"), ("shanghai", "CN", "Asia"),
    ("tsinghua", "CN", "Asia"), ("peking", "CN", "Asia"), ("nanjing", "CN", "Asia"),
    ("shenyang", "CN", "Asia"), ("hangzhou", "CN", "Asia"), ("wuhan", "CN", "Asia"),
    ("huazhong", "CN", "Asia"), ("jiao tong", "CN", "Asia"), ("sjtu", "CN", "Asia"),
    ("ucas", "CN", "Asia"), ("ihep", "CN", "Asia"), ("ictp-ap", "CN", "Asia"),
    ("westlake", "CN", "Asia"), ("hui zhou", "CN", "Asia"), ("fudan", "CN", "Asia"),
    # --- South / SE Asia ---
    ("india", "IN", "Asia"), ("mumbai", "IN", "Asia"), ("tifr", "IN", "Asia"),
    ("kanpur", "IN", "Asia"), ("delhi", "IN", "Asia"), ("bangalore", "IN", "Asia"),
    ("icts", "IN", "Asia"), ("gurugram", "IN", "Asia"), ("iit ", "IN", "Asia"),
    ("singapore", "SG", "Asia"), ("nanyang", "SG", "Asia"),
    # --- Middle East ---
    ("israel", "IL", "Middle East"), ("ariel", "IL", "Middle East"),
    ("ilan", "IL", "Middle East"), ("technion", "IL", "Middle East"),
    ("weizmann", "IL", "Middle East"), ("tel aviv", "IL", "Middle East"),
    ("jerusalem", "IL", "Middle East"),
    ("iran", "IR", "Middle East"), ("tehran", "IR", "Middle East"),
    ("saudi", "SA", "Middle East"), ("fahd", "SA", "Middle East"), ("kaust", "SA", "Middle East"),
    ("qatar", "QA", "Middle East"), ("emirates", "AE", "Middle East"), ("abu dhabi", "AE", "Middle East"),
    ("lebanon", "LB", "Middle East"),
    ("turkey", "TR", "Middle East"), ("türkiye", "TR", "Middle East"),
    ("bogazici", "TR", "Middle East"), ("boğaziçi", "TR", "Middle East"), ("istanbul", "TR", "Middle East"),
    # --- UK / Ireland ---
    ("united kingdom", "GB", "Europe"), (" uk", "GB", "Europe"), ("u.k.", "GB", "Europe"),
    ("london", "GB", "Europe"), ("oxford", "GB", "Europe"), ("cambridge", "GB", "Europe"),
    ("durham", "GB", "Europe"), ("liverpool", "GB", "Europe"), ("manchester", "GB", "Europe"),
    ("sheffield", "GB", "Europe"), ("southampton", "GB", "Europe"), ("edinburgh", "GB", "Europe"),
    ("glasgow", "GB", "Europe"), ("imperial", "GB", "Europe"), ("swansea", "GB", "Europe"),
    ("sussex", "GB", "Europe"), ("queen mary", "GB", "Europe"), ("king's", "GB", "Europe"),
    ("birmingham", "GB", "Europe"), ("nottingham", "GB", "Europe"), ("lancaster", "GB", "Europe"),
    ("ireland", "IE", "Europe"), ("dublin", "IE", "Europe"),
    # --- Europe (continent) ---
    ("france", "FR", "Europe"), ("paris", "FR", "Europe"), ("saclay", "FR", "Europe"),
    ("annecy", "FR", "Europe"), ("lapth", "FR", "Europe"), ("grenoble", "FR", "Europe"),
    ("marseille", "FR", "Europe"), ("lyon", "FR", "Europe"), ("cppm", "FR", "Europe"),
    ("lpsc", "FR", "Europe"), ("strasbourg", "FR", "Europe"), ("montpellier", "FR", "Europe"),
    ("italy", "IT", "Europe"), ("sissa", "IT", "Europe"), ("trieste", "IT", "Europe"),
    ("gssi", "IT", "Europe"), ("aquila", "IT", "Europe"), ("rome", "IT", "Europe"),
    ("roma", "IT", "Europe"), ("padova", "IT", "Europe"), ("padua", "IT", "Europe"),
    ("ictp", "IT", "Europe"), ("torino", "IT", "Europe"), ("bologna", "IT", "Europe"),
    ("milano", "IT", "Europe"), ("napoli", "IT", "Europe"), ("pisa", "IT", "Europe"),
    ("spain", "ES", "Europe"), ("madrid", "ES", "Europe"), ("barcelona", "ES", "Europe"),
    ("zaragoza", "ES", "Europe"), ("valencia", "ES", "Europe"), ("ific", "ES", "Europe"),
    ("ifae", "ES", "Europe"), ("basque", "ES", "Europe"), ("santander", "ES", "Europe"),
    ("portugal", "PT", "Europe"), ("lisbon", "PT", "Europe"), ("lisboa", "PT", "Europe"),
    ("switzerland", "CH", "Europe"), ("geneva", "CH", "Europe"), ("genève", "CH", "Europe"),
    ("cern", "CH", "Europe"), ("eth", "CH", "Europe"), ("epfl", "CH", "Europe"),
    ("zurich", "CH", "Europe"), ("zürich", "CH", "Europe"), ("psi", "CH", "Europe"),
    ("netherlands", "NL", "Europe"), ("amsterdam", "NL", "Europe"), ("nikhef", "NL", "Europe"),
    ("nijmegen", "NL", "Europe"), ("utrecht", "NL", "Europe"), ("leiden", "NL", "Europe"),
    ("belgium", "BE", "Europe"), ("louvain", "BE", "Europe"), ("brussels", "BE", "Europe"),
    ("gent", "BE", "Europe"), ("ghent", "BE", "Europe"),
    ("austria", "AT", "Europe"), ("vienna", "AT", "Europe"), ("wien", "AT", "Europe"),
    ("sweden", "SE", "Europe"), ("uppsala", "SE", "Europe"), ("stockholm", "SE", "Europe"),
    ("lund", "SE", "Europe"), ("nordita", "SE", "Europe"), ("chalmers", "SE", "Europe"),
    ("norway", "NO", "Europe"), ("oslo", "NO", "Europe"), ("ntnu", "NO", "Europe"),
    ("denmark", "DK", "Europe"), ("copenhagen", "DK", "Europe"), ("bohr", "DK", "Europe"),
    ("finland", "FI", "Europe"), ("helsinki", "FI", "Europe"),
    ("poland", "PL", "Europe"), ("warsaw", "PL", "Europe"), ("krakow", "PL", "Europe"),
    ("cracow", "PL", "Europe"), ("ncbj", "PL", "Europe"),
    ("greece", "GR", "Europe"), ("athens", "GR", "Europe"),
    ("czech", "CZ", "Europe"), ("prague", "CZ", "Europe"),
    ("hungary", "HU", "Europe"), ("budapest", "HU", "Europe"),
    ("cyprus", "CY", "Europe"),
    # --- North America ---
    ("usa", "US", "North America"), ("united states", "US", "North America"),
    ("u.s.a", "US", "North America"), ("fermilab", "US", "North America"),
    ("brookhaven", "US", "North America"), ("berkeley", "US", "North America"),
    ("stanford", "US", "North America"), ("mit", "US", "North America"),
    ("harvard", "US", "North America"), ("princeton", "US", "North America"),
    ("cornell", "US", "North America"), ("chicago", "US", "North America"),
    ("cincinnati", "US", "North America"), ("stony brook", "US", "North America"),
    ("michigan", "US", "North America"), ("flatiron", "US", "North America"),
    ("caltech", "US", "North America"), ("duke", "US", "North America"),
    ("washington", "US", "North America"), ("los alamos", "US", "North America"),
    ("kansas", "US", "North America"), ("ohio", "US", "North America"),
    ("new york", "US", "North America"), ("california", "US", "North America"),
    ("massachusetts", "US", "North America"), ("illinois", "US", "North America"),
    ("canada", "CA", "North America"), ("toronto", "CA", "North America"),
    ("perimeter", "CA", "North America"), ("mcgill", "CA", "North America"),
    ("vancouver", "CA", "North America"), ("triumf", "CA", "North America"),
    ("montreal", "CA", "North America"), ("waterloo", "CA", "North America"),
    ("sherbrooke", "CA", "North America"), ("regina", "CA", "North America"),
    ("mexico", "MX", "North America"), ("unam", "MX", "North America"),
    # --- South America ---
    ("brazil", "BR", "South America"), ("sao paulo", "BR", "South America"),
    ("são paulo", "BR", "South America"), ("rio de janeiro", "BR", "South America"),
    ("chile", "CL", "South America"), ("santiago", "CL", "South America"),
    ("valparaiso", "CL", "South America"), ("valparaíso", "CL", "South America"),
    ("argentina", "AR", "South America"), ("buenos aires", "AR", "South America"),
    ("colombia", "CO", "South America"),
    # --- Oceania / Africa ---
    ("australia", "AU", "Oceania"), ("sydney", "AU", "Oceania"), ("melbourne", "AU", "Oceania"),
    ("new zealand", "NZ", "Oceania"),
    ("south africa", "ZA", "Africa"), ("witwatersrand", "ZA", "Africa"),
    ("cape town", "ZA", "Africa"),
]
# fmt: on

for _sub, _cc, _reg in COUNTRY_TABLE:
    _REGION_OF.setdefault(_cc, _reg)

# country name -> ISO2, so a selector like "Korea" or "Germany" works
_NAME_TO_CODE = {
    "korea": "KR", "south korea": "KR", "germany": "DE", "japan": "JP",
    "hong kong": "HK", "taiwan": "TW", "china": "CN", "india": "IN",
    "singapore": "SG", "israel": "IL", "iran": "IR", "saudi arabia": "SA",
    "qatar": "QA", "uae": "AE", "lebanon": "LB", "turkey": "TR", "türkiye": "TR",
    "uk": "GB", "united kingdom": "GB", "britain": "GB", "england": "GB",
    "ireland": "IE", "france": "FR", "italy": "IT", "spain": "ES", "portugal": "PT",
    "switzerland": "CH", "netherlands": "NL", "belgium": "BE", "austria": "AT",
    "sweden": "SE", "norway": "NO", "denmark": "DK", "finland": "FI", "poland": "PL",
    "greece": "GR", "czech republic": "CZ", "czechia": "CZ", "hungary": "HU",
    "cyprus": "CY", "usa": "US", "united states": "US", "america": "US",
    "canada": "CA", "mexico": "MX", "brazil": "BR", "chile": "CL", "argentina": "AR",
    "colombia": "CO", "australia": "AU", "new zealand": "NZ", "south africa": "ZA",
}

# region alias -> canonical region (so "EU"/"europe" match the Europe region)
_REGION_ALIASES = {
    "europe": "Europe", "eu": "Europe", "european": "Europe",
    "asia": "Asia", "asian": "Asia", "asia-pacific": "Asia", "apac": "Asia",
    "north america": "North America", "na": "North America", "americas": "North America",
    "south america": "South America", "latin america": "South America",
    "oceania": "Oceania", "australia/nz": "Oceania",
    "africa": "Africa", "middle east": "Middle East", "mena": "Middle East",
}


def infer_country(institution: str | None, region_hint: str | None = None) -> tuple[str | None, str | None]:
    """Best-effort (ISO2, region) from an institution string.

    region_hint is the InspireHEP `regions` value (e.g. "Europe"); used only to fill the region
    when the institution string yields no country match.
    """
    s = (institution or "").lower()
    for sub, cc, reg in COUNTRY_TABLE:
        if sub in s:
            return cc, reg
    # no country token; fall back to a region hint if it is a recognised region
    if region_hint:
        canon = _REGION_ALIASES.get(region_hint.strip().lower())
        if canon:
            return None, canon
        # InspireHEP already uses canonical names; accept as-is
        return None, region_hint.strip()
    return None, None


def _selector_set(selectors) -> set[str]:
    """Flatten preferred tiers / excluded list into a comparable token set (upper-cased)."""
    out: set[str] = set()
    for sel in selectors or []:
        if isinstance(sel, (list, tuple)):
            out |= _selector_set(sel)
        elif sel and str(sel).strip():
            out.add(str(sel).strip())
    return out


def country_matches(code: str | None, region: str | None, selectors) -> bool:
    """True if a posting's (code, region) matches any selector.

    A selector may be an ISO2 code ("KR"), a country name ("Korea"), or a region alias
    ("Europe", "Asia"). Matching is case-insensitive.
    """
    toks = _selector_set(selectors)
    if not toks:
        return False
    code_u = (code or "").upper()
    region_l = (region or "").lower()
    for tok in toks:
        t = tok.strip()
        tl = t.lower()
        if code_u and t.upper() == code_u:
            return True
        if tl in _NAME_TO_CODE and _NAME_TO_CODE[tl] == code_u and code_u:
            return True
        canon = _REGION_ALIASES.get(tl)
        if canon and region_l and canon.lower() == region_l:
            return True
        # also allow a raw region name selector ("Middle East") to match the region
        if region_l and tl == region_l:
            return True
    return False


def preference_tier(code: str | None, region: str | None, preferred_tiers) -> int:
    """0-based index of the first preferred tier the posting belongs to.

    preferred_tiers is a list of tiers, each tier a list of selectors. Returns the tier index
    (lower = more preferred), or len(preferred_tiers) when the posting is in no tier.
    """
    tiers = preferred_tiers or []
    for i, tier in enumerate(tiers):
        if country_matches(code, region, tier if isinstance(tier, (list, tuple)) else [tier]):
            return i
    return len(tiers)


# --------------------------------------------------------------------------- #
# eligibility / red-flag detection
# --------------------------------------------------------------------------- #
_FLAG_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("female-only", re.compile(r"\bfemale[\s-]*only\b|\bwomen[\s-]*only\b|only\s+female|\[\s*female\s+only\s*\]", re.I)),
    ("fresh-phd-limit", re.compile(
        r"within\s+(?:the\s+)?(?:last\s+)?(?:one|two|three|four|five|\d+)\s+years?\s+"
        r"(?:of|after|from|since)[^.]{0,40}(?:ph\.?\s?d|doctora|degree)"
        r"|(?:no(?:t)?\s+(?:more\s+than|exceed)|less\s+than|not\s+exceeding|maximum\s+of|up\s+to)\s+"
        r"\w+\s+years?[^.]{0,30}(?:ph\.?\s?d|doctora|degree)"
        r"|\bfresh\s+ph\.?\s?d|\brecent\s+ph\.?\s?d", re.I)),
    ("nationality-restricted", re.compile(
        r"(?:only|exclusively|must\s+be|reserved\s+for|open\s+only\s+to)[^.]{0,40}"
        r"(?:citizen|national|nationality|passport|permanent\s+resident)"
        r"|(?:citizens?|nationals?)\s+of\s+[A-Z]"
        r"|lived\s+in\s+russia|affected\s+by\s+the\s+war", re.I)),
    ("military-service-clause", re.compile(r"전문연구요원|병역|military\s+service\s+(?:obligation|exempt|requirement)", re.I)),
    ("funding-pending", re.compile(
        r"pending\s+(?:funding|the\s+confirmation|budget)|subject\s+to\s+(?:funding|the\s+availability\s+of\s+funding|budget)"
        r"|funding\s+(?:confirmation|is\s+pending)|contingent\s+(?:on|upon)\s+funding", re.I)),
]

_PROF_RE = re.compile(r"\bprofessor\b", re.I)
_JUNIOR_RANK_RE = re.compile(r"assistant|associate|tenure[\s-]?track|non[\s-]?tenure|postdoc|junior|lecturer|fellow", re.I)
_YEAR_CTX_RE = re.compile(
    r"(?:deadline|apply(?:ing)?\s+by|by\s+the|before\s+the|no\s+later\s+than|received\s+by|"
    r"closing\s+date|decision\s+(?:by|on)|review\s+begins?(?:\s+on)?)[^.]{0,40}?(20\d{2})", re.I)


def detect_flags(
    title: str | None,
    position_type: str | None,
    description: str | None,
    deadline_dt: datetime | str | None = None,
) -> list[str]:
    """Return a sorted list of eligibility / caution flags found in the posting text.

    Flags are warnings, not filters: they are surfaced so the curator (and reader) sees an
    eligibility trap up front. Detection is conservative; absence of a flag is not a guarantee.
    """
    hay = " ".join(x for x in (title, description) if x)
    flags: set[str] = set()
    if hay.strip():
        for name, pat in _FLAG_PATTERNS:
            if pat.search(hay):
                flags.add(name)

    # senior rank: title/type says "Professor" with no junior/assistant qualifier
    rankhay = " ".join(x for x in (title, position_type) if x)
    if _PROF_RE.search(rankhay) and not _JUNIOR_RANK_RE.search(rankhay):
        flags.add("senior:professor")

    # recycled / stale: a deadline-context year in the body earlier than the effective year
    dyear = _deadline_year(deadline_dt)
    if dyear and description:
        ctx_years = [int(y) for y in _YEAR_CTX_RE.findall(description)]
        if ctx_years and min(ctx_years) < dyear:
            flags.add("date-mismatch(stale?)")

    return sorted(flags)


def _deadline_year(deadline_dt) -> int | None:
    if isinstance(deadline_dt, datetime):
        return deadline_dt.year
    if isinstance(deadline_dt, str):
        m = re.search(r"(20\d{2})", deadline_dt)
        if m:
            return int(m.group(1))
    return None
