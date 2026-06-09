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
from . import classify as classifymod
from . import config as cfgmod
from . import db as dbmod
from . import fetch as fetchmod
from . import inspire as inspiremod


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _split(arg: str | None) -> list[str] | None:
    if arg is None:
        return None
    return [x.strip() for x in arg.split(",") if x.strip()]


def _split_tiers(arg: str | None) -> list[list[str]] | None:
    """Parse tiered country preferences: '; ' separates tiers, ',' separates entries.

    e.g. "KR,DE; JP,HK,GB,US" -> [["KR","DE"], ["JP","HK","GB","US"]].
    """
    if arg is None:
        return None
    tiers = []
    for chunk in arg.split(";"):
        entries = [x.strip() for x in chunk.split(",") if x.strip()]
        if entries:
            tiers.append(entries)
    return tiers


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _row_view(j: dict) -> dict:
    return {
        "id": j["id"],
        "source": j.get("source") or "ajo",
        "new": bool(j.get("is_new", 0)),
        "deadline": j.get("deadline_raw") or ("rolling" if j.get("status") == "rolling" else ""),
        "type": j.get("position_type") or "",
        "title": j.get("title") or j.get("code") or "",
        "institution": j.get("institution") or "",
        "country": j.get("country") or "",
        "region": j.get("region") or "",
        "pref_tier": j.get("pref_tier"),
        "flags": j.get("flags") or "",
        "url": j.get("url") or "",
        "matched": j.get("matched_keywords") or "",
    }


