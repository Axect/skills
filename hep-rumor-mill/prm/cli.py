"""`prm` command-line interface for the HEP-theory postdoc rumor mill.

Commands:
  fetch      pull a year's rumor-mill sheet, tag country, store entries
  enrich     resolve each offer-holder's InspireHEP / OpenAlex / Semantic Scholar record
  profile    show one person's metrics and paper list
  institute  cohort distribution of people who got offers at an institution
  analyze    place your own profile on the accepted cohort, per institute
  report     emit a Korean markdown report skeleton (data filled, judgment blanks)

Every command accepts --json for machine-readable output (consumed by the skill). The data is
self-reported and incomplete; commands surface N and unresolved counts rather than hiding them.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import db as dbmod
from . import sheet as sheetmod
from . import inspire as inspiremod
from . import openalex as oamod
from . import orcid_api as orcidmod
from . import semantic_scholar as ssmod
from . import metrics as metricsmod
from . import classify as classifymod

CAVEAT = (
    "주의: rumor mill 데이터는 자기보고이고 불완전하다. 기관당 표본이 작으면 통계가 아니라 "
    "정성 시그널로만 읽어야 하며, 보고되지 않은 오퍼는 누락되어 있다."
)


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _split(arg: str | None) -> list[str]:
    if not arg:
        return []
    return [x.strip() for x in arg.split(",") if x.strip()]


def _now_year() -> int:
    # The single place datetime.now is allowed; metrics takes current_year as a parameter.
    return datetime.now().year


# --------------------------------------------------------------------------- #
# shared enrichment
# --------------------------------------------------------------------------- #
def _enrich_one(conn, session, recid: int, *, cross_disc: bool, current_year: int) -> dict:
    """Resolve one person across sources and compute metrics. One failing source does not
    abort the person; failures are collected into the returned note list."""
    errors: list[str] = []
    openalex_id = None
    ss_id = None

    a = inspiremod.fetch_author(session, recid)
    dbmod.upsert_author(conn, {**a, "enriched": 0})

    if a.get("bai"):
        try:
            ps = inspiremod.fetch_papers(session, a["bai"], recid=recid)
            for p in ps:
                p["source"] = "inspire"
            dbmod.replace_papers(conn, recid, "inspire", ps)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"inspire papers: {exc}")
    else:
        errors.append("no BAI (no InspireHEP publication record)")

    if cross_disc:
        if a.get("orcid"):
            try:
                ws = oamod.fetch_works_by_orcid(a["orcid"])
                # Guard against OpenAlex author-conflation: a shared-name ORCID cluster can pull
                # in unrelated disciplines (crystallography, neuroscience, ...). Drop distant-
                # field works. If contamination is heavy (>= 25% or >= 10 distant works), the
                # whole cluster is unreliable (its CS/ML works are likely a different person too),
                # so discard the entire OpenAlex augmentation rather than inject phantom papers.
                kept, dropped = metricsmod.split_conflation(ws)
                heavy = ws and (len(dropped) >= 10 or len(dropped) / len(ws) >= 0.25)
                if heavy:
                    # OpenAlex clustered this ORCID with other same-named people. Discard the
                    # whole cluster and rescue the real list from the ORCID-claimed works
                    # (author-curated, no conflation); backfill citations per DOI.
                    dbmod.replace_papers(conn, recid, "openalex", [])
                    claimed = orcidmod.fetch_claimed_works(a["orcid"])
                    for w in claimed:
                        if w.get("doi"):
                            hit = oamod.fetch_work_by_doi(w["doi"])
                            if hit:
                                w["citations"] = hit.get("citations")
                                w["field"] = hit.get("field")
                                w["n_authors"] = hit.get("n_authors")
                                if hit.get("venue"):
                                    w["venue"] = hit["venue"]
                        else:
                            # No DOI (arXiv-only): backfill citations via Semantic Scholar
                            # title-match so ML preprints are not stuck at 0.
                            sm = ssmod.match_paper(w.get("title") or "")
                            if sm:
                                if sm.get("citations") is not None:
                                    w["citations"] = sm["citations"]
                                if sm.get("field") and not w.get("field"):
                                    w["field"] = sm["field"]
                        w["source"] = "orcid"
                        w.setdefault("citations", None)
                        w.setdefault("author_pos", None)
                    dbmod.replace_papers(conn, recid, "orcid", claimed)
                    errors.append(
                        f"openalex: discarded {len(ws)} clustered works "
                        f"({len(dropped)} distant-field; conflation), rescued "
                        f"{len(claimed)} ORCID-claimed works instead"
                    )
                else:
                    for p in kept:
                        p["source"] = "openalex"
                    dbmod.replace_papers(conn, recid, "openalex", kept)
                    if dropped:
                        errors.append(
                            f"openalex: dropped {len(dropped)}/{len(ws)} distant-field works"
                        )
                summ = oamod.fetch_author_summary_by_orcid(a["orcid"])
                if summ:
                    openalex_id = summ.get("openalex_id")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"openalex: {exc}")
        else:
            try:
                cand = ssmod.find_author(
                    a.get("display_name") or "", affiliation_hint=a.get("current_inst")
                )
                if cand:
                    ss_id = cand.get("ss_id")
                    sp = ssmod.fetch_papers(cand["ss_id"])
                    kept, dropped = metricsmod.split_conflation(sp)
                    for p in kept:
                        p["source"] = "ss"
                    dbmod.replace_papers(conn, recid, "ss", kept)
                    if cand.get("match_confidence") == "low":
                        errors.append("semantic scholar: low-confidence name match (no ORCID)")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"semantic scholar: {exc}")

    m = metricsmod.compute_metrics(conn, recid, current_year=current_year)
    dbmod.upsert_author(
        conn,
        {"recid": recid, "openalex_id": openalex_id, "ss_id": ss_id, "enriched": 1},
    )
    return {
        "recid": recid,
        "metrics": m,
        "author": dbmod.get_author(conn, recid),
        "errors": errors,
    }


# --------------------------------------------------------------------------- #
# fetch
# --------------------------------------------------------------------------- #
def cmd_fetch(args) -> int:
    conn = dbmod.connect()
    try:
        rows = sheetmod.fetch_rows(args.year, sheet_id=args.sheet_id)
    except ValueError as exc:
        _eprint(str(exc))
        return 2

    status_counts: Counter = Counter()
    people: set = set()
    institutions: set = set()
    with_recid = 0
    for r in rows:
        cc, region = classifymod.infer_country(r.get("institution"))
        r["country"] = cc
        r["region"] = region
        dbmod.upsert_rumor(conn, r)
        status_counts[r["status"]] += 1
        people.add(r.get("recid") or r["name"])
        institutions.add(r["institution"])
        if r.get("recid"):
            with_recid += 1

    summary = {
        "year": args.year,
        "total": len(rows),
        "unique_people": len(people),
        "institutions": len(institutions),
        "status_counts": dict(status_counts),
        "with_recid": with_recid,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"Fetched {len(rows)} rumor-mill entries for {args.year}.")
        print(f"  unique people:  {len(people)}")
        print(f"  institutions:   {len(institutions)}")
        print(f"  with InspireHEP recid: {with_recid}/{len(rows)}")
        print("  status:")
        for st, n in status_counts.most_common():
            print(f"    {st:10} {n}")
        print(f"\nNext: prm enrich --year {args.year} --status Accepted")
    return 0


# --------------------------------------------------------------------------- #
# enrich
# --------------------------------------------------------------------------- #
def cmd_enrich(args) -> int:
    conn = dbmod.connect()
    recids = dbmod.distinct_recids(conn, year=args.year, status=args.status)
    todo = dbmod.unenriched_recids(conn, recids)
    requested = len(todo)
    if args.limit is not None:
        todo = todo[: max(0, args.limit)]

    session = inspiremod.make_session()
    current_year = _now_year()
    enriched, failed = [], []
    for i, recid in enumerate(todo, 1):
        _eprint(f"[{i}/{len(todo)}] enriching {recid} ...")
        try:
            res = _enrich_one(
                conn, session, recid,
                cross_disc=not args.no_cross_disc, current_year=current_year,
            )
            enriched.append(recid)
            if res["errors"]:
                _eprint(f"    notes: {'; '.join(res['errors'])}")
        except Exception as exc:  # noqa: BLE001
            failed.append({"recid": recid, "error": str(exc)})
            _eprint(f"    FAILED: {exc}")
        time.sleep(inspiremod.REQUEST_DELAY_S)

    remaining = len(dbmod.unenriched_recids(conn, recids))
    summary = {
        "requested_unenriched": requested,
        "enriched": len(enriched),
        "failed": failed,
        "remaining_unenriched": remaining,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"\nEnriched {len(enriched)} people; {len(failed)} failed; "
              f"{remaining} still unenriched.")
        if failed:
            print("  failed recids: " + ", ".join(str(f['recid']) for f in failed))
        if remaining:
            print(f"  re-run to continue: prm enrich --year {args.year or ''} "
                  f"--status {args.status or ''}".rstrip())
    return 0


# --------------------------------------------------------------------------- #
# profile
# --------------------------------------------------------------------------- #
def _resolve_recid(conn, args) -> int | None:
    if args.recid is not None:
        return args.recid
    if args.name:
        rs = dbmod.query_rumors(conn)
        for r in rs:
            if args.name.lower() in (r["name"] or "").lower() and r.get("recid"):
                return r["recid"]
    return None


def cmd_profile(args) -> int:
    conn = dbmod.connect()
    recid = _resolve_recid(conn, args)
    if recid is None:
        _eprint("could not resolve a recid (pass an integer or --name matching a stored rumor)")
        return 2
    author = dbmod.get_author(conn, recid)
    metrics = dbmod.get_metrics(conn, recid)
    papers = dbmod.get_papers(conn, recid)
    if author is None or metrics is None:
        _eprint(f"recid {recid} is not enriched yet. Run: prm enrich")
        if not args.json:
            return 1

    if args.json:
        print(json.dumps(
            {"author": author, "metrics": metrics, "papers": papers}, ensure_ascii=False))
        return 0

    print(f"== {author.get('display_name') if author else recid} (recid {recid}) ==")
    if author:
        print(f"  PhD year:    {author.get('phd_year')}")
        print(f"  current:     {author.get('current_rank')} @ {author.get('current_inst')}")
        print(f"  arxiv cats:  {author.get('arxiv_cats')}")
        adv = author.get("advisors")
        if adv:
            try:
                adv = json.loads(adv) if isinstance(adv, str) else adv
                print("  advisors:    " + ", ".join(x.get("name", "") for x in adv))
            except (json.JSONDecodeError, TypeError):
                pass
    if metrics:
        lc = metrics.get("n_large_collab") or 0
        lc_note = f", {lc} large-collab (>50 authors)" if lc else ""
        print(f"  papers:      {metrics.get('n_papers')} "
              f"(first-author {metrics.get('n_first_author')}{lc_note})")
        print(f"  citations:   {metrics.get('total_citations')}  h-index {metrics.get('h_index')}")
        print(f"  years since PhD: {metrics.get('years_since_phd')}")
        print(f"  interdisciplinary: {'yes' if metrics.get('interdisciplinary') else 'no'}")
        tv = metrics.get("top_venues") or []
        if tv:
            print("  top venues:  " + ", ".join(f"{v}({n})" for v, n in tv))
        cd = metrics.get("cross_disc") or {}
        for src, s in cd.items():
            print(f"  [{src}] papers={s.get('n_papers')} cit={s.get('total_citations')} "
                  f"h={s.get('h_index')}")
    print("\n  papers (year | tier | cit | venue | title):")
    for p in sorted(papers, key=lambda x: (x.get("year") or 0), reverse=True):
        print(f"    {p.get('year') or '????'} {p.get('venue_tier') or '-':9} "
              f"{str(p.get('citations') or 0):>4}  {(p.get('venue') or '-')[:22]:22} "
              f"{(p.get('title') or '')[:50]}")
    return 0


# --------------------------------------------------------------------------- #
# institute
# --------------------------------------------------------------------------- #
def _cohort_for(conn, *, institution_like=None, status=None, year=None):
    """Return (metrics_list, people_rows, unenriched_count) for matching rumors."""
    rs = dbmod.query_rumors(
        conn, year=year, status=status, institution_like=institution_like)
    seen: dict[int, dict] = {}
    for r in rs:
        rid = r.get("recid")
        if rid and rid not in seen:
            seen[rid] = r
    mlist, unenriched = [], 0
    for rid, r in seen.items():
        m = dbmod.get_metrics(conn, rid)
        if m:
            mlist.append(m)
        else:
            unenriched += 1
    return mlist, list(seen.values()), unenriched


def cmd_institute(args) -> int:
    conn = dbmod.connect()
    mlist, people, unenriched = _cohort_for(
        conn, institution_like=args.name, status=args.status, year=args.year)
    cohort = metricsmod.cohort_stats(mlist)

    if args.json:
        print(json.dumps({
            "institution": args.name, "status": args.status, "year": args.year,
            "n_resolved": len(mlist), "n_unenriched": unenriched,
            "cohort": cohort,
            "people": [{"recid": p.get("recid"), "name": p.get("name"),
                        "remarks": p.get("remarks")} for p in people],
        }, ensure_ascii=False))
        return 0

    print(f"== {args.name} :: offers ({args.status or 'any status'}) ==")
    print(f"  people: {len(people)}  (enriched {len(mlist)}, unenriched {unenriched})")
    print(f"  {CAVEAT}")
    if mlist:
        c = cohort
        def fmt(d):
            return (f"median {d.get('median')} (q1 {d.get('q1')}, q3 {d.get('q3')}, "
                    f"min {d.get('min')}, max {d.get('max')})")
        print(f"  citations:       {fmt(c['citations'])}")
        print(f"  papers:          {fmt(c['papers'])}")
        print(f"  h-index:         {fmt(c['h_index'])}")
        print(f"  years since PhD: {fmt(c['years_since_phd'])}")
        print(f"  interdisciplinary fraction: {c.get('interdisciplinary_frac')}")
        fm = c.get("field_mix") or {}
        if fm:
            top = sorted(fm.items(), key=lambda kv: kv[1], reverse=True)[:6]
            print("  field mix: " + ", ".join(f"{k}({v})" for k, v in top))
    print("\n  people:")
    for p in people:
        m = dbmod.get_metrics(conn, p.get("recid")) if p.get("recid") else None
        cit = m.get("total_citations") if m else "?"
        npp = m.get("n_papers") if m else "?"
        fel = f"  [{p.get('remarks')}]" if p.get("remarks") else ""
        print(f"    {p.get('name'):28} cit={cit} papers={npp}{fel}")
    return 0


# --------------------------------------------------------------------------- #
# analyze
# --------------------------------------------------------------------------- #
def _place(me: dict, cohort_metrics: list[dict]) -> dict:
    def pop(key):
        return [m.get(key) for m in cohort_metrics if m.get(key) is not None]
    axes = {}
    for key in ("total_citations", "n_papers", "h_index"):
        axes[key] = {
            "me": me.get(key),
            "percentile": metricsmod.percentile_of(me.get(key), pop(key)),
            "cohort_median": metricsmod.cohort_stats(cohort_metrics).get(
                {"total_citations": "citations", "n_papers": "papers",
                 "h_index": "h_index"}[key], {}).get("median"),
        }
    return axes


def cmd_analyze(args) -> int:
    conn = dbmod.connect()
    current_year = _now_year()
    # Use the cached enriched record if present; re-enrich only when missing or --refresh.
    # This avoids clobbering a good record (e.g. a manual citation correction) on every run,
    # and keeps the flaky Semantic Scholar backfill from being re-rolled each time.
    cached = dbmod.get_metrics(conn, args.me)
    if cached is not None and not args.refresh:
        me = cached
    else:
        session = inspiremod.make_session()
        res = _enrich_one(
            conn, session, args.me, cross_disc=not args.no_cross_disc,
            current_year=current_year)
        me = res["metrics"]

    cohorts = []
    institutes = _split(args.institutes)

    def _without_me(mlist):
        # Never benchmark the user against a cohort that contains themselves.
        return [m for m in mlist if m.get("recid") != args.me]

    if institutes:
        for inst in institutes:
            mlist, _people, unenriched = _cohort_for(
                conn, institution_like=inst, status="Accepted", year=args.year)
            mlist = _without_me(mlist)
            cohorts.append({
                "label": inst, "n": len(mlist), "n_unenriched": unenriched,
                "axes": _place(me, mlist) if mlist else None,
            })
    else:
        mlist, _people, unenriched = _cohort_for(
            conn, status="Accepted", year=args.year)
        mlist = _without_me(mlist)
        cohorts.append({
            "label": f"all Accepted{f' {args.year}' if args.year else ''}",
            "n": len(mlist), "n_unenriched": unenriched,
            "axes": _place(me, mlist) if mlist else None,
        })

    if args.json:
        print(json.dumps({"me": me, "cohorts": cohorts}, ensure_ascii=False))
        return 0

    print(f"== analyze recid {args.me} ==")
    print(f"  me: papers={me.get('n_papers')} citations={me.get('total_citations')} "
          f"h-index={me.get('h_index')} interdisc={'yes' if me.get('interdisciplinary') else 'no'}")
    print(f"  {CAVEAT}\n")
    for c in cohorts:
        print(f"  vs [{c['label']}]  N={c['n']} (unenriched {c['n_unenriched']})")
        if not c["axes"]:
            print("    cohort not enriched yet; run prm enrich first.")
            continue
        for key, ax in c["axes"].items():
            pct = ax["percentile"]
            pct_s = f"{pct:.0f}th pct" if pct is not None else "n/a"
            print(f"    {key:16} me={ax['me']}  cohort median={ax['cohort_median']}  ({pct_s})")
    return 0


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def cmd_report(args) -> int:
    conn = dbmod.connect()
    year = args.year
    rs = dbmod.query_rumors(conn, year=year)
    status_counts: Counter = Counter(r["status"] for r in rs)
    inst_offers = Counter(r["institution"] for r in rs if r["status"] in ("Offered", "Accepted"))

    mlist, _people, unenriched = _cohort_for(conn, status="Accepted", year=year)
    cohort = metricsmod.cohort_stats(mlist)

    lines: list[str] = []
    lines.append(f"# HEP-theory 포스닥 rumor mill 분석 {year}\n")
    lines.append(f"> {CAVEAT}\n")
    lines.append("## 개요\n")
    lines.append(f"- 전체 항목: {len(rs)}")
    lines.append(f"- 상태 분포: " + ", ".join(f"{k} {v}" for k, v in status_counts.most_common()))
    lines.append(f"- enrich된 Accepted 코호트: {len(mlist)}명 (미enrich {unenriched}명)\n")

    lines.append("## 오퍼가 많은 기관 (Offered+Accepted)\n")
    lines.append("| 기관 | 건수 |")
    lines.append("| --- | --- |")
    for inst, n in inst_offers.most_common(20):
        lines.append(f"| {inst} | {n} |")
    lines.append("")

    if mlist:
        c = cohort
        lines.append("## Accepted 코호트 실적 분포\n")
        lines.append("| 지표 | 중앙값 | Q1 | Q3 | 최소 | 최대 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for label, key in (("총 인용", "citations"), ("논문 수", "papers"),
                           ("h-index", "h_index"), ("PhD 후 연수", "years_since_phd")):
            d = c[key]
            lines.append(f"| {label} | {d.get('median')} | {d.get('q1')} | {d.get('q3')} | "
                         f"{d.get('min')} | {d.get('max')} |")
        lines.append(f"\n- interdisciplinary 비율: {c.get('interdisciplinary_frac')}")
        fm = c.get("field_mix") or {}
        if fm:
            top = sorted(fm.items(), key=lambda kv: kv[1], reverse=True)[:8]
            lines.append("- 분야 믹스: " + ", ".join(f"{k}({v})" for k, v in top))
        lines.append("")

    if args.me is not None:
        # Use the cached enriched record if present (do not clobber a manual correction);
        # enrich only when missing.
        me = dbmod.get_metrics(conn, args.me)
        if me is None:
            session = inspiremod.make_session()
            res = _enrich_one(conn, session, args.me, cross_disc=True, current_year=_now_year())
            me = res["metrics"]
        cohort_excl_me = [m for m in mlist if m.get("recid") != args.me]
        axes = _place(me, cohort_excl_me) if cohort_excl_me else {}
        lines.append("## 내 프로필 위치 (Accepted 코호트 대비)\n")
        lines.append("| 지표 | 나 | 코호트 중앙값 | 백분위 |")
        lines.append("| --- | --- | --- | --- |")
        for key, label in (("total_citations", "총 인용"), ("n_papers", "논문 수"),
                           ("h_index", "h-index")):
            ax = axes.get(key, {})
            pct = ax.get("percentile")
            lines.append(f"| {label} | {ax.get('me')} | {ax.get('cohort_median')} | "
                         f"{f'{pct:.0f}' if pct is not None else '-'} |")
        lines.append("")

    lines.append("## 정성 분석 (Claude가 채울 부분)\n")
    lines.append("아래 항목은 데이터만으로 채우지 말고, 각 인물/코호트의 대표 논문을 읽고 작성한다 "
                 "(references/analysis.md 절차 준수).\n")
    lines.append("- [ ] 기관별로 오퍼를 받은 사람들의 **실제 연구 주제**와 공통 패턴")
    lines.append("- [ ] named fellowship(Humboldt, Leinweber 등)이 어떤 프로필에 갔는지")
    lines.append("- [ ] 내 프로필과의 **격차**와 구체적 보완 전략 (벤치마크 근거 포함)")
    lines.append("- [ ] interdisciplinary 인물의 cross-disciplinary 실적 해석 (OpenAlex 보강분)")
    lines.append("")

    out = Path(args.out).expanduser() if args.out else (
        Path.home() / "Dropbox" / "RumorMill" / f"RumorMill_{year}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote skeleton: {out}")
    return 0


# --------------------------------------------------------------------------- #
# argument parsing
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prm", description="HEP-theory postdoc rumor mill analysis")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="pull a year's rumor-mill sheet and store entries")
    f.add_argument("--year", type=int, required=True)
    f.add_argument("--sheet-id", default=None, help="override the sheet id for this year")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_fetch)

    e = sub.add_parser("enrich", help="resolve offer-holders' publication records")
    e.add_argument("--year", type=int, default=None)
    e.add_argument("--status", default=None, help="e.g. Accepted / Offered / Declined")
    e.add_argument("--limit", type=int, default=None, help="cap people processed this run")
    e.add_argument("--no-cross-disc", action="store_true",
                   help="skip OpenAlex/Semantic Scholar augmentation")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=cmd_enrich)

    pr = sub.add_parser("profile", help="show one person's metrics and papers")
    pr.add_argument("recid", type=int, nargs="?", default=None)
    pr.add_argument("--name", default=None, help="resolve recid by name from stored rumors")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_profile)

    it = sub.add_parser("institute", help="cohort distribution for an institution's offers")
    it.add_argument("name")
    it.add_argument("--status", default=None)
    it.add_argument("--year", type=int, default=None)
    it.add_argument("--json", action="store_true")
    it.set_defaults(func=cmd_institute)

    an = sub.add_parser("analyze", help="place your own profile on the accepted cohort")
    an.add_argument("--me", type=int, required=True, help="your InspireHEP recid")
    an.add_argument("--institutes", default=None, help="comma-separated institution filters")
    an.add_argument("--year", type=int, default=None)
    an.add_argument("--no-cross-disc", action="store_true")
    an.add_argument("--refresh", action="store_true",
                    help="force re-enrich of --me instead of using the cached record")
    an.add_argument("--json", action="store_true")
    an.set_defaults(func=cmd_analyze)

    rp = sub.add_parser("report", help="emit a Korean markdown report skeleton")
    rp.add_argument("--year", type=int, required=True)
    rp.add_argument("--me", type=int, default=None, help="include your percentile table")
    rp.add_argument("--institutes", default=None)
    rp.add_argument("--out", default=None)
    rp.set_defaults(func=cmd_report)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
