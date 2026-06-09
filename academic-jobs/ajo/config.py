"""Field presets stored as TOML at ~/.local/share/academic-jobs/config.toml.

A preset is a named search profile:
    [presets.physics-ml]
    keywords            = ["cosmology", "machine learning", "dark matter"]
    position_types      = ["postdoc"]            # substring match on AJO type / InspireHEP ranks
    countries           = []                     # hard include filter (substring on institution)
    preferred_countries = [["KR", "DE"], ["JP", "HK", "GB", "US"]]  # ordered tiers (soft sort)
    excluded_countries  = ["IN", "IL"]           # hard drop (ISO2 / country name / region alias)
    sources             = ["ajo", "inspire"]     # which job boards to search

`preferred_countries` and `excluded_countries` accept ISO2 codes ("KR"), country names
("Korea"), or region aliases ("Europe", "Asia"). Excluded postings are dropped at fetch;
preferred tiers only reorder results (tier 0 first). `countries` is the older hard include
filter and still works alongside them.

Default preset 'physics-ml' is seeded on first run.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from . import CONFIG_PATH

DEFAULT_PRESET = "physics-ml"
ALL_SOURCES = ["ajo", "inspire"]

DEFAULT_CONFIG = {
    "default_preset": DEFAULT_PRESET,
    "presets": {
        DEFAULT_PRESET: {
            "keywords": [
                "cosmology",
                "dark matter",
                "machine learning",
                "astrophysics",
            ],
            "position_types": ["postdoc"],
            "countries": [],
            "preferred_countries": [],
            "excluded_countries": [],
            "sources": list(ALL_SOURCES),
        }
    },
}


def _dump_toml(cfg: dict) -> str:
    """Minimal TOML writer (stdlib has no tomli-w). Handles our flat schema."""
    lines: list[str] = []
    dp = cfg.get("default_preset", DEFAULT_PRESET)
    lines.append(f'default_preset = "{dp}"')
    lines.append("")
    for name, p in cfg.get("presets", {}).items():
        lines.append(f"[presets.{_key(name)}]")
        for field in ("keywords", "position_types", "countries"):
            vals = p.get(field, [])
            arr = ", ".join(f'"{_esc(v)}"' for v in vals)
            lines.append(f"{field} = [{arr}]")
        # preferred_countries is a list of tiers (list of lists)
        tiers = p.get("preferred_countries", []) or []
        tier_strs = [
            "[" + ", ".join(f'"{_esc(v)}"' for v in (t if isinstance(t, (list, tuple)) else [t])) + "]"
            for t in tiers
        ]
        lines.append(f"preferred_countries = [{', '.join(tier_strs)}]")
        excl = p.get("excluded_countries", []) or []
        lines.append("excluded_countries = [" + ", ".join(f'"{_esc(v)}"' for v in excl) + "]")
        srcs = p.get("sources", [])
        lines.append("sources = [" + ", ".join(f'"{_esc(v)}"' for v in srcs) + "]")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _key(name: str) -> str:
    # quote preset names that are not bare keys
    import re
    return name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else f'"{_esc(name)}"'


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def load_config() -> dict:
    """Load config, creating the default file on first use."""
    path = Path(CONFIG_PATH)
    if not path.exists():
        save_config(DEFAULT_CONFIG)
        return _normalize(DEFAULT_CONFIG)
    with path.open("rb") as f:
        cfg = tomllib.load(f)
    return _normalize(cfg)


def save_config(cfg: dict) -> None:
    path = Path(CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_toml(cfg))


def _normalize(cfg: dict) -> dict:
    cfg.setdefault("default_preset", DEFAULT_PRESET)
    cfg.setdefault("presets", {})
    for p in cfg["presets"].values():
        p.setdefault("keywords", [])
        p.setdefault("position_types", [])
        p.setdefault("countries", [])
        p.setdefault("preferred_countries", [])
        p.setdefault("excluded_countries", [])
        # normalize tiers to a list of lists (tolerate a flat list as a single tier)
        tiers = p.get("preferred_countries") or []
        if tiers and all(not isinstance(t, (list, tuple)) for t in tiers):
            tiers = [list(tiers)]
        p["preferred_countries"] = [list(t) for t in tiers]
        # presets predating multi-source support search both boards by default
        p.setdefault("sources", list(ALL_SOURCES))
    return cfg


def get_preset(cfg: dict, name: str | None) -> tuple[str, dict]:
    """Resolve a preset by name (or default). Raises KeyError if unknown."""
    name = name or cfg.get("default_preset", DEFAULT_PRESET)
    if name not in cfg["presets"]:
        raise KeyError(name)
    return name, cfg["presets"][name]


def set_preset(
    cfg: dict,
    name: str,
    *,
    keywords: list[str] | None = None,
    position_types: list[str] | None = None,
    countries: list[str] | None = None,
    preferred_countries: list | None = None,
    excluded_countries: list[str] | None = None,
    sources: list[str] | None = None,
    make_default: bool = False,
) -> dict:
    p = cfg["presets"].get(
        name,
        {
            "keywords": [], "position_types": [], "countries": [],
            "preferred_countries": [], "excluded_countries": [], "sources": list(ALL_SOURCES),
        },
    )
    if keywords is not None:
        p["keywords"] = keywords
    if position_types is not None:
        p["position_types"] = position_types
    if countries is not None:
        p["countries"] = countries
    if preferred_countries is not None:
        # accept either a flat list (single tier) or a list of tiers
        tiers = preferred_countries
        if tiers and all(not isinstance(t, (list, tuple)) for t in tiers):
            tiers = [list(tiers)]
        p["preferred_countries"] = [list(t) for t in tiers]
    if excluded_countries is not None:
        p["excluded_countries"] = excluded_countries
    if sources is not None:
        invalid = [s for s in sources if s not in ALL_SOURCES]
        if invalid:
            raise ValueError(f"unknown source(s): {invalid}; valid: {ALL_SOURCES}")
        p["sources"] = sources
    cfg["presets"][name] = p
    if make_default:
        cfg["default_preset"] = name
    return cfg