def _print_table(jobs: list[dict]) -> None:
    if not jobs:
        print("(no postings)")
        return
    print(f"{'NEW':3} {'SRC':8} {'CC':3} {'DEADLINE':17} {'TYPE':12} TITLE")
    print("-" * 92)
    for j in jobs:
        v = _row_view(j)
        flag = "NEW" if v["new"] else ""
        src = (v["source"] or "")[:8]
        cc = (v["country"] or "")[:2]
        dl = (v["deadline"] or "")[:17]
        typ = (v["type"] or "")[:12]
        title = v["title"]
        inst = f"  [{v['institution']}]" if v["institution"] else ""
        warn = f"  ⚠{v['flags']}" if v["flags"] else ""
        print(f"{flag:3} {src:8} {cc:3} {dl:17} {typ:12} {v['source']}#{j['id']} {title}{inst}{warn}")
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
        try:
            cfgmod.set_preset(
                cfg,
                args.set_preset,
                keywords=_split(args.keywords),
                position_types=_split(args.types),
                countries=_split(args.countries),
                preferred_countries=_split_tiers(args.preferred),
                excluded_countries=_split(args.excluded),
                sources=_split(args.sources),
                make_default=args.make_default,
            )
        except ValueError as e:
            _eprint(str(e))
            return 2
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
            tiers = p.get("preferred_countries", []) or []
            tier_str = " > ".join("[" + ", ".join(t) + "]" for t in tiers) or "-"
            print(f"[{name}]{mark}")
            print(f"  keywords:            {', '.join(p['keywords']) or '-'}")
            print(f"  position_types:      {', '.join(p['position_types']) or '-'}")
            print(f"  countries:           {', '.join(p['countries']) or '-'}")
            print(f"  preferred_countries: {tier_str}")
            print(f"  excluded_countries:  {', '.join(p.get('excluded_countries', [])) or '-'}")
            print(f"  sources:             {', '.join(p.get('sources', [])) or '-'}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    now = datetime.now()
    if args.keyword:
        keywords = [args.keyword]
        position_types, countries = _split(args.types) or [], _split(args.countries) or []
        preferred_tiers = _split_tiers(args.preferred) or []
        excluded_countries = _split(args.excluded) or []
        preset_sources = list(cfgmod.ALL_SOURCES)
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
        preferred_tiers = (
            _split_tiers(args.preferred) if args.preferred else preset.get("preferred_countries", [])
        )
        excluded_countries = (
            _split(args.excluded) if args.excluded else preset.get("excluded_countries", [])
        )
        preset_sources = preset.get("sources", list(cfgmod.ALL_SOURCES))
        if not keywords:
            _eprint(f"preset '{preset_name}' has no keywords. Set some with `ajo config`.")
            return 2

    # resolve which boards to hit: --source overrides the preset's sources
    if args.source and args.source != "both":
        sources = [args.source]
    elif args.source == "both":
        sources = list(cfgmod.ALL_SOURCES)
    else:
        sources = [s for s in preset_sources if s in cfgmod.ALL_SOURCES] or list(cfgmod.ALL_SOURCES)

    log = (lambda m: None) if args.json else _eprint
    all_jobs: list[dict] = []
    source_stats: dict[str, dict] = {}

    if "ajo" in sources:
        jobs, stats = fetchmod.search_valid(
            fetchmod.make_session(),
            keywords,
            now=now,
            limit=args.limit,
            include_rolling=args.include_rolling,
            fetch_details=not args.fast,
            position_types=position_types,
            countries=countries,
            excluded_countries=excluded_countries,
            preferred_tiers=preferred_tiers,
            detail_cap=args.detail_cap,
            log=log,
        )
        all_jobs.extend(jobs)
        source_stats["ajo"] = stats

    if "inspire" in sources:
        jobs, stats = inspiremod.search_valid(
            inspiremod.make_session(),
            keywords,
            now=now,
            limit=args.limit,
            include_rolling=args.include_rolling,
            position_types=position_types,
            countries=countries,
            excluded_countries=excluded_countries,
            preferred_tiers=preferred_tiers,
            log=log,
        )
        all_jobs.extend(jobs)
        source_stats["inspire"] = stats

    conn = dbmod.connect()
    new_ids = []
    for j in all_jobs:
        is_new = dbmod.upsert_job(conn, j)
        j["is_new"] = 1 if is_new else 0
        if is_new:
            new_ids.append((j.get("source", "ajo"), j["id"]))
    dbmod.set_meta(conn, "last_fetch_at", now.replace(microsecond=0).isoformat())
    conn.close()

    all_jobs.sort(key=lambda j: (
        j.get("pref_tier", 99), j["deadline_dt"] is None, j["deadline_dt"] or ""
    ))
    stats = {
        "sources": sources,
        "per_source": source_stats,
        "new": len(new_ids),
        "stored": len(all_jobs),
    }
    _output(all_jobs, args.json, extra={"stats": stats})
    if not args.json:
        _eprint(f"{len(new_ids)} new posting(s) since last fetch across {', '.join(sources)}.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = dbmod.connect()
    jobs = dbmod.query_jobs(
        conn,
        valid_only=args.valid,
        new_only=args.new,
        keyword_like=args.keyword_like,
        source=args.source,
    )
    conn.close()
    _output(jobs, args.json)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show one posting. Reads the stored row first (incl. captured description); only hits
    the network when the row is missing, lacks a description, or --refresh is passed."""
    fields = ("source", "id", "code", "title", "institution", "country", "region",
              "position_type", "subject_areas", "deadline_raw", "flags", "contact",
              "url", "description")

    det = None
    if not args.refresh:
        conn = dbmod.connect()
        rows = dbmod.query_jobs(conn, source=args.source)
        conn.close()
        for r in rows:
            if r["id"] == args.id:
                if r.get("description") or r.get("detail_fetched"):
                    det = r
                break

    if det is None:
        session = inspiremod.make_session() if args.source == "inspire" else fetchmod.make_session()
        fetch_detail = inspiremod.fetch_detail if args.source == "inspire" else fetchmod.fetch_detail
        try:
            det = fetch_detail(session, args.id)
        except Exception as e:  # noqa: BLE001
            _eprint(f"failed to fetch {args.source}#{args.id}: {e}")
            return 1
        det["source"] = args.source
        # compute country/region/flags so a fresh fetch matches the stored shape
        eff = det.get("effective_deadline_dt") or det.get("deadline_dt")
        code, region = classifymod.infer_country(det.get("institution"), det.get("regions"))
        det["country"], det["region"] = code, region
        det["flags"] = ",".join(classifymod.detect_flags(
            det.get("title"), det.get("position_type"), det.get("description"), eff
        )) or None
        # persist what we just fetched so future shows/reports have it
        _persist_detail(args.source, args.id, det)

    det["deadline_dt"] = (
        det["deadline_dt"].isoformat() if isinstance(det.get("deadline_dt"), datetime) else det.get("deadline_dt")
    )
    if args.json:
        print(json.dumps(det, ensure_ascii=False, indent=2, default=str))
    else:
        for k in fields:
            if det.get(k):
                print(f"{k:15}: {det.get(k)}")
    return 0


def _persist_detail(source: str, jid: int, det: dict) -> None:
    """Best-effort: write a freshly fetched detail back into an existing stored row."""
    conn = dbmod.connect()
    try:
        existing = [r for r in dbmod.query_jobs(conn, source=source) if r["id"] == jid]
        if existing:
            dbmod.upsert_job(conn, {
                "id": jid, "source": source,
                "code": det.get("code") or det.get("position_code"),
                "title": det.get("title"),
                "institution": det.get("institution"),
                "position_type": det.get("position_type"),
                "subject_areas": det.get("subject_areas"),
                "deadline_raw": existing[0].get("deadline_raw"),
                "deadline_dt": existing[0].get("deadline_dt"),
                "status": existing[0].get("status"),
                "url": det.get("url") or existing[0].get("url"),
                "matched_keywords": existing[0].get("matched_keywords", ""),
                "description": det.get("description"),
                "contact": det.get("contact"),
                "country": det.get("country"),
                "region": det.get("region"),
                "flags": det.get("flags"),
            })
    finally:
        conn.close()


def cmd_enrich(args: argparse.Namespace) -> int:
    """Fetch detail bodies for stored postings that lack them (detail_fetched=0).

    Lets a truncated AJO run be completed over several polite passes. InspireHEP rows are
    enriched by hitting the API record for the description/contact.
    """
    import time
    conn = dbmod.connect()
    rows = dbmod.query_jobs(conn, valid_only=not args.include_expired, source=args.source)
    conn.close()
    pending = [r for r in rows if not r.get("detail_fetched")]
    if args.source:
        pending = [r for r in pending if r["source"] == args.source]
    cap = args.detail_cap if args.detail_cap and args.detail_cap > 0 else fetchmod.DETAIL_FETCH_CAP
    pending = pending[:cap]
    if not pending:
        print("nothing to enrich (all stored postings already have details).")
        return 0

    ajo_sess = fetchmod.make_session()
    insp_sess = inspiremod.make_session()
    done = 0
    for i, r in enumerate(pending):
        src = r["source"]
        try:
            if src == "inspire":
                det = inspiremod.fetch_detail(insp_sess, r["id"])
            else:
                det = fetchmod.fetch_detail(ajo_sess, r["id"])
        except Exception as e:  # noqa: BLE001
            _eprint(f"  enrich {src}#{r['id']} failed: {e}")
            continue
        eff = r.get("deadline_dt")
        code, region = classifymod.infer_country(
            det.get("institution") or r.get("institution"), det.get("regions")
        )
        flags = ",".join(classifymod.detect_flags(
            det.get("title") or r.get("title"),
            det.get("position_type") or r.get("position_type"),
            det.get("description"), eff,
        )) or None
        _persist_detail(src, r["id"], {
            **det, "country": code, "region": region, "flags": flags,
            "title": det.get("title") or r.get("title"),
        })
        done += 1
        if i < len(pending) - 1:
            time.sleep(fetchmod.DETAIL_DELAY_S)
    print(f"enriched {done} posting(s); {len(pending) - done} failed.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Emit a markdown SKELETON of valid stored postings, grouped by preference tier, with the
    mandated per-posting fields pre-filled from the DB and blank fit placeholders for the
    curator (Claude) to complete. This never invents fit judgments; see references/curation.md.
    """
    conn = dbmod.connect()
    rows = dbmod.query_jobs(conn, valid_only=True, source=args.source)
    conn.close()
    if args.preferred or args.excluded:
        pref = _split_tiers(args.preferred) or []
        excl = _split(args.excluded) or []
        kept = []
        for r in rows:
            code, region = r.get("country"), r.get("region")
            if excl and classifymod.country_matches(code, region, excl):
                continue
            r["pref_tier"] = classifymod.preference_tier(code, region, pref)
            kept.append(r)
        rows = kept
    else:
        for r in rows:
            r.setdefault("pref_tier", classifymod.preference_tier(r.get("country"), r.get("region"), []))

    md = _render_report_skeleton(rows)
    if args.out:
        from pathlib import Path
        Path(args.out).expanduser().write_text(md)
        print(f"wrote skeleton for {len(rows)} posting(s) -> {args.out}")
    else:
        print(md)
    return 0


def _render_report_skeleton(rows: list[dict]) -> str:
    from collections import defaultdict
    by_tier: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_tier[r.get("pref_tier", 99)].append(r)
    out = ["# Academic Jobs — curation skeleton",
           "",
           "> Auto-generated field skeleton. Deep-read each posting and fill the **fit 근거/등급**",
           "> and verify eligibility flags. See references/curation.md for the required schema.",
           ""]
    for tier in sorted(by_tier):
        label = f"Tier {tier + 1}" if tier < 90 else "기타 지역"
        out.append(f"## {label}")
        out.append("")
        for r in sorted(by_tier[tier], key=lambda j: (j["deadline_dt"] is None, j["deadline_dt"] or "")):
            cc = r.get("country") or "?"
            out.append(f"### {r.get('title') or r.get('code')}  ({cc})")
            out.append(f"- **기관/지역**: {r.get('institution') or '-'} · {cc}/{r.get('region') or '-'}")
            out.append(f"- **직급/유형**: {r.get('position_type') or '-'}")
            out.append(f"- **마감**: {r.get('deadline_raw') or 'rolling'}")
            out.append(f"- **분야**: {r.get('subject_areas') or '-'}")
            out.append(f"- **연락처**: {r.get('contact') or '-'}")
            out.append(f"- **링크**: {r.get('url') or '-'}")
            flags = r.get("flags")
            if flags:
                out.append(f"- ⚠️ **플래그**: {flags}")
            out.append("- **연구주제·PI**: _<상세 정독해서 채우기>_")
            out.append("- **자격·eligibility**: _<학위 시점/국적/군문제 등 확인>_")
            out.append("- **기간·급여·시작일**: _<상세에서 추출>_")
            out.append("- **지원 서류**: _<상세에서 추출>_")
            out.append("- **fit 근거**: _<OSPREY/SMEFTML/LowRank/ExMeV 중 어디에 왜>_")
            out.append("- **fit 등급**: _<상/중/하>_")
            desc = (r.get("description") or "").strip()
            if desc:
                out.append(f"- **본문(발췌)**: {desc[:600]}{'…' if len(desc) > 600 else ''}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def cmd_mark_seen(args: argparse.Namespace) -> int:
    conn = dbmod.connect()
    ids = args.ids if args.ids else None
    if args.all:
        ids = None
    elif not args.ids:
        _eprint("provide ids or --all")
        conn.close()
        return 2
    if ids is not None and not args.source:
        _eprint("with explicit ids, pass --source ajo|inspire (ids are not unique across sources)")
        conn.close()
        return 2
    n = dbmod.mark_seen(conn, ids, source=args.source)
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
    c.add_argument("--countries", help="comma-separated hard include filter (institution substring)")
    c.add_argument("--preferred", metavar="TIERS",
                   help="tiered preferred countries; ';' separates tiers, ',' entries "
                        "(e.g. 'KR,DE; JP,HK,GB,US'). ISO2 / name / region alias.")
    c.add_argument("--excluded", help="comma-separated countries to hard-drop (ISO2/name/region)")
    c.add_argument("--sources", help="comma-separated job boards: ajo, inspire")
    c.add_argument("--make-default", action="store_true", help="set this preset as default")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_config)

    f = sub.add_parser("fetch", help="search AJO and store valid postings")
    g = f.add_mutually_exclusive_group()
    g.add_argument("--preset", help="preset name (default: config default)")
    g.add_argument("--keyword", help="single ad-hoc keyword instead of a preset")
    f.add_argument("--limit", type=int, default=fetchmod.DEFAULT_LIMIT, help="page size")
    f.add_argument("--source", choices=["ajo", "inspire", "both"],
                   help="override preset sources: just one board, or both")
    f.add_argument("--include-rolling", action="store_true",
                   help="include postings with no deadline at all (truly open-ended)")
    f.add_argument("--fast", action="store_true",
                   help="AJO only: list-only pass, skip detail pages (deadlines approximate)")
    f.add_argument("--types", help="override preset position_types filter")
    f.add_argument("--countries", help="override preset countries (hard include) filter")
    f.add_argument("--preferred", metavar="TIERS",
                   help="override preset preferred tiers (';' tiers, ',' entries)")
    f.add_argument("--excluded", help="override preset excluded countries (hard drop)")
    f.add_argument("--detail-cap", type=int, default=fetchmod.DETAIL_FETCH_CAP,
                   help=f"max AJO detail pages this run (default {fetchmod.DETAIL_FETCH_CAP})")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_fetch)

    ls = sub.add_parser("list", help="query stored postings")
    ls.add_argument("--valid", action="store_true", help="only postings still open now")
    ls.add_argument("--new", action="store_true", help="only postings flagged new")
    ls.add_argument("--keyword-like", help="substring filter on title/institution/subject")
    ls.add_argument("--source", choices=["ajo", "inspire"], help="filter to one board")
    ls.add_argument("--json", action="store_true")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="show one posting (stored detail first, network if needed)")
    sh.add_argument("id", type=int)
    sh.add_argument("--source", choices=["ajo", "inspire"], default="ajo",
                    help="which board the id belongs to (default ajo)")
    sh.add_argument("--refresh", action="store_true",
                    help="force a fresh network fetch even if the body is already stored")
    sh.add_argument("--json", action="store_true")
    sh.set_defaults(func=cmd_show)

    en = sub.add_parser("enrich", help="fetch detail bodies for stored postings missing them")
    en.add_argument("--source", choices=["ajo", "inspire"], help="limit to one board")
    en.add_argument("--detail-cap", type=int, default=fetchmod.DETAIL_FETCH_CAP,
                    help=f"max detail fetches this pass (default {fetchmod.DETAIL_FETCH_CAP})")
    en.add_argument("--include-expired", action="store_true",
                    help="also enrich postings whose deadline has passed")
    en.set_defaults(func=cmd_enrich)

    rp = sub.add_parser("report", help="emit a markdown curation skeleton of valid postings")
    rp.add_argument("--source", choices=["ajo", "inspire"], help="limit to one board")
    rp.add_argument("--preferred", metavar="TIERS", help="group by these preferred tiers")
    rp.add_argument("--excluded", help="drop these countries from the skeleton")
    rp.add_argument("--out", help="write to this path instead of stdout")
    rp.set_defaults(func=cmd_report)

    ms = sub.add_parser("mark-seen", help="clear the new flag")
    ms.add_argument("ids", nargs="*", type=int)
    ms.add_argument("--source", choices=["ajo", "inspire"],
                    help="scope to one board (required when passing explicit ids)")
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
