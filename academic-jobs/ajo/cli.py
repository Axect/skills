"""`ajo` command-line interface.

Commands:
  config     view / edit field presets
  fetch      search AJO, keep valid postings, store + flag new
  list       query stored postings
  show       fetch + parse one detail page
  mark-seen  clear the 'new' flag
  prune      delete expired postings

Every command accepts --json for machine-readable output (consumed by the skill).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from . import DB_PATH
from . import config as cfgmod
from . import db as dbmod
from . import fetch as fetchmod


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _split(arg: str | None) -> list[str] | None:
    if arg is None:
        return None
    return [x.strip() for x in arg.split(",") if x.strip()]


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _row_view(j: dict) -> dict:
    return {
        "id": j["id"],
        "new": bool(j.get("is_new", 0)),
        "deadline": j.get("deadline_raw") or ("rolling" if j.get("status") == "rolling" else ""),
        "type": j.get("position_type") or "",
        "title": j.get("title") or j.get("code") or "",
        "institution": j.get("institution") or "",
        "url": j.get("url") or "",
        "matched": j.get("matched_keywords") or "",
    }


def _print_table(jobs: list[dict]) -> None:
    if not jobs:
        print("(no postings)")
        return
    print(f"{'NEW':3} {'DEADLINE':17} {'TYPE':12} TITLE")
    print("-" * 78)
    for j in jobs:
        v = _row_view(j)
        flag = "NEW" if v["new"] else ""
        dl = (v["deadline"] or "")[:17]
        typ = (v["type"] or "")[:12]
        title = v["title"]
        inst = f"  [{v['institution']}]" if v["institution"] else ""
        print(f"{flag:3} {dl:17} {typ:12} #{j['id']} {title}{inst}")
    print(f"\n{len(jobs)} posting(s).")


def _output(jobs: list[dict], as_json: bool, extra: dict | None = None) -> None:
    if as_json:
        payload = {"count": len(jobs), "jobs": [_row_view(j) | {"raw": j} for j in jobs]}
        if extra:
            payload.update(extra)
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        _print_table(jobs)
        if extra and extra.get("stats"):
            _eprint(f"stats: {json.dumps(extra['stats'], default=str)}")


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_config(args: argparse.Namespace) -> int:
    cfg = cfgmod.load_config()
    if args.set_preset:
        cfgmod.set_preset(
            cfg,
            args.set_preset,
            keywords=_split(args.keywords),
            position_types=_split(args.types),
            countries=_split(args.countries),
            make_default=args.make_default,
        )
        cfgmod.save_config(cfg)
        print(f"preset '{args.set_preset}' saved.")
        cfg = cfgmod.load_config()

    if args.json:
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
    else:
        print(f"config: {cfgmod.CONFIG_PATH}")
        print(f"default preset: {cfg['default_preset']}\n")
        for name, p in cfg["presets"].items():
            mark = " (default)" if name == cfg["default_preset"] else ""
            print(f"[{name}]{mark}")
            print(f"  keywords:       {', '.join(p['keywords']) or '-'}")
            print(f"  position_types: {', '.join(p['position_types']) or '-'}")
            print(f"  countries:      {', '.join(p['countries']) or '-'}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    now = datetime.now()
    if args.keyword:
        keywords = [args.keyword]
        position_types, countries = _split(args.types) or [], _split(args.countries) or []
        preset_name = None
    else:
        cfg = cfgmod.load_config()
        try:
            preset_name, preset = cfgmod.get_preset(cfg, args.preset)
        except KeyError:
            _eprint(f"unknown preset: {args.preset}")
            return 2
        keywords = preset["keywords"]
        position_types = _split(args.types) if args.types else preset["position_types"]
        countries = _split(args.countries) if args.countries else preset["countries"]
        if not keywords:
            _eprint(f"preset '{preset_name}' has no keywords. Set some with `ajo config`.")
            return 2

    session = fetchmod.make_session()
    log = (lambda m: None) if args.json else _eprint
    jobs, stats = fetchmod.search_valid(
        session,
        keywords,
        now=now,
        limit=args.limit,
        include_rolling=args.include_rolling,
        fetch_details=not args.fast,
        position_types=position_types,
        countries=countries,
        log=log,
    )

    conn = dbmod.connect()
    new_ids = []
    for j in jobs:
        is_new = dbmod.upsert_job(conn, j)
        j["is_new"] = 1 if is_new else 0
        if is_new:
            new_ids.append(j["id"])
    dbmod.set_meta(conn, "last_fetch_at", now.replace(microsecond=0).isoformat())
    conn.close()

    stats["new"] = len(new_ids)
    stats["stored"] = len(jobs)
    _output(jobs, args.json, extra={"stats": stats})
    if not args.json:
        _eprint(f"{len(new_ids)} new posting(s) since last fetch.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = dbmod.connect()
    jobs = dbmod.query_jobs(
        conn,
        valid_only=args.valid,
        new_only=args.new,
        keyword_like=args.keyword_like,
    )
    conn.close()
    _output(jobs, args.json)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    session = fetchmod.make_session()
    try:
        det = fetchmod.fetch_detail(session, args.id)
    except Exception as e:  # noqa: BLE001
        _eprint(f"failed to fetch #{args.id}: {e}")
        return 1
    det["deadline_dt"] = (
        det["deadline_dt"].isoformat() if isinstance(det.get("deadline_dt"), datetime) else det.get("deadline_dt")
    )
    if args.json:
        print(json.dumps(det, ensure_ascii=False, indent=2, default=str))
    else:
        for k in ("id", "institution", "position_type", "subject_areas", "deadline_raw", "url"):
            print(f"{k:15}: {det.get(k) or '-'}")
    return 0


def cmd_mark_seen(args: argparse.Namespace) -> int:
    conn = dbmod.connect()
    ids = args.ids if args.ids else None
    if args.all:
        ids = None
    elif not args.ids:
        _eprint("provide ids or --all")
        conn.close()
        return 2
    n = dbmod.mark_seen(conn, ids)
    conn.close()
    print(f"marked {n} posting(s) as seen.")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    conn = dbmod.connect()
    n = dbmod.prune_expired(conn)
    conn.close()
    print(f"pruned {n} expired posting(s).")
    return 0


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ajo", description="Academic Jobs Online fetcher")
    p.add_argument("--db", help=f"override DB path (default {DB_PATH})")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("config", help="view/edit field presets")
    c.add_argument("--show", action="store_true", help="(default) show config")
    c.add_argument("--set-preset", metavar="NAME", help="create/update a preset")
    c.add_argument("--keywords", help="comma-separated keywords for the preset")
    c.add_argument("--types", help="comma-separated position types (substring match)")
    c.add_argument("--countries", help="comma-separated country/institution filters")
    c.add_argument("--make-default", action="store_true", help="set this preset as default")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_config)

    f = sub.add_parser("fetch", help="search AJO and store valid postings")
    g = f.add_mutually_exclusive_group()
    g.add_argument("--preset", help="preset name (default: config default)")
    g.add_argument("--keyword", help="single ad-hoc keyword instead of a preset")
    f.add_argument("--limit", type=int, default=fetchmod.DEFAULT_LIMIT, help="page size")
    f.add_argument("--include-rolling", action="store_true",
                   help="include postings with no deadline at all (truly open-ended)")
    f.add_argument("--fast", action="store_true",
                   help="list-only pass: skip detail pages (faster but deadlines are approximate)")
    f.add_argument("--types", help="override preset position_types filter")
    f.add_argument("--countries", help="override preset countries filter")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_fetch)

    ls = sub.add_parser("list", help="query stored postings")
    ls.add_argument("--valid", action="store_true", help="only postings still open now")
    ls.add_argument("--new", action="store_true", help="only postings flagged new")
    ls.add_argument("--keyword-like", help="substring filter on title/institution/subject")
    ls.add_argument("--json", action="store_true")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="fetch + parse one detail page")
    sh.add_argument("id", type=int)
    sh.add_argument("--json", action="store_true")
    sh.set_defaults(func=cmd_show)

    ms = sub.add_parser("mark-seen", help="clear the new flag")
    ms.add_argument("ids", nargs="*", type=int)
    ms.add_argument("--all", action="store_true")
    ms.set_defaults(func=cmd_mark_seen)

    pr = sub.add_parser("prune", help="delete expired postings")
    pr.set_defaults(func=cmd_prune)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "db", None):
        import ajo
        from pathlib import Path
        ajo.DB_PATH = Path(args.db)
        dbmod.DB_PATH = Path(args.db)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
