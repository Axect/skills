#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""rboard: hypothesis/experiment board over ~/.research/projects/*/cards/*.md.

Reads cards (YAML frontmatter + prose). Writes only with `refresh --accept` (recomputed metric
values and source hashes, under the per-project flock). See references/schema.md.
"""
from __future__ import annotations

import argparse
import base64
import csv
import fcntl
import hashlib
import html
import json
import math
from decimal import Decimal
import os
import re
import statistics
import subprocess
import signal
import sys
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
import glob
import shlex
import time
from shutil import which

import yaml

WORK = ['active', 'waiting', 'candidate', 'parked', 'closed']
VERDICT = {'unassessed', 'supported', 'refuted', 'inconclusive', 'conflicting'}
KIND = {'hypothesis', 'exploration', 'engineering'}
EXP_STATUS = {'planned', 'running', 'analyzing', 'done', 'failed', 'invalid'}
EFFECT = {'supports', 'refutes', 'inconclusive', 'none'}
RUN_STATE = {'queued', 'running', 'finished', 'failed', 'unknown'}
PROV = {'prospective', 'retrospective', 'unknown'}
CLOSURE = {'resolved', 'superseded', 'deferred', 'unknown'}
DIRS = {'lower', 'higher'}
AGG = {'median', 'mean', 'min', 'max', 'sum', 'count', 'first'}
STYLE = {'scienceplot', 'legacy'}
ROLE = {'key', 'supporting'}
ACTIVE_STALE_DAYS = 14
RUN_STALE_DAYS = 3
MAX_EMBED_BYTES = 700_000
BADGE = {'unassessed': '---', 'supported': 'SUP', 'refuted': 'REF',
         'inconclusive': 'INC', 'conflicting': 'CFL'}


def today() -> date:
    v = os.environ.get('RBOARD_TODAY')
    return date.fromisoformat(v) if v else date.today()


def dparse(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    if isinstance(x, str) and re.match(r'\d{4}-\d{2}-\d{2}', x):
        return date.fromisoformat(x[:10])
    return None


def dstr(x) -> str:
    d = dparse(x)
    return d.isoformat() if d else (str(x) if x not in (None, '') else '')


def age_days(x):
    d = dparse(x)
    return (today() - d).days if d else None


def xp(p) -> Path:
    return Path(os.path.expanduser(str(p)))


def sha12(path) -> str:
    return hashlib.sha256(xp(path).read_bytes()).hexdigest()[:12]


# ------------------------------------------------------------------ store

def store_root(args) -> Path:
    return xp(args.root or os.environ.get('RBOARD_ROOT') or '~/.research')


def parse_card(path: Path, slug: str) -> dict:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError('missing frontmatter')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise ValueError('unterminated frontmatter')
    fm = yaml.safe_load(text[4:end]) or {}
    if not isinstance(fm, dict):
        raise ValueError('frontmatter is not a mapping')
    return {'fm': fm, 'body': text[end + 5:], 'path': path, 'slug': slug}


def load_all(root: Path, project: str | None = None):
    cards, issues = [], []
    base = root / 'projects'
    if not base.is_dir():
        return cards, [('error', str(base), 'no projects directory')]
    for pdir in sorted(base.iterdir()):
        if not pdir.is_dir() or (project and pdir.name != project):
            continue
        for f in sorted((pdir / 'cards').glob('Q*.md')):
            try:
                cards.append(parse_card(f, pdir.name))
            except Exception as e:  # report and continue: one bad card must not hide the rest
                issues.append(('error', f'{pdir.name}/{f.name}', f'parse: {e}'))
    return cards, issues


def cid(c) -> str:
    return str(c['fm'].get('id', ''))


def exps(c):
    return c['fm'].get('experiments') or []


def find_card(cards, token: str, project: str | None):
    hits = [c for c in cards if cid(c) == token]
    if not hits and ':' not in token:
        hits = [c for c in cards if cid(c).endswith(':' + token) and (not project or c['slug'] == project)]
    if len(hits) != 1:
        raise SystemExit(f'card {token!r}: {len(hits)} matches' + (' (use slug:Qn)' if hits else ''))
    return hits[0]


def parse_ref(cards, token: str, project: str | None):
    parts = token.split('/')
    card = find_card(cards, parts[0], project)
    exp = None
    if len(parts) > 1 and parts[1]:
        exp = next((e for e in exps(card) if str(e.get('id')) == parts[1]), None)
        if exp is None:
            raise SystemExit(f'{token}: no experiment {parts[1]} in {cid(card)}')
    plot = None
    if len(parts) > 2 and exp is not None:
        plot = next((p for p in (exp.get('results') or {}).get('plots') or [] if str(p.get('id')) == parts[2]), None)
        if plot is None:
            raise SystemExit(f'{token}: no plot {parts[2]}')
    return card, exp, plot


@contextmanager
def lock(root: Path, slug: str):
    d = root / '.locks'
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f'{slug}.lock', 'a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def write_card(c):
    fm = yaml.safe_dump(c['fm'], sort_keys=False, allow_unicode=True, width=100)
    c['path'].write_text(f'---\n{fm}---\n{c["body"]}', encoding='utf-8')


# ------------------------------------------------------------------ judgement

def exp_valid(e) -> bool:
    if e.get('status') != 'done':
        return False
    ev = e.get('evaluation') or {}
    return ev.get('valid') is not False


def collect_assessments(cards):
    out = defaultdict(list)
    for c in cards:
        owner = cid(c)
        for e in exps(c):
            for target, a in (e.get('assess') or {}).items():
                a = a or {}
                out[str(target)].append(dict(
                    ref=f'{owner}/{e.get("id")}', exp=e, owner=owner, effect=a.get('effect'),
                    scope=a.get('scope', ''), note=a.get('note', ''), date=dparse(e.get('date')),
                    valid=exp_valid(e)))
    return out


def verdict_hint(assessments) -> str:
    eff = {a['effect'] for a in assessments if a['valid'] and a['effect'] and a['effect'] != 'none'}
    if {'supports', 'refutes'} <= eff:
        return 'conflicting'
    if 'refutes' in eff:
        return 'refuted'
    if 'supports' in eff:
        return 'supported'
    if 'inconclusive' in eff:
        return 'inconclusive'
    return 'unassessed'


# ------------------------------------------------------------------ metrics

def _nums(vals):
    out = []
    for v in vals:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if not math.isnan(f):
            out.append(f)
    return out


def _agg(vals, how):
    if not vals:
        raise ValueError('no numeric values selected')
    if how == 'median':
        return statistics.median(vals)
    if how == 'mean':
        return statistics.fmean(vals)
    if how == 'min':
        return min(vals)
    if how == 'max':
        return max(vals)
    if how == 'sum':
        return sum(vals)
    if how == 'count':
        return float(len(vals))
    if how == 'first':
        return vals[0]
    raise ValueError(f'unknown agg {how}')


def extract_value(metric: dict):
    """Recompute (value, n, lo, hi) from metric['extract']."""
    ex = metric.get('extract')
    if not ex:
        raise ValueError('no extract spec')
    f = xp(ex['file'])
    how = ex.get('agg', 'median')
    if f.suffix.lower() == '.json':
        node = json.loads(f.read_text(encoding='utf-8'))
        for k in ex.get('path', []):
            node = node[k]
        vals = _nums(node if isinstance(node, list) else [node])
    else:
        if f.suffix.lower() == '.parquet':
            import pandas as pd  # optional dependency, only for parquet sources
            rows = pd.read_parquet(f).astype(object).to_dict('records')
            cols = set(rows[0]) if rows else set()
        else:
            with open(f, newline='', encoding='utf-8') as fh:
                rd = csv.DictReader(fh)
                cols = set(rd.fieldnames or [])
                rows = list(rd)
        where = ex.get('where')
        if where is None:
            missing = [k for k in metric.get('scope', {}) if k not in cols]
            if missing:
                raise ValueError(f'scope keys {missing} are not columns; give extract.where explicitly')
            where = metric.get('scope', {})
        bad = [k for k in where if k not in cols]
        if bad:
            raise ValueError(f'where keys {bad} are not columns of {f.name}')
        sel = [r for r in rows if all(str(r[k]) == str(v) for k, v in where.items())]
        vals = _nums(r[ex['column']] for r in sel)
    v = _agg(vals, how)
    return v, len(vals), (min(vals) if len(vals) > 1 else None), (max(vals) if len(vals) > 1 else None)


def sig6(x):
    return None if x is None else float(f'{x:.6g}')


def close(stored, new) -> bool:
    """True when `new` equals `stored` at the precision `stored` was written with (>= 2 significant digits)."""
    if stored is None or new is None:
        return stored is None and new is None
    sig = max(2, len(Decimal(repr(float(stored))).normalize().as_tuple().digits))
    return float(f'{new:.{sig}g}') == float(stored) or math.isclose(float(new), float(stored), rel_tol=1e-9)


def refresh_exp(c, e, accept: bool):
    """Return list of findings; mutate card in memory when accept is set."""
    res = e.get('results') or {}
    out = []
    for s in res.get('sources') or []:
        p = xp(s.get('path', ''))
        if not p.exists():
            out.append(('warn', f'source missing: {s.get("path")}'))
            continue
        cur = sha12(p)
        stored = str(s.get('sha256', ''))
        if not stored or not cur.startswith(stored[:12]):
            out.append(('warn', f'source changed: {p.name} stored={stored[:12] or "-"} now={cur}'))
            if accept:
                s['sha256'] = cur
        else:
            out.append(('ok', f'source unchanged: {p.name} @ {cur}'))
    for m in res.get('metrics') or []:
        label = f'{m.get("name")} {fmt_scope(m.get("scope", {}))}'
        if not m.get('extract'):
            out.append(('info', f'no extract spec (cannot refresh): {label}'))
            continue
        try:
            v, n, lo, hi = extract_value(m)
        except Exception as ex:
            out.append(('error', f'extract failed: {label}: {ex}'))
            continue
        same = (close(m.get('value'), v) and n == m.get('n')
                and close(m.get('lo'), lo) and close(m.get('hi'), hi))
        if same:
            out.append(('ok', f'metric unchanged: {label} = {v:.6g} (n={n})'))
        else:
            out.append(('warn', f'metric drift: {label}: stored {m.get("value")} (n={m.get("n")}) -> now {v:.6g} (n={n})'))
            if accept:
                m['value'], m['n'] = sig6(v), n
                m['lo'], m['hi'] = sig6(lo), sig6(hi)
                if m['lo'] is None:
                    m.pop('lo'), m.pop('hi')
    if accept and res:
        res['computed_at'] = today()
    return out


# ------------------------------------------------------------------ comparison

def fmt_scope(scope, skip=()):
    return ', '.join(f'{k}={v}' for k, v in (scope or {}).items() if k not in skip)


def key_arm(m):
    arm = m.get('arm_key')
    return (m.get('name'), str(m.get('unit', '')),
            tuple(sorted((k, str(v)) for k, v in (m.get('scope') or {}).items() if k != arm)))


def key_full(m):
    return (m.get('name'), str(m.get('unit', '')),
            tuple(sorted((k, str(v)) for k, v in (m.get('scope') or {}).items())))


def arm_of(m):
    return str((m.get('scope') or {}).get(m.get('arm_key'), ''))


def better(m, v_new, v_ref):
    if v_new == v_ref:
        return 'equal'
    lower = m.get('dir') == 'lower'
    return 'better' if ((v_new < v_ref) == lower) else 'worse'


def spread_flag(a, b):
    na, nb = a.get('n') or 0, b.get('n') or 0
    if na <= 1 or nb <= 1:
        return 'n=1: no spread'
    if a.get('lo') is None or b.get('lo') is None:
        return ''
    if a['lo'] <= b['hi'] and b['lo'] <= a['hi']:
        return 'ranges overlap'
    return ''


def arm_compare(e, ref_arm=None):
    """Arm comparisons within one experiment: same name/unit/scope except arm_key."""
    groups = defaultdict(list)
    for m in (e.get('results') or {}).get('metrics') or []:
        if m.get('arm_key') and m.get('value') is not None:
            groups[key_arm(m)].append(m)
    rows = []
    for k, ms in groups.items():
        if len(ms) < 2:
            continue
        base = [m for m in ms if m.get('baseline')]
        ref = next((m for m in ms if arm_of(m) == ref_arm), ms[0]) if ref_arm else (base[0] if base else ms[0])
        for m in ms:
            if m is ref:
                continue
            rel = (m['value'] - ref['value']) / ref['value'] if ref['value'] else None
            rows.append(dict(name=k[0], unit=k[1], scope=dict(k[2]), ref=ref, arm=m, rel=rel,
                             verdict=better(m, m['value'], ref['value']), flag=spread_flag(m, ref)))
    return rows


def explain_mismatch(ma, mb):
    sa, sb = ma.get('scope') or {}, mb.get('scope') or {}
    only_a = sorted(set(sa) - set(sb))
    only_b = sorted(set(sb) - set(sa))
    diff = sorted(k for k in set(sa) & set(sb) if str(sa[k]) != str(sb[k]))
    parts = []
    if str(ma.get('unit', '')) != str(mb.get('unit', '')):
        parts.append(f'unit {ma.get("unit")!r} vs {mb.get("unit")!r}')
    if only_a or only_b:
        parts.append(f'scope keys differ (only A: {only_a}, only B: {only_b})')
    if diff:
        parts.append('scope values differ: ' + '; '.join(f'{k}: {sa[k]} vs {sb[k]}' for k in diff))
    return ' | '.join(parts) or 'unknown'


def cross_compare(items):
    """items: list of (label, card, exp). Returns dict(rows, blocked, notes, excluded)."""
    valid, excluded = [], []
    for label, c, e in items:
        (valid if exp_valid(e) else excluded).append((label, c, e))
    idx = []
    for label, c, e in valid:
        d = {}
        for m in (e.get('results') or {}).get('metrics') or []:
            if m.get('value') is not None:
                d[key_full(m)] = m
        idx.append((label, e, d))
    keys = defaultdict(list)
    for i, (_, _, d) in enumerate(idx):
        for k in d:
            keys[k].append(i)
    rows = [dict(key=k, cells={idx[i][0]: idx[i][2][k] for i in ii})
            for k, ii in keys.items() if len(ii) >= 2]
    blocked, notes = [], []
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            la, ea, da = idx[i]
            lb, eb, db = idx[j]
            if set(da) & set(db):
                va, vb = (ea.get('evaluation') or {}).get('version'), (eb.get('evaluation') or {}).get('version')
                if va and vb and va != vb:
                    notes.append(f'{la} vs {lb}: different evaluation.version ({va} / {vb})')
                continue
            names = {k[0] for k in da} & {k[0] for k in db}
            for nm in sorted(n for n in names if n):
                ma = next(m for k, m in da.items() if k[0] == nm)
                mb = next(m for k, m in db.items() if k[0] == nm)
                blocked.append((la, lb, nm, explain_mismatch(ma, mb)))
    return dict(rows=rows, blocked=blocked, notes=notes,
                excluded=[(l, (e.get('status'), (e.get('evaluation') or {}).get('valid'))) for l, _, e in excluded])


# ------------------------------------------------------------------ lint

def lint(cards, project_filter=None):
    issues = []
    ids = defaultdict(list)
    for c in cards:
        ids[cid(c)].append(c)
    assess = collect_assessments(cards)

    def err(c, m):
        issues.append(('error', cid(c) or c['path'].name, m))

    def warn(c, m):
        issues.append(('warn', cid(c), m))

    for c in cards:
        fm = c['fm']
        i = cid(c)
        if not re.fullmatch(rf'{re.escape(c["slug"])}:Q\d+', i):
            err(c, f'id must be {c["slug"]}:Q<n>, got {i!r}')
        elif not c['path'].name.startswith(i.split(':')[1] + '-'):
            err(c, f'file name {c["path"].name} does not start with {i.split(":")[1]}-')
        if len(ids[i]) > 1:
            err(c, 'duplicate id')
        for req in ('kind', 'title', 'work', 'verdict', 'last_verified_at', 'updated'):
            if fm.get(req) in (None, ''):
                err(c, f'missing {req}')
        if fm.get('kind') and fm['kind'] not in KIND:
            err(c, f'kind {fm["kind"]!r} not in {sorted(KIND)}')
        if fm.get('work') and fm['work'] not in WORK:
            err(c, f'work {fm["work"]!r} not in {WORK}')
        if fm.get('verdict') and fm['verdict'] not in VERDICT:
            err(c, f'verdict {fm["verdict"]!r} not in {sorted(VERDICT)}')
        for dk in ('last_verified_at', 'updated'):
            if fm.get(dk) not in (None, '') and dparse(fm.get(dk)) is None:
                err(c, f'{dk} is not a date')
        if fm.get('work') in ('waiting', 'parked') and not fm.get('work_reason'):
            err(c, f'work={fm["work"]} requires work_reason')
        if fm.get('work') == 'closed' and fm.get('closure') not in CLOSURE:
            err(c, f'work=closed requires closure in {sorted(CLOSURE)}')
        fal = fm.get('falsifier')
        if fm.get('kind') == 'hypothesis':
            if not fal or not fal.get('text'):
                warn(c, 'hypothesis without falsifier')
            elif fal.get('provenance') not in PROV:
                err(c, f'falsifier.provenance must be in {sorted(PROV)}')
            elif fal['provenance'] == 'prospective' and not fal.get('ref'):
                err(c, 'prospective falsifier requires ref')
            if not fm.get('claim'):
                err(c, 'hypothesis requires claim')
        for s in fm.get('supersedes') or []:
            if s not in ids:
                err(c, f'supersedes missing card {s}')
        seen = set()
        for e in exps(c):
            eid = str(e.get('id', ''))
            if not re.fullmatch(r'E\d+', eid) or eid in seen:
                err(c, f'experiment id {eid!r} invalid or duplicate')
            seen.add(eid)
            where = f'{i}/{eid}'
            if e.get('status') not in EXP_STATUS:
                err(c, f'{where}: status {e.get("status")!r} not in {sorted(EXP_STATUS)}')
            if e.get('status') == 'done' and 'assess' not in e:
                warn(c, f'{where}: done without assess (write `assess: {{}}` for infrastructure work)')
            for tgt, a in (e.get('assess') or {}).items():
                if str(tgt) not in ids:
                    err(c, f'{where}: assess targets missing card {tgt}')
                if (a or {}).get('effect') not in EFFECT:
                    err(c, f'{where}: assess[{tgt}].effect must be in {sorted(EFFECT)}')
            for s in e.get('sessions') or []:
                if not s.get('id') or not s.get('path'):
                    err(c, f'{where}: session needs id and path')
                elif not xp(s['path']).exists():
                    warn(c, f'{where}: session file missing: {s["path"]}')
            if e.get('status') in ('running', 'analyzing') and fm.get('work') in ('active', 'waiting') \
                    and not e.get('sessions'):
                warn(c, f'{where}: {e["status"]} without a linked session (rboard link {where} --here)')
            for r in e.get('runs') or []:
                if r.get('state') not in RUN_STATE:
                    err(c, f'{where}: run state {r.get("state")!r} not in {sorted(RUN_STATE)}')
                elif r['state'] in ('running', 'queued'):
                    a = age_days(r.get('observed_at'))
                    if a is None or a > RUN_STALE_DAYS:
                        warn(c, f'{where}: last observed {r["state"]} '
                                f'({dstr(r.get("observed_at")) or "no date"}), currently unknown')
            res = e.get('results') or {}
            for m in res.get('metrics') or []:
                for req in ('name', 'scope', 'dir'):
                    if m.get(req) in (None, ''):
                        err(c, f'{where}: metric missing {req}')
                if m.get('value') is None:
                    if m.get('extract'):
                        warn(c, f'{where}: metric {m.get("name")} has no value yet (run rboard refresh --accept)')
                    else:
                        err(c, f'{where}: metric {m.get("name")} missing value (or give an extract spec)')
                if m.get('dir') and m['dir'] not in DIRS:
                    err(c, f'{where}: metric dir must be in {sorted(DIRS)}')
                if 'unit' not in m:
                    err(c, f'{where}: metric {m.get("name")} missing unit (use "" if dimensionless)')
                if m.get('arm_key') and m['arm_key'] not in (m.get('scope') or {}):
                    err(c, f'{where}: arm_key {m["arm_key"]!r} not in scope')
                if m.get('extract') and m['extract'].get('agg', 'median') not in AGG:
                    err(c, f'{where}: extract.agg must be in {sorted(AGG)}')
            for p in res.get('plots') or []:
                if p.get('style') not in STYLE:
                    err(c, f'{where}: plot {p.get("id")} style must be in {sorted(STYLE)}')
                if p.get('role') not in ROLE:
                    err(c, f'{where}: plot {p.get("id")} role must be in {sorted(ROLE)}')
                if p.get('out') and not xp(p['out']).exists():
                    warn(c, f'{where}: plot {p.get("id")} out missing on disk: {p["out"]}')
                if p.get('style') == 'scienceplot' and not p.get('recipe'):
                    warn(c, f'{where}: scienceplot plot {p.get("id")} has no recipe')
            for s in res.get('sources') or []:
                p = xp(s.get('path', ''))
                if p.exists() and s.get('sha256') and not sha12(p).startswith(str(s['sha256'])[:12]):
                    warn(c, f'{where}: source changed since stored: {p.name} (run rboard refresh)')
        if fm.get('work') == 'active':
            a = age_days(fm.get('last_verified_at'))
            if a is not None and a > ACTIVE_STALE_DAYS:
                warn(c, f'active but last verified {a} days ago')
        for s in fm.get('sessions') or []:
            if not s.get('id') or not s.get('path'):
                err(c, 'card session needs id and path')
            elif not xp(s['path']).exists():
                warn(c, f'card session file missing: {s["path"]}')
        if fm.get('needs_review'):
            warn(c, f'needs_review: {fm.get("review_note") or "(no note)"}')
        hint = verdict_hint(assess.get(i, []))
        if fm.get('verdict') in VERDICT and fm['verdict'] != hint and not fm.get('verdict_reason'):
            warn(c, f'verdict {fm["verdict"]} differs from hint {hint} and has no verdict_reason')
    return issues


# ------------------------------------------------------------------ text views

def last_exp(c):
    es = sorted(exps(c), key=lambda e: dstr(e.get('date')), reverse=True)
    return es[0] if es else None


def effect_for(c, e):
    a = (e.get('assess') or {})
    x = a.get(cid(c)) or (next(iter(a.values())) if a else {})
    return (x or {}).get('effect', 'none')


def cmd_board(args, cards):
    by = defaultdict(list)
    for c in cards:
        by[c['slug']].append(c)
    if not by:
        print('no cards')
        return
    for slug, cs in by.items():
        counts = defaultdict(int)
        for c in cs:
            counts[c['fm'].get('work', '?')] += 1
        print(f'\n{slug}  (' + ', '.join(f'{counts[w]} {w}' for w in WORK if counts[w]) + ')')
        for w in WORK:
            group = [c for c in cs if c['fm'].get('work') == w]
            if not group or (w == 'closed' and not args.closed):
                continue
            print(f'  {w.upper()}')
            for c in sorted(group, key=lambda c: cid(c)):
                fm = c['fm']
                a = age_days(fm.get('last_verified_at'))
                stale = ' !' if (w == 'active' and a is not None and a > ACTIVE_STALE_DAYS) else ''
                kind = {'hypothesis': 'H', 'exploration': 'X', 'engineering': 'E'}.get(fm.get('kind'), '?')
                print(f'    {cid(c).split(":")[1]:<4}[{kind}] [{BADGE.get(fm.get("verdict"), "?")}] {fm.get("title", "")}')
                le = last_exp(c)
                bits = []
                if le:
                    bits.append(f'last {le.get("id")} {dstr(le.get("date"))} {le.get("status")}/{effect_for(c, le)}')
                if fm.get('next_action'):
                    bits.append(f'next: {fm["next_action"]}')
                if fm.get('blocked_by'):
                    bits.append(f'blocked: {fm["blocked_by"]}')
                if fm.get('work_reason'):
                    bits.append(f'why: {fm["work_reason"]}')
                sb = session_summary(c)
                if sb:
                    bits.append(sb)
                bits.append(f'verified {a}d ago{stale}' if a is not None else 'never verified')
                if fm.get('needs_review'):
                    bits.append('NEEDS REVIEW')
                print('         ' + ' | '.join(bits))


def cmd_show(args, cards):
    c, _, _ = parse_ref(cards, args.ref, args.project)
    fm = c['fm']
    assess = collect_assessments(cards)
    mine = assess.get(cid(c), [])
    print(f'{cid(c)}  [{fm.get("kind")}]  {fm.get("title")}')
    print(f'  work={fm.get("work")}' + (f' ({fm.get("work_reason")})' if fm.get('work_reason') else '') +
          f'  verdict={fm.get("verdict")}  verified={dstr(fm.get("last_verified_at"))} '
          f'({age_days(fm.get("last_verified_at"))}d ago)')
    if fm.get('needs_review'):
        print(f'  !! NEEDS REVIEW: {fm.get("review_note")}')
    for k in ('claim', 'scope', 'goal'):
        if fm.get(k):
            print(f'  {k}: {fm[k]}')
    fal = fm.get('falsifier')
    if fal:
        print(f'  falsifier [{fal.get("provenance")}]: {fal.get("text")}' + (f' (ref {fal["ref"]})' if fal.get('ref') else ''))
    if fm.get('supersedes'):
        print(f'  supersedes: {", ".join(fm["supersedes"])}')
    print(f'\n  NEXT: {fm.get("next_action") or "-"}')
    if fm.get('blocked_by'):
        print(f'  BLOCKED BY: {fm["blocked_by"]}')
    print(f'\n  VERDICT BASIS (hint from valid assessments, scope-blind: {verdict_hint(mine)}; stated: {fm.get("verdict")})')
    if fm.get('verdict_reason'):
        print(f'    reason: {fm["verdict_reason"]}')
    for a in sorted(mine, key=lambda a: a['date'] or date.min, reverse=True):
        tag = '' if a['valid'] else '  [EXCLUDED: not done or evaluation invalid]'
        print(f'    {a["ref"]} {dstr(a["date"])} {a["effect"]}{tag}')
        if a['scope']:
            print(f'        scope: {a["scope"]}')
        if a['note']:
            print(f'        {a["note"]}')
    corr = [(e, cid(c)) for c in cards for e in exps(c) if e.get('correction') or e.get('status') in ('invalid', 'failed')]
    mine_corr = [(e, o) for e, o in corr if o == cid(c)]
    if mine_corr:
        print('\n  CORRECTIONS / INVALIDATIONS')
        for e, o in mine_corr:
            print(f'    {o}/{e.get("id")} [{e.get("status")}] {e.get("correction") or ""}')
    print('\n  EXPERIMENTS')
    for e in sorted(exps(c), key=lambda e: dstr(e.get('date')), reverse=True):
        ev = e.get('evaluation') or {}
        print(f'    {e.get("id")} {dstr(e.get("date"))} [{e.get("status")}] eval.valid={ev.get("valid", "?")}  {e.get("title")}')
        if e.get('protocol'):
            print(f'        protocol: {e["protocol"]}')
        if e.get('runs_summary'):
            print(f'        runs: {e["runs_summary"]}')
        for r in e.get('runs') or []:
            a = age_days(r.get('observed_at'))
            state = r.get('state')
            if state in ('running', 'queued') and (a is None or a > RUN_STALE_DAYS):
                state = f'last observed {state} ({dstr(r.get("observed_at")) or "no date"}), currently unknown'
            print(f'        run {r.get("arm", "")} s={r.get("seed", "-")}: {state}')
        res = e.get('results') or {}
        for m in res.get('metrics') or []:
            spread = f' [{m["lo"]:.4g}, {m["hi"]:.4g}]' if m.get('lo') is not None else ''
            print(f'        metric {m.get("name")} {fmt_scope(m.get("scope"))} = {m.get("value")} {m.get("unit", "")} '
                  f'(n={m.get("n")}{spread}, {m.get("dir")} better)')
        for p in res.get('plots') or []:
            print(f'        plot {p.get("id")} [{p.get("role")}/{p.get("style")}] {p.get("out")}')
        for r in arm_compare(e):
            rel = f'{r["rel"] * 100:+.1f}%' if r['rel'] is not None else 'n/a'
            print(f'        arm: {arm_of(r["arm"])} vs {arm_of(r["ref"])} @ {fmt_scope(r["scope"])}: {rel} '
                  f'{r["verdict"]}' + (f' ({r["flag"]})' if r['flag'] else ''))
        for line in session_lines(c, e):
            print('        ' + line)
    for line in session_lines(c, None):
        print('  ' + line)
    if fm.get('source_refs'):
        print('\n  SOURCES: ' + '; '.join(map(str, fm['source_refs'])))
    body = c['body'].strip()
    if body:
        print('\n  ' + body.replace('\n', '\n  '))


def print_compare(res, items):
    print('COMPARISON: ' + ', '.join(l for l, _, _ in items))
    for label, c, e in items:
        for r in arm_compare(e):
            rel = f'{r["rel"] * 100:+.1f}%' if r['rel'] is not None else 'n/a'
            print(f'  [{label}] arm {arm_of(r["arm"])} vs {arm_of(r["ref"])} @ {fmt_scope(r["scope"])}: '
                  f'{r["ref"]["value"]:.4g}(n={r["ref"]["n"]}) -> {r["arm"]["value"]:.4g}(n={r["arm"]["n"]}) '
                  f'{rel} {r["verdict"]}' + (f' [{r["flag"]}]' if r['flag'] else ''))
    print('  ALIGNED ACROSS EXPERIMENTS:' + (' none' if not res['rows'] else ''))
    for row in res['rows']:
        vals = [f'{l}={m["value"]:.4g}(n={m["n"]})' for l, m in row['cells'].items()]
        print(f'    {row["key"][0]} {fmt_scope(dict(row["key"][2]))}: ' + '  '.join(vals))
    for la, lb, nm, why in res['blocked']:
        print(f'  NOT COMPARABLE {la} x {lb} ({nm}): {why}')
    for n in res['notes']:
        print(f'  NOTE {n}')
    for lbl, st in res['excluded']:
        print(f'  EXCLUDED {lbl}: status/valid = {st}')


def cmd_compare(args, cards):
    items = []
    for tok in args.refs:
        c, e, _ = parse_ref(cards, tok, args.project)
        if e is None:
            items += [(f'{cid(c)}/{x.get("id")}', c, x) for x in exps(c)]
        else:
            items.append((f'{cid(c)}/{e.get("id")}', c, e))
    if not items:
        raise SystemExit('nothing to compare')
    res = cross_compare(items)
    print_compare(res, items)
    if args.html:
        out = xp(args.html)
        out.parent.mkdir(parents=True, exist_ok=True)
        copy_assets(out.parent)
        out.write_text(compare_page(items, res), encoding='utf-8')
        print(f'wrote {out}')


def cmd_refresh(args, cards, root):
    targets = [find_card(cards, args.ref, args.project)] if args.ref else cards
    changed = 0
    for c in targets:
        lines = []
        for e in exps(c):
            if e.get('results'):
                lines += [(f'{cid(c)}/{e.get("id")}', lv, m) for lv, m in refresh_exp(c, e, args.accept)]
        if not lines:
            continue
        print(cid(c))
        for ref, lv, m in lines:
            print(f'  [{lv}] {ref}: {m}')
        if args.accept and any(lv == 'warn' for _, lv, _ in lines):
            with lock(root, c['slug']):
                fresh = parse_card(c['path'], c['slug'])
                # re-apply on the freshly read card so concurrent edits outside results are not lost
                for e_new, e_old in zip(exps(fresh), exps(c)):
                    if e_old.get('results'):
                        e_new['results'] = e_old['results']
                fresh['fm']['updated'] = today()
                write_card(fresh)
            changed += 1
    if args.accept:
        print(f'\naccepted changes in {changed} card(s)')
    else:
        print('\n(dry run; use --accept to rewrite cards)')


def cmd_lint(args, cards, pre):
    issues = pre + lint(cards, args.project)
    errs = [i for i in issues if i[0] == 'error']
    for lv, who, msg in sorted(issues, key=lambda i: (i[0] != 'error', i[1])):
        print(f'{lv.upper():5} {who}: {msg}')
    print(f'\n{len(errs)} error(s), {len(issues) - len(errs)} warning(s), {len(cards)} card(s)')
    return 1 if errs else 0


def cmd_render(args, cards, root):
    c, e, p = parse_ref(cards, args.ref, args.project)
    if p is None or not p.get('recipe'):
        raise SystemExit('ref must be slug:Qn/En/pn with a plot that has a recipe')
    reg = {}
    dash = root / 'dashboard.md'
    if dash.exists():
        for line in dash.read_text(encoding='utf-8').splitlines():
            m = re.match(r'-\s*([\w-]+):\s*(\S.*)$', line)
            if m:
                reg[m.group(1)] = m.group(2).strip()
    cwd = xp(reg[c['slug']]) if c['slug'] in reg else xp(p['recipe']).parent
    before = xp(p['out']).stat().st_mtime if xp(p['out']).exists() else 0
    r = subprocess.run(['uv', 'run', 'python', str(xp(p['recipe']))], cwd=cwd)
    out = xp(p['out'])
    ok = r.returncode == 0 and out.exists() and out.stat().st_size > 0 and out.stat().st_mtime > before
    print(f'render {"ok" if ok else "FAILED"}: {out} (cwd {cwd})')
    return 0 if ok else 1


# ------------------------------------------------------------------ html

CSS = """
:root{--bg:#f4f5f7;--panel:#fff;--ink:#1b2230;--muted:#6a7383;--faint:#9aa2b1;--line:#e2e5ea;--soft:#f7f8fa;
--accent:#3563d9;--sup:#1c8f4e;--ref:#cf3f3f;--inc:#c98a12;--cfl:#8f47c4;--un:#98a1b0;--warnbg:#fff6df;--warnln:#ecc75a;
--shadow:0 1px 2px rgba(20,30,50,.06),0 2px 8px rgba(20,30,50,.05)}
:root[data-theme=dark]{--bg:#14171c;--panel:#1c2027;--ink:#e3e7ee;--muted:#9aa3b3;--faint:#6b7483;--line:#2c323c;
--soft:#232831;--accent:#7aa0ff;--warnbg:#3a3120;--warnln:#8a6d25;--shadow:none}
.theme{position:fixed;top:12px;right:16px;z-index:10;display:flex;background:var(--panel);border:1px solid var(--line);
border-radius:999px;padding:2px;box-shadow:var(--shadow)}
.theme button{all:unset;cursor:pointer;font-size:12px;padding:3px 11px;border-radius:999px;color:var(--muted)}
.theme button:hover{color:var(--ink)}.theme button.on{background:var(--soft);color:var(--ink);font-weight:600}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 'Pretendard','Noto Sans KR','Noto Sans CJK KR',system-ui,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{font:12px ui-monospace,'JetBrains Mono',monospace;background:var(--soft);border:1px solid var(--line);border-radius:4px;padding:0 5px}
.top{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line)}
.top .in{max-width:1480px;margin:0 auto;padding:12px 24px 0}
.brand{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}.brand h1{font-size:18px;margin:0}.brand .meta{font-size:12px}
.tabs{display:flex;gap:2px;margin-top:10px;overflow-x:auto}
.tabs button{all:unset;cursor:pointer;padding:8px 14px;border-radius:8px 8px 0 0;color:var(--muted);font-weight:600;white-space:nowrap;
border:1px solid transparent;border-bottom:none;display:flex;gap:7px;align-items:center}
.tabs button:hover{color:var(--ink);background:var(--soft)}
.tabs button.on{color:var(--ink);background:var(--bg);border-color:var(--line)}
.cnt{font-size:11px;font-weight:600;background:var(--soft);color:var(--muted);border-radius:10px;padding:0 7px}
.tabs button.on .cnt{background:var(--panel)}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;flex:none}.dot.rev{background:var(--inc)}.dot.live{background:var(--sup)}
main{max-width:1480px;margin:0 auto;padding:18px 24px 40px}
.panel{display:none}.panel.on{display:block}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 16px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 14px;box-shadow:var(--shadow)}
.stat b{display:block;font-size:20px;line-height:1.2}.stat span{font-size:12px;color:var(--muted)}
.board{display:grid;grid-template-columns:repeat(5,minmax(210px,1fr));gap:14px;align-items:start}
.col{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:10px;min-height:80px}
.col h3{margin:2px 4px 10px;font-size:12px;letter-spacing:.04em;color:var(--muted);display:flex;justify-content:space-between}
.col .empty{color:var(--faint);font-size:12px;text-align:center;padding:14px 0}
.tile{display:block;color:inherit;background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--un);border-radius:10px;
padding:10px 12px;margin-bottom:10px;box-shadow:var(--shadow);transition:transform .08s,border-color .08s}
.tile:hover{text-decoration:none;transform:translateY(-1px);border-color:var(--accent)}
.tile.v-supported{border-left-color:var(--sup)}.tile.v-refuted{border-left-color:var(--ref)}.tile.v-inconclusive{border-left-color:var(--inc)}
.tile.v-conflicting{border-left-color:var(--cfl)}
.tile .hd{display:flex;gap:6px;align-items:center;font-size:12px;color:var(--muted);margin-bottom:4px}
.tile .t{font-weight:600;line-height:1.35}
.tile .nx{margin-top:6px;font-size:12.5px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.tile .ft{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:11.5px;color:var(--faint)}
.pill{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600;
background:var(--soft);color:var(--muted);border:1px solid var(--line);white-space:nowrap}
.pill.v-supported{color:var(--sup)}.pill.v-refuted{color:var(--ref)}.pill.v-inconclusive{color:var(--inc)}.pill.v-conflicting{color:var(--cfl)}
.pill.warn{color:var(--inc);border-color:var(--warnln);background:var(--warnbg)}.pill.bad{color:var(--ref)}.pill.good{color:var(--sup)}
.kind{font:700 10px ui-monospace,monospace;border-radius:4px;padding:1px 5px;background:var(--soft);border:1px solid var(--line);color:var(--muted)}
.wrap{max-width:1100px;margin:0 auto;padding:6px 24px 56px}
.crumb{font-size:13px;margin-bottom:6px}
.title h1{font-size:22px;margin:0 0 8px;line-height:1.3}.title .row{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.box{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px;box-shadow:var(--shadow);margin-bottom:16px}
.box h2{font-size:13px;letter-spacing:.04em;color:var(--muted);margin:0 0 10px}
.kv{display:grid;grid-template-columns:96px 1fr;gap:7px 14px;margin:0}.kv dt{color:var(--muted);font-size:13px}.kv dd{margin:0}
.warnbox{background:var(--warnbg);border:1px solid var(--warnln);border-radius:10px;padding:9px 13px;margin:10px 0;font-size:13px}
.meta{color:var(--muted);font-size:12.5px}
.lin{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0}
figure{margin:0;background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px}
figure img{width:100%;display:block}figcaption{font-size:12px;color:#555;margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;font-size:11.5px;letter-spacing:.03em;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line);padding:6px 8px}
td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;font-size:11.5px;background:var(--soft);border:1px solid var(--line);border-radius:5px;padding:0 6px;margin:1px 3px 1px 0;color:var(--muted)}
.tag b{color:var(--ink);font-weight:600}
h4{font-size:13px;margin:18px 0 8px;color:var(--muted);letter-spacing:.03em}
.up{color:var(--sup);font-weight:600}.down{color:var(--ref);font-weight:600}
ul.plain{list-style:none;padding:0;margin:6px 0}ul.plain li{margin:4px 0;font-size:13px}
.hero{background:var(--panel);border-bottom:1px solid var(--line)}
.hero .in{max-width:1100px;margin:0 auto;padding:14px 24px 20px}
.hero .id{font:600 13px ui-monospace,monospace;color:var(--muted)}
.hero h1{font-size:24px;line-height:1.3;margin:2px 0 10px;padding-right:130px}
.hero .row{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.sum{display:grid;grid-template-columns:1fr 1.35fr 0.9fr;gap:12px;margin-top:16px}
.sumc{border:1px solid var(--line);border-radius:12px;padding:12px 15px;background:var(--soft)}
.sumc .lb{font-size:11.5px;color:var(--muted);font-weight:700;letter-spacing:.05em;margin-bottom:7px}
.sumc .big{font-size:17px;font-weight:700;margin-bottom:4px}
.sumc p{margin:4px 0 0;font-size:13.5px}
.sumc.nx{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 7%,var(--panel))}
.sumc.nx .txt{font-size:14.5px;font-weight:600;line-height:1.5}
.sumc .blk{margin-top:8px;font-size:13px;color:var(--ref)}
.sumc.v-supported{border-top:3px solid var(--sup)}.sumc.v-refuted{border-top:3px solid var(--ref)}
.sumc.v-inconclusive{border-top:3px solid var(--inc)}.sumc.v-conflicting{border-top:3px solid var(--cfl)}.sumc.v-unassessed{border-top:3px solid var(--un)}
.sumc .big.v-supported{color:var(--sup)}.sumc .big.v-refuted{color:var(--ref)}.sumc .big.v-inconclusive{color:var(--inc)}.sumc .big.v-conflicting{color:var(--cfl)}
.clamp{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
details.review{background:var(--warnbg);border:1px solid var(--warnln);border-radius:10px;margin:16px 0 0;font-size:13px}
details.review>summary{cursor:pointer;padding:9px 14px;font-weight:600;color:var(--inc)}
details.review>div{padding:0 14px 12px}
.sec{display:flex;align-items:baseline;gap:10px;margin:28px 0 10px}.sec h2{font-size:16px;margin:0}.sec .meta{font-size:12.5px}
.claim{font-size:16px;line-height:1.6;border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:2px 0 14px}
.note{white-space:pre-wrap;color:var(--muted);font-size:13px;margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)}
.tl{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);overflow:hidden}
details.er+details.er,details.er+.er,.er+details.er{border-top:1px solid var(--line)}
details.er>summary,.er.ext{display:grid;grid-template-columns:40px 84px minmax(0,1fr) auto;gap:12px;align-items:start;
padding:12px 16px;list-style:none;border-left:4px solid var(--line)}
details.er>summary{cursor:pointer}details.er>summary::-webkit-details-marker{display:none}
details.er>summary:hover{background:var(--soft)}details.er[open]>summary{background:var(--soft)}
.er .eid{font:700 13px ui-monospace,monospace;color:var(--accent);padding-top:1px}
.er .d{font-size:12px;color:var(--faint);padding-top:2px}
.er .ttl{font-weight:600;line-height:1.4}.er .one{font-size:12.5px;color:var(--muted);margin-top:3px}
.er .st{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
.er.e-supports>summary,.er.ext.e-supports{border-left-color:var(--sup)}.er.e-refutes>summary,.er.ext.e-refutes{border-left-color:var(--ref)}
.er.e-inconclusive>summary,.er.ext.e-inconclusive{border-left-color:var(--inc)}
.er.e-run>summary{border-left-color:var(--accent)}
.rb{padding:6px 20px 20px 60px;border-top:1px dashed var(--line)}
.plot{max-width:860px;margin:14px 0 4px}
.rt{margin:10px 0 4px}
.rt .cond{font-size:12.5px;color:var(--muted);margin:0 0 10px;line-height:1.7}.rt .cond b{color:var(--ink);font-weight:600}
table.mx{width:auto;min-width:min(100%,560px);max-width:100%;border:1px solid var(--line);border-radius:10px;border-collapse:separate;border-spacing:0;overflow:hidden}
table.mx th{background:var(--soft);padding:8px 14px;border-bottom:1px solid var(--line)}
table.mx th.arm{text-align:right;min-width:130px;color:var(--ink);font-size:12.5px;border-left:1px solid var(--line)}
table.mx th.arm .ref{margin-left:5px}
table.mx td{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
table.mx tr:last-child td{border-bottom:none}
table.mx tr.grp td{background:var(--soft);font-size:12px;color:var(--muted);padding:5px 14px}
table.mx tr.grp b{color:var(--ink);font-weight:600}
table.mx td.mn{min-width:230px}
table.mx td.mn .nm{font-weight:600}table.mx td.mn .dir{color:var(--faint);font-size:12px;margin-left:4px}
table.mx td.mn .cd{font-size:12px;color:var(--muted);margin-left:6px}
table.mx td.cell{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;border-left:1px solid var(--line)}
table.mx th.arm:nth-child(even),table.mx td.cell:nth-child(even){background:color-mix(in srgb,var(--soft) 55%,var(--panel))}
table.mx td.mn{border-right:2px solid var(--line)}table.mx th:first-child{border-right:2px solid var(--line)}
table.mx td.cell.na{color:var(--faint);font-size:12px}
table.mx td.cell .v{font-size:14.5px}table.mx td.cell.best .v{font-weight:700;color:var(--sup)}
table.mx td.cell .s{font-size:11.5px;color:var(--faint);margin-top:1px}
table.mx td.cell .dl{font-size:12px;margin-top:1px}
.ref{font-size:10.5px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 4px;background:var(--panel)}
.caution{font-size:11px;color:var(--inc)}
.rt .foot-note{font-size:12px;color:var(--faint);margin-top:6px}
.katex{font-size:1.04em}
details.more{margin-top:16px;border-top:1px solid var(--line);padding-top:10px}
details.more>summary{cursor:pointer;color:var(--muted);font-size:13px;font-weight:600}
.foot{margin-top:28px}
@media (max-width:1100px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}.sum{grid-template-columns:1fr}}
@media (max-width:760px){details.er>summary,.er.ext{grid-template-columns:40px minmax(0,1fr)}
details.er>summary>*:not(.eid),.er.ext>*:not(.eid){grid-column:2}.er .st{justify-content:flex-start}.rb{padding-left:20px}}
"""

WORK_LABEL = {'active': '진행', 'waiting': '대기', 'candidate': '후보', 'parked': '보류', 'closed': '종료'}
VERDICT_LABEL = {'supported': '지지', 'refuted': '반박', 'inconclusive': '불충분', 'conflicting': '상충', 'unassessed': '미평가'}
KIND_LABEL = {'hypothesis': 'H', 'exploration': 'X', 'engineering': 'E'}
STATUS_LABEL = {'planned': '계획', 'running': '실행 중', 'analyzing': '분석 중', 'done': '완료', 'failed': '실패', 'invalid': '무효'}
EFFECT_LABEL = {'supports': '지지', 'refutes': '반박', 'inconclusive': '불충분', 'none': '판정 없음'}


def esc(x) -> str:
    return html.escape('' if x is None else str(x))


def fnum(v):
    return '-' if v is None else format(v, '.4g')


def ago(x):
    a = age_days(x)
    return '-' if a is None else ('오늘' if a == 0 else f'{a}일 전')


def img_tag(path):
    p = xp(path)
    if not p.exists() or p.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
        return f'<p class=warnbox>plot file unavailable: {esc(path)}</p>'
    if p.stat().st_size > MAX_EMBED_BYTES:
        return f'<p class=warnbox>plot too large to embed ({p.stat().st_size // 1024} KB): <a href="file://{esc(p)}">{esc(p.name)}</a></p>'
    mime = 'image/png' if p.suffix.lower() == '.png' else 'image/jpeg'
    return f'<img src="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}" alt="{esc(p.name)}">'


def lineage_html(res):
    parts = []
    for s in res.get('sources') or []:
        p = xp(s.get('path', ''))
        if not p.exists():
            parts.append(f'<span class="pill bad" title="{esc(p)}">{esc(p.name)} · missing</span>')
            continue
        cur, stored = sha12(p), str(s.get('sha256', ''))[:12]
        ok = bool(stored) and cur.startswith(stored)
        parts.append(f'<span class="pill {"good" if ok else "bad"}" title="{esc(p)}">{esc(p.name)} · '
                     f'{"최신" if ok else "변경됨 (refresh 필요)"}</span>')
    return ''.join(parts)


def vpill(v):
    return f'<span class="pill v-{esc(v)}">{esc(VERDICT_LABEL.get(v, v))}</span>'


def chips(fm):
    w = fm.get('work')
    out = f'<span class=kind>{esc(KIND_LABEL.get(fm.get("kind"), "?"))}</span><span class=pill>{esc(WORK_LABEL.get(w, w))}</span>{vpill(fm.get("verdict"))}'
    if fm.get('needs_review'):
        out += '<span class="pill warn">검토 필요</span>'
    return out


def session_pills(c, e=None):
    out = ''
    for s in sessions_of(c, e):
        st = state_of(s)[0]
        cls = 'good' if st == 'live' else ('warn' if st.startswith('live') else '')
        dot = '<span class="dot live"></span>' if st == 'live' else ''
        ref = cid(c) + (f'/{e.get("id")}' if e is not None else '')
        out += (f'<li><span class="pill {cls}">{dot}{esc(st)}</span> {esc(s.get("title") or str(s.get("id"))[:8])} '
                f'<code>rboard open {esc(ref)}</code></li>')
    return f'<ul class=plain>{out}</ul>' if out else ''


def scope_tags(scope, skip=()):
    return ''.join(f'<span class=tag>{esc(k)} <b>{esc(v)}</b></span>' for k, v in (scope or {}).items() if k not in skip)


def common_scope(ms):
    if len(ms) < 2:
        return {}
    first = ms[0].get('scope') or {}
    return {k: v for k, v in first.items()
            if all(str((m.get('scope') or {}).get(k)) == str(v) for m in ms[1:])}


EFFECT_CLS = {'supports': 'v-supported', 'refutes': 'v-refuted', 'inconclusive': 'v-inconclusive'}
CAUTION_LABEL = {'ranges overlap': '범위 겹침', 'n=1: no spread': 'n=1'}


def metric_label(m):
    """Display name: `label` (may contain $...$ LaTeX) or the raw metric name."""
    return esc(m.get('label') or m.get('name'))


def result_matrix(e):
    """Metrics as a compact table: rows = metric (+ the conditions that still differ), columns = arms.

    Conditions shared by every metric print once above the table. A condition key present in every row
    with few distinct values (e.g. the evaluation protocol) becomes a group header instead of being
    repeated per row. Each non-reference cell shows its change against the reference arm of its row.
    """
    ms = [m for m in (e.get('results') or {}).get('metrics') or [] if m.get('value') is not None]
    if not ms:
        return '<p class=meta>핵심 지표가 붙어 있지 않습니다.</p>'
    com = common_scope(ms)
    cmp_rows = arm_compare(e)
    delta = {id(r['arm']): r for r in cmp_rows}
    refs = {id(r['ref']) for r in cmp_rows}
    arms = []
    for m in sorted(ms, key=lambda m: not m.get('baseline')):
        a = arm_of(m) if m.get('arm_key') else '값'
        if a not in arms:
            arms.append(a)
    ref_arms = {arm_of(r['ref']) for r in cmp_rows}
    rows = {}
    for m in ms:
        skip = set(com) | ({m['arm_key']} if m.get('arm_key') else set())
        cond = tuple((k, str(v)) for k, v in (m.get('scope') or {}).items() if k not in skip)
        rows.setdefault((m.get('name'), str(m.get('unit', '')), cond), {})[arm_of(m) if m.get('arm_key') else '값'] = m
    # group key: in every row's conditions, and fewer distinct values than rows
    keys = [dict(k[2]) for k in rows]
    gkey = None
    if len(rows) > 2:
        for k in keys[0]:
            vals = [d.get(k) for d in keys]
            if None not in vals and len(set(vals)) < len(vals):
                gkey = k
                break
    all_n1 = all((m.get('n') or 1) <= 1 for m in ms)
    body, cur = '', object()
    ordered = sorted(rows.items(), key=lambda kv: str(dict(kv[0][2]).get(gkey, ''))) if gkey else list(rows.items())
    for (name, unit, cond), cells in ordered:
        cd = dict(cond)
        if gkey and cd.get(gkey) != cur:
            cur = cd.get(gkey)
            body += f'<tr class=grp><td colspan={len(arms) + 1}>{esc(gkey)} <b>{esc(cur)}</b></td></tr>'
        first = next(iter(cells.values()))
        lower = first.get('dir') == 'lower'
        vals = [m['value'] for m in cells.values()]
        best = (min(vals) if lower else max(vals)) if len(vals) > 1 else None
        tds = ''
        for a in arms:
            m = cells.get(a)
            if m is None:
                tds += '<td class="cell na" title="이 arm에는 측정값 없음">없음</td>'
                continue
            sub = []
            if (m.get('n') or 1) > 1:
                sub.append(f'n={m["n"]}' + (f' · {fnum(m["lo"])}–{fnum(m["hi"])}' if m.get('lo') is not None else ''))
            elif not all_n1:
                sub.append('n=1')
            extra = ''
            if id(m) in delta:
                r = delta[id(m)]
                cls = {'better': 'up', 'worse': 'down'}.get(r['verdict'], '')
                rel = f'{r["rel"] * 100:+.1f}%' if r['rel'] is not None else 'n/a'
                extra = f'<div class="dl {cls}">{rel}</div>'
                if r['flag'] == 'ranges overlap':
                    extra += '<div class=caution>범위 겹침</div>'
            tds += (f'<td class="cell{" best" if best is not None and m["value"] == best else ""}">'
                    f'<div class=v>{fnum(m["value"])}</div>{extra}'
                    f'{("<div class=s>" + esc(" ".join(sub)) + "</div>") if sub else ""}</td>')
        rest = [(k, v) for k, v in cond if k != gkey]
        cond_txt = ' · '.join(f'{esc(k)} {esc(v)}' for k, v in rest)
        arrow = f'<span class=dir title="{"낮을수록" if lower else "높을수록"} 좋음">{"↓" if lower else "↑"}</span>'
        body += (f'<tr><td class=mn><span class=nm>{metric_label(first)}</span>'
                 f'{(" <span class=meta>" + esc(unit) + "</span>") if unit else ""}{arrow}'
                 f'{("<span class=cd>" + cond_txt + "</span>") if cond_txt else ""}</td>{tds}</tr>')
    head = ''.join(f'<th class=arm>{esc(a)}{"<span class=ref>기준</span>" if a in ref_arms else ""}</th>' for a in arms)
    cond_line = ('<div class=cond>공통 조건 · ' + ' · '.join(f'{esc(k)} <b>{esc(v)}</b>' for k, v in com.items()) + '</div>') if com else ''
    notes = ['↑↓ = 좋은 방향', '초록 굵은 값 = 행에서 가장 좋음', '% = 기준 arm 대비 변화', 'min–max는 신뢰구간이 아님']
    if all_n1:
        notes.insert(0, '모든 값이 n=1 (단일 seed/run)이라 차이의 크기는 확정되지 않음')
    return (f'<div class=rt>{cond_line}<table class=mx><tr><th>지표</th>{head}</tr>{body}</table>'
            f'<div class=foot-note>{" · ".join(notes)}</div></div>')


def exp_one_line(c, e):
    a = e.get('assess') or {}
    x = a.get(cid(c)) or (next(iter(a.values())) if a else None) or {}
    return (x or {}).get('note') or e.get('protocol') or ''


def exp_row(c, e, open_=False):
    res = e.get('results') or {}
    ev = e.get('evaluation') or {}
    eff = effect_for(c, e)
    running = e.get('status') in ('running', 'analyzing')
    row_cls = 'e-run' if running else f'e-{eff}'
    status = f'<span class=pill>{esc(STATUS_LABEL.get(e.get("status"), e.get("status")))}</span>'
    effect = f'<span class="pill {EFFECT_CLS.get(eff, "")}">{esc(EFFECT_LABEL.get(eff, eff))}</span>' if eff != 'none' else ''
    live = any(state_of(s)[0] == 'live' for s in sessions_of(c, e))
    live_pill = '<span class="pill good"><span class="dot live"></span>세션</span>' if live else ''
    warn = ''
    if e.get('correction'):
        warn += f'<div class=warnbox><b>정정</b> {esc(e["correction"])}</div>'
    if not (exp_valid(e) or running or e.get('status') == 'planned'):
        warn += '<div class=warnbox>판정과 비교에서 제외된 실험입니다 (미완료이거나 평가가 무효).</div>'
    plots = ''.join(
        f'<figure class=plot>{img_tag(p.get("out"))}<figcaption>'
        f'{("<span class=\"pill warn\">스타일 미검증</span> ") if p.get("style") == "legacy" else ""}<b>{esc(p.get("title"))}</b>'
        f'{("<br>" + esc(p.get("caption"))) if p.get("caption") else ""}</figcaption></figure>'
        for p in res.get('plots') or [])
    tables = ''
    for t in res.get('tables') or []:
        head = ''.join(f'<th>{esc(x)}</th>' for x in t.get('columns', []))
        body = ''.join('<tr>' + ''.join(f'<td>{esc(v)}</td>' for v in row) + '</tr>' for row in t.get('rows', []))
        tables += (f'<h4>{esc(t.get("title"))}</h4><table><tr>{head}</tr>{body}</table>'
                   f'{("<p class=meta>" + esc(t.get("note")) + "</p>") if t.get("note") else ""}')
    runs = ''
    for r in e.get('runs') or []:
        a = age_days(r.get('observed_at'))
        st = r.get('state')
        if st in ('running', 'queued') and (a is None or a > RUN_STALE_DAYS):
            st = f'마지막 관측 {st} ({dstr(r.get("observed_at")) or "날짜 없음"}), 현재 미확인'
        runs += f'<li><span class=pill>{esc(st)}</span> {esc(r.get("arm"))} · seed {esc(r.get("seed", "-"))}</li>'
    kv = ''
    for k, v in (('프로토콜', e.get('protocol')), ('실행', e.get('runs_summary')),
                 ('평가', ' · '.join(x for x in (f'valid={ev.get("valid", "?")}', str(ev.get('version') or ''),
                                                str(ev.get('note') or '')) if x)),
                 ('journal', e.get('journal'))):
        if v:
            kv += f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>'
    if res.get('sources'):
        kv += f'<dt>원본</dt><dd><div class=lin>{lineage_html(res)}</div></dd>'
    if runs:
        kv += f'<dt>run</dt><dd><ul class=plain>{runs}</ul></dd>'
    sess = session_pills(c, e)
    if sess:
        kv += f'<dt>세션</dt><dd>{sess}</dd>'
    has_results = bool(res.get('metrics') or res.get('plots') or res.get('tables'))
    results_html = (f'<h4>결과</h4>{plots}{result_matrix(e) if res.get("metrics") else ""}{tables}' if has_results
                    else '<p class=meta style="margin-top:12px">붙어 있는 결과가 없습니다. 세부 정보를 참고하세요.</p>')
    return f'''<details class="er {row_cls}"{" open" if open_ else ""}><summary>
<span class=eid>{esc(e.get("id"))}</span><span class=d>{esc(dstr(e.get("date")))}</span>
<div><div class=ttl>{esc(e.get("title"))}</div><div class="one clamp">{esc(exp_one_line(c, e))}</div></div>
<span class=st>{live_pill}{status}{effect}</span></summary>
<div class=rb>{warn}{results_html}
<details class=more{" open" if not has_results else ""}><summary>세부 정보 (프로토콜 · 평가 · 원본 · run · 세션)</summary>
<dl class=kv style="margin-top:10px">{kv}</dl></details></div></details>'''


def exp_section(c, e, open_=True):
    """One experiment as a standalone block (compare pages)."""
    return f'<div class=tl>{exp_row(c, e, open_)}</div>'


def compare_block(items):
    res = cross_compare(items)
    body = ''
    if res['rows']:
        heads = ''.join(f'<th class=arm>{esc(l.split("/")[-1])}</th>' for l, _, _ in items)
        rows = ''
        for row in res['rows']:
            ms = list(row['cells'].values())
            vals = [m['value'] for m in ms]
            best = min(vals) if ms[0].get('dir') == 'lower' else max(vals)
            tds = ''
            for l, _, _ in items:
                m = row['cells'].get(l)
                if m is None:
                    tds += '<td class=cell><span class=s>–</span></td>'
                else:
                    cls = ' best' if m['value'] == best and len(ms) > 1 else ''
                    tds += f'<td class="cell{cls}"><div class=v>{fnum(m["value"])}</div><div class=s>n={m["n"]}</div></td>'
            rows += f'<tr><td><b>{esc(row["key"][0])}</b><div>{scope_tags(dict(row["key"][2]))}</div></td>{tds}</tr>'
        body += f'<table class=mx><tr><th>지표</th>{heads}</tr>{rows}</table>'
    else:
        body += '<p class=meta>이름·단위·조건이 모두 같은 지표가 없어 실험끼리 나란히 놓을 수 있는 수치가 없습니다.</p>'
    blocked = ''.join(f'<li><b>{esc(la.split("/")[-1])} × {esc(lb.split("/")[-1])}</b> ({esc(nm)}): {esc(why)}</li>'
                      for la, lb, nm, why in res['blocked'])
    if blocked:
        body += (f'<details class=more><summary>비교 불가 {len(res["blocked"])}건: 이름은 같지만 조건이 다른 지표</summary>'
                 f'<ul class=plain>{blocked}</ul></details>')
    for n in res['notes']:
        body += f'<div class=warnbox>{esc(n)}</div>'
    if res['excluded']:
        body += '<p class=meta>제외: ' + ', '.join(esc(l.split('/')[-1]) for l, _ in res['excluded']) + ' (미완료이거나 평가 무효)</p>'
    return f'<div class=box>{body}</div>'


THEME_HEAD_JS = "try{document.documentElement.dataset.theme=localStorage.rboardTheme||'light'}catch(e){}"
THEME_JS = """
document.querySelectorAll('.theme button').forEach(b=>{
b.classList.toggle('on',b.dataset.t===document.documentElement.dataset.theme);
b.onclick=()=>{document.documentElement.dataset.theme=b.dataset.t;try{localStorage.rboardTheme=b.dataset.t}catch(e){}
document.querySelectorAll('.theme button').forEach(x=>x.classList.toggle('on',x===b))}});
"""
THEME_SWITCH = '<div class=theme role=group aria-label="테마"><button data-t=light>라이트</button><button data-t=dark>다크</button></div>'


ASSETS = Path(__file__).resolve().parent.parent / 'assets'
MATH_JS = """
if(window.renderMathInElement)renderMathInElement(document.body,{delimiters:[
{left:'$$',right:'$$',display:true},{left:'\\\\[',right:'\\\\]',display:true},
{left:'$',right:'$',display:false},{left:'\\\\(',right:'\\\\)',display:false}],
ignoredTags:['script','noscript','style','textarea','pre','code'],throwOnError:false});
"""


def copy_assets(out: Path):
    """Vendored KaTeX (assets/katex, MIT) next to the generated pages: math renders offline."""
    import shutil
    shutil.copytree(ASSETS / 'katex', out / 'assets' / 'katex', dirs_exist_ok=True)


def page(title, body, script='', base=''):
    """Theme is the user's choice (light by default), stored in localStorage and shared by every page.

    `base` is the relative path from the page to the board root (where assets/ lives). Text between
    $...$, $$...$$, \\(...\\) or \\[...\\] is rendered with KaTeX (code/pre blocks are left alone).
    """
    k = f'{base}assets/katex'
    return (f'<!doctype html><html lang=ko data-theme=light><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1"><script>{THEME_HEAD_JS}</script>'
            f'<title>{esc(title)}</title><link rel=stylesheet href="{k}/katex.min.css"><style>{CSS}</style>'
            f'<script defer src="{k}/katex.min.js"></script><script defer src="{k}/contrib/auto-render.min.js"></script>'
            f'<body>{THEME_SWITCH}{body}'
            f'<script>{THEME_JS}{script}</script>'
            f'<script>document.addEventListener("DOMContentLoaded",()=>{{{MATH_JS}}})</script></body></html>')


def compare_page(items, res=None):
    parts = ['<div class=wrap><div class=title><h1>실험 비교</h1></div>']
    for label, c, e in items:
        parts.append(f'<p class=crumb><b>{esc(label)}</b> · {esc(c["fm"].get("title"))}</p>' + exp_section(c, e))
    parts.append(compare_block(items) + '</div>')
    return page('rboard compare', ''.join(parts))


KIND_FULL = {'hypothesis': '가설', 'exploration': '탐색', 'engineering': '엔지니어링'}


def card_page(c, cards):
    fm = c['fm']
    mine = collect_assessments(cards).get(cid(c), [])
    hint = verdict_hint(mine)
    v = fm.get('verdict')
    fal = fm.get('falsifier') or {}
    es = sorted(exps(c), key=lambda e: dstr(e.get('date')), reverse=True)
    es = sorted(es, key=lambda e: e.get('status') not in ('running', 'analyzing'))
    n_run = sum(1 for e in es if e.get('status') in ('running', 'analyzing'))
    n_done = sum(1 for e in es if e.get('status') == 'done')
    live = [(e, s) for e in [None, *es] for s in sessions_of(c, e) if state_of(s)[0] == 'live']

    # hero: what is this, what is the verdict, what do I do next
    pills = (f'<span class=pill>{esc(KIND_FULL.get(fm.get("kind"), fm.get("kind")))}</span>'
             f'<span class=pill>{esc(WORK_LABEL.get(fm.get("work"), fm.get("work")))}</span>'
             + (f'<span class=pill>goal {esc(fm.get("goal"))}</span>' if fm.get('goal') else ''))
    verdict_tile = (f'<div class="sumc v-{esc(v)}"><div class=lb>판정</div><div class="big v-{esc(v)}">{esc(VERDICT_LABEL.get(v, v))}</div>'
                    + (f'<p class=clamp>{esc(fm.get("verdict_reason"))}</p>' if fm.get('verdict_reason') else '')
                    + (f'<p class=meta>실험 근거로 계산한 힌트는 {esc(VERDICT_LABEL.get(hint, hint))}</p>' if hint != v else '')
                    + '</div>')
    next_tile = (f'<div class="sumc nx"><div class=lb>다음 행동</div><div class=txt>{esc(fm.get("next_action") or "정해지지 않음")}</div>'
                 + (f'<div class=blk>막힘 · {esc(fm["blocked_by"])}</div>' if fm.get('blocked_by') else '')
                 + (f'<p class=meta>{esc(WORK_LABEL.get(fm.get("work")))} 사유 · {esc(fm["work_reason"])}</p>' if fm.get('work_reason') else '')
                 + '</div>')
    open_cmd = ''
    if live:
        e0 = live[0][0]
        ref = cid(c) + (f'/{e0.get("id")}' if e0 is not None else '')
        open_cmd = f'<p><span class="pill good"><span class="dot live"></span>세션 실행 중</span></p><p><code>rboard open {esc(ref)}</code></p>'
    state_tile = (f'<div class=sumc><div class=lb>현황</div>'
                  f'<p>실험 {len(es)}개 · 완료 {n_done} · 실행 중 {n_run}</p>'
                  f'<p>검증 {esc(ago(fm.get("last_verified_at")))} <span class=meta>({esc(dstr(fm.get("last_verified_at")))})</span></p>'
                  f'{open_cmd}</div>')
    review = (f'<details class=review><summary>⚠ 검토 필요: 기록끼리 서로 다르다 (눌러서 보기)</summary>'
              f'<div>{esc(fm.get("review_note"))}</div></details>') if fm.get('needs_review') else ''
    hero = (f'<header class=hero><div class=in><div class=crumb><a href="../index.html#{esc(c["slug"])}">← {esc(c["slug"])} 보드</a></div>'
            f'<div class=id>{esc(cid(c))}</div><h1>{esc(fm.get("title"))}</h1><div class=row>{pills}</div>'
            f'<div class=sum>{verdict_tile}{next_tile}{state_tile}</div>{review}</div></header>')

    # the question
    q = ''
    if fm.get('claim'):
        q += f'<p class=claim>{esc(fm["claim"])}</p>'
    kv = ''
    if fm.get('scope'):
        kv += f'<dt>적용 범위</dt><dd>{esc(fm["scope"])}</dd>'
    if fal.get('text'):
        prov = {'retrospective': '사후 재구성', 'prospective': '사전 기록', 'unknown': '출처 불명'}.get(fal.get('provenance'), fal.get('provenance'))
        kv += (f'<dt>반증 조건</dt><dd><span class=pill>{esc(prov)}</span> {esc(fal["text"])}'
               f'{(" <span class=meta>(" + esc(fal["ref"]) + ")</span>") if fal.get("ref") else ""}</dd>')
    if fm.get('supersedes'):
        kv += f'<dt>대체한 카드</dt><dd>{esc(", ".join(fm["supersedes"]))}</dd>'
    note = c['body'].strip()
    question = (f'<div class=sec><h2>질문</h2></div><div class=box>{q}'
                f'{("<dl class=kv>" + kv + "</dl>") if kv else ""}'
                f'{("<div class=note>" + esc(note) + "</div>") if note else ""}</div>')

    # experiments: own ones as expandable rows, evidence owned by other cards as linked rows
    with_res = [e for e in es if (e.get('results') or {}).get('metrics') or (e.get('results') or {}).get('plots')]
    first = (with_res or es or [None])[0]
    rows = ''.join(exp_row(c, e, open_=(e is first)) for e in es)
    for a in sorted((a for a in mine if a['owner'] != cid(c)), key=lambda a: a['date'] or date.min, reverse=True):
        slug, q_ = a['owner'].split(':')
        rows += (f'<div class="er ext e-{esc(a["effect"])}"><span class=eid>↗</span><span class=d>{esc(dstr(a["date"]))}</span>'
                 f'<div><div class=ttl><a href="{esc(slug)}-{esc(q_)}.html">{esc(a["ref"])}</a> '
                 f'<span class=meta>다른 카드의 실험</span></div><div class="one clamp">{esc(a["note"] or a["scope"])}</div></div>'
                 f'<span class=st><span class="pill {EFFECT_CLS.get(a["effect"], "")}">{esc(EFFECT_LABEL.get(a["effect"], a["effect"]))}</span></span></div>')
    experiments = (f'<div class=sec><h2>실험</h2><span class=meta>실행 중인 것 먼저, 그다음 최신순. 줄을 누르면 결과가 펼쳐진다.</span></div>'
                   f'<div class=tl>{rows or "<p class=meta style=\"padding:14px\">연결된 실험이 없습니다.</p>"}</div>')
    items = [(f'{cid(c)}/{e.get("id")}', c, e) for e in es]
    compare = (f'<div class=sec><h2>실험 간 비교</h2></div>{compare_block(items)}') if len(items) > 1 else ''

    srcs = ''.join(f'<li class=meta>{esc(s)}</li>' for s in fm.get('source_refs') or [])
    foot = (f'<details class="more foot"><summary>출처와 기록 정보</summary><dl class=kv style="margin-top:10px">'
            f'<dt>갱신</dt><dd>{esc(dstr(fm.get("updated")))}</dd>'
            f'<dt>검증</dt><dd>{esc(dstr(fm.get("last_verified_at")))}</dd>'
            f'<dt>카드 파일</dt><dd><code>{esc(short(c["path"]))}</code></dd>'
            f'{("<dt>출처</dt><dd><ul class=plain>" + srcs + "</ul></dd>") if srcs else ""}'
            f'{("<dt>카드 세션</dt><dd>" + session_pills(c) + "</dd>") if sessions_of(c) else ""}</dl></details>')
    return page(cid(c), hero + f'<div class=wrap>{question}{experiments}{compare}{foot}</div>', base='../')


TABS_JS = """
const bs=[...document.querySelectorAll('.tabs button')],ps=[...document.querySelectorAll('.panel')];
function show(s){if(!ps.some(p=>p.id==='p-'+s))s=ps[0].id.slice(2);
bs.forEach(b=>b.classList.toggle('on',b.dataset.s===s));ps.forEach(p=>p.classList.toggle('on',p.id==='p-'+s));
history.replaceState(null,'','#'+s);try{localStorage.rboardTab=s}catch(e){}}
bs.forEach(b=>b.onclick=()=>show(b.dataset.s));
show(decodeURIComponent(location.hash.slice(1))||(()=>{try{return localStorage.rboardTab}catch(e){}})()||'');
"""


def tile(c):
    fm = c['fm']
    slug, q = c['slug'], cid(c).split(':')[1]
    le = last_exp(c)
    a = age_days(fm.get('last_verified_at'))
    foot = []
    if le:
        foot.append(f'{esc(le.get("id"))} {esc(STATUS_LABEL.get(le.get("status"), le.get("status")))} · {esc(dstr(le.get("date")))}')
    foot.append(f'검증 {ago(fm.get("last_verified_at"))}')
    live = any(state_of(s)[0] == 'live' for x in [None, *exps(c)] for s in sessions_of(c, x))
    flags = ''
    if live:
        flags += '<span class="pill good"><span class="dot live"></span>세션</span>'
    if fm.get('needs_review'):
        flags += '<span class="pill warn">검토</span>'
    if fm.get('work') == 'active' and a is not None and a > ACTIVE_STALE_DAYS:
        flags += '<span class="pill bad">오래됨</span>'
    return (f'<a class="tile v-{esc(fm.get("verdict"))}" href="cards/{esc(slug)}-{esc(q)}.html">'
            f'<div class=hd><b>{esc(q)}</b><span class=kind>{esc(KIND_LABEL.get(fm.get("kind"), "?"))}</span>{vpill(fm.get("verdict"))}</div>'
            f'<div class=t>{esc(fm.get("title"))}</div>'
            + (f'<div class=nx>→ {esc(fm.get("next_action"))}</div>' if fm.get('next_action') and fm.get('work') != 'closed' else '')
            + f'<div class=ft>{flags}<span>{" · ".join(foot)}</span></div></a>')


def cmd_html(args, cards, pre_issues, root):
    out = xp(args.out) if args.out else root / 'board'
    (out / 'cards').mkdir(parents=True, exist_ok=True)
    by = defaultdict(list)
    for c in cards:
        by[c['slug']].append(c)
    copy_assets(out)
    issues = pre_issues + lint(cards)
    n_err = sum(1 for i in issues if i[0] == 'error')
    n_warn = len(issues) - n_err
    # most recently touched project first
    order = sorted(by, key=lambda s: max(dstr(c['fm'].get('updated')) for c in by[s]), reverse=True)
    tabs, panels = '', ''
    for slug in order:
        cs = by[slug]
        n = {w: sum(1 for c in cs if c['fm'].get('work') == w) for w in WORK}
        rev = sum(1 for c in cs if c['fm'].get('needs_review'))
        live = sum(1 for c in cs for x in [None, *exps(c)] for s in sessions_of(c, x) if state_of(s)[0] == 'live')
        tabs += (f'<button data-s="{esc(slug)}">{esc(slug)}<span class=cnt>{n["active"] + n["waiting"]}</span>'
                 f'{"<span class=\"dot rev\" title=\"검토 필요\"></span>" if rev else ""}'
                 f'{"<span class=\"dot live\" title=\"실행 중 세션\"></span>" if live else ""}</button>')
        last = max((dstr(c['fm'].get('last_verified_at')) for c in cs), default='')
        stats = ''.join(f'<div class=stat><b>{v}</b><span>{k}</span></div>' for k, v in (
            ('진행', n['active']), ('대기', n['waiting']), ('후보', n['candidate']),
            ('검토 필요', rev), ('실행 중 세션', live), ('최근 검증', ago(last) if last else '-')))
        cols = ''
        for w in WORK:
            group = sorted([c for c in cs if c['fm'].get('work') == w], key=lambda c: int(cid(c).split(':Q')[1]))
            inner = ''.join(tile(c) for c in group) or '<div class=empty>없음</div>'
            cols += f'<div class=col><h3><span>{WORK_LABEL[w]}</span><span>{len(group)}</span></h3>{inner}</div>'
        panels += f'<section class=panel id="p-{esc(slug)}"><div class=stats>{stats}</div><div class=board>{cols}</div></section>'
        for c in cs:
            (out / 'cards' / f'{slug}-{cid(c).split(":")[1]}.html').write_text(card_page(c, cards), encoding='utf-8')
    lint_pill = (f'<span class="pill {"bad" if n_err else ("warn" if n_warn else "good")}">lint 오류 {n_err} · 경고 {n_warn}</span>')
    head = (f'<header class=top><div class=in><div class=brand><h1>Research Board</h1>'
            f'<span class=meta>카드 {len(cards)}장 · {today().isoformat()} 생성</span>{lint_pill}</div>'
            f'<nav class=tabs>{tabs}</nav></div></header>')
    body = head + f'<main>{panels or "<p class=meta>카드 없음</p>"}</main>'
    (out / 'index.html').write_text(page('Research Board', body, TABS_JS if panels else ''), encoding='utf-8')
    print(f'wrote {out}/index.html and {len(cards)} card page(s)')


def cmd_serve(args, root):
    """Serve the board over localhost HTTP, regenerating the HTML from the cards on every page load.

    Needed for Orca's embedded browser: it blocks navigation that a file:// page starts itself
    (link clicks, location changes), so card links on a file:// board do nothing.
    """
    import functools
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    out = xp(args.out) if args.out else root / 'board'

    def rebuild():
        _CACHE.clear()  # session liveness must be re-read on every rebuild
        cards, pre = load_all(root, args.project)
        cmd_html(argparse.Namespace(out=str(out)), cards, pre, root)

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if path in ('/', '/index.html') or (path.startswith('/cards/') and path.endswith('.html')):
                try:
                    rebuild()
                except Exception as ex:  # keep serving the last good build; report why it is stale
                    print(f'rebuild failed, serving previous build: {ex}', file=sys.stderr)
            if path == '/':
                self.path = '/index.html'
            super().do_GET()

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def log_message(self, *a):
            pass

    # main() sets SIGPIPE to default for `rboard | head`; a server must survive clients that disconnect
    # mid-response (browsers do this routinely), so turn it back into a BrokenPipeError per request.
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    rebuild()
    srv = ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(Handler, directory=str(out)))
    print(f'serving {out} at http://127.0.0.1:{args.port}/ (Ctrl-C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


# ------------------------------------------------------------------ Orca sessions
#
# Linkage rule: an experiment (or card) lists the omp sessions working on it. Liveness is read from
# the OS, not guessed from titles: a running `omp` process holds its main session .jsonl open and
# carries ORCA_TERMINAL_HANDLE in its environment, so file -> process -> Orca terminal is exact.
# Linux /proc only; local host only.

SESSION_RE = re.compile(r'/\.omp/agent/sessions/([^/]+)/(\d{4}-\d\d-\d\dT[\d-]+Z)_([0-9a-f-]{36})\.jsonl$')
_CACHE: dict = {}


def short(p) -> str:
    s, h = str(p), str(Path.home())
    return '~' + s[len(h):] if s.startswith(h + '/') else s


def _argv_session(argv):
    """Session file named by `omp --resume <path|id>` / `-r <v>` / `--resume=<v>`, or None."""
    if not argv or os.path.basename(argv[0]) != 'omp':
        return None
    val = None
    for i, a in enumerate(argv[1:], 1):
        if a in ('--resume', '-r') and i + 1 < len(argv):
            val = argv[i + 1]
        elif a.startswith('--resume='):
            val = a.split('=', 1)[1]
    if not val:
        return None
    try:
        return str(resolve_session_file(val))
    except SystemExit:
        return None


def scan_omp():
    """Local omp processes and the main session file each one is on.

    Evidence, strongest first: an open session .jsonl file descriptor (present once the process has
    written), else the `--resume <path|id>` argument (an idle resumed session has not opened its file
    yet; stale if the user switched session inside the process, which errs toward refusing a resume).
    Returns [{pid, handle, path, id, cwd, via}]; None without /proc.
    """
    if 'scan' in _CACHE:
        return _CACHE['scan']
    if not Path('/proc/self').exists():
        _CACHE['scan'] = None
        return None
    out = []
    for pid in (p for p in os.listdir('/proc') if p.isdigit()):
        try:
            paths = set()
            for fd in os.listdir(f'/proc/{pid}/fd'):
                t = os.readlink(f'/proc/{pid}/fd/{fd}')
                if SESSION_RE.search(t):
                    paths.add(t)
            via = 'fd'
            if not paths:
                argv = [x.decode('utf-8', 'replace') for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
                p = _argv_session(argv)
                if not p:
                    continue
                paths, via = {p}, 'argv'
            env = dict(x.split(b'=', 1) for x in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in x)
            cwd = os.readlink(f'/proc/{pid}/cwd')
        except OSError:
            continue
        h = env.get(b'ORCA_TERMINAL_HANDLE')
        for t in paths:
            out.append(dict(pid=int(pid), handle=h.decode() if h else None, path=t,
                            id=SESSION_RE.search(t).group(3), cwd=cwd, via=via))
    _CACHE['scan'] = out
    return out


def orca_cmd():
    v = os.environ.get('ORCA_CLI_COMMAND')
    if v:
        return shlex.split(v)
    if os.environ.get('ORCA_DEV_REPO_ROOT') and which('orca-dev'):
        return ['orca-dev']
    if which('orca-ide'):
        return ['orca-ide']
    return None  # never fall back to bare `orca`: on Linux that is the GNOME screen reader


def orca(*a):
    """Run the Orca CLI with --json. Returns (ok, parsed_json_or_None, combined_text)."""
    cmd = orca_cmd()
    if not cmd:
        return False, None, 'orca-ide not found'
    r = subprocess.run(cmd + list(a) + ['--json'], capture_output=True)
    out = r.stdout.decode('utf-8', 'replace').replace('\0', '')
    txt = out + r.stderr.decode('utf-8', 'replace').replace('\0', '')
    try:
        data = json.loads(out)
    except ValueError:
        data = None
    return r.returncode == 0 and (data is None or data.get('ok', True) is not False), data, txt


def live_handles():
    if 'handles' in _CACHE:
        return _CACHE['handles']
    ok, data, _ = orca('terminal', 'list')
    hs = None
    if ok and data:
        r = data.get('result', {})
        ts = r.get('terminals', r) if isinstance(r, dict) else r
        hs = {t.get('handle') for t in ts if isinstance(t, dict)}
    _CACHE['handles'] = hs
    return hs


def session_header(path):
    """(id, cwd, current title) from the first records of a session file."""
    title = cwd = sid = None
    try:
        with open(xp(path), encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i > 8:
                    break
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get('type') == 'title' and title is None:
                    title = d.get('title')
                elif d.get('type') == 'session':
                    sid, cwd = d.get('id'), d.get('cwd')
                    title = title or d.get('title')
    except OSError:
        pass
    return sid, cwd, title


def resolve_session_file(token: str) -> Path:
    p = xp(token)
    if p.is_file() and SESSION_RE.search(str(p.resolve())):
        return p.resolve()
    pat = str(xp('~/.omp/agent/sessions')) + f'/*/*_{token}*.jsonl'
    hits = [Path(x) for x in glob.glob(pat) if SESSION_RE.search(x)]
    if len(hits) != 1:
        raise SystemExit(f'session {token!r}: {len(hits)} matches (give a full path or a longer id prefix)')
    return hits[0]


def session_entry(path, cwd=None) -> dict:
    _, hcwd, title = session_header(path)
    return dict(agent='omp', id=SESSION_RE.search(str(path)).group(3), path=short(path),
                cwd=short(hcwd or cwd or ''), title=title or '', linked_at=today())


def here_session():
    scan = scan_omp()
    if scan is None:
        raise SystemExit('--here needs Linux /proc')
    by_pid = defaultdict(list)
    for s in scan:
        by_pid[s['pid']].append(s)
    pid = os.getpid()
    while pid > 1:
        if pid in by_pid:
            return by_pid[pid]
        try:
            pid = int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
    raise SystemExit('no omp ancestor process with an open session file; use --terminal or --session')


def sessions_of(c, e=None):
    return list((e if e is not None else c['fm']).get('sessions') or [])


def state_of(s):
    """(state, scan_hit). live | live-stale-handle | live-outside-orca | resumable | unknown | missing."""
    scan = scan_omp()
    hits = [x for x in scan or [] if x['id'] == str(s.get('id', ''))]
    if hits:
        h = hits[0]
        if not h['handle']:
            return 'live-outside-orca', h
        hs = live_handles()
        if hs is not None and h['handle'] not in hs:
            return 'live-stale-handle', h
        return 'live', h
    p = xp(s['path']) if s.get('path') else None
    if p is not None and p.exists():
        return ('resumable' if scan is not None else 'unknown'), None
    return 'missing', None


def session_lines(c, e):
    label = cid(c) + (f'/{e.get("id")}' if e is not None else '')
    out = []
    for s in sorted(sessions_of(c, e), key=lambda s: dstr(s.get('linked_at')), reverse=True):
        st, hit = state_of(s)
        title = session_header(s['path'])[2] if s.get('path') else None
        where = f' in {hit["handle"]}' if hit and hit.get('handle') else ''
        out.append(f'session {str(s.get("id"))[:8]} [{st}{where}] "{title or s.get("title", "")}" '
                   f'cwd={s.get("cwd")}  -> rboard open {label}')
    return out


def session_summary(c):
    parts = []
    for e in exps(c):
        if e.get('status') in ('running', 'analyzing'):
            for s in sessions_of(c, e):
                parts.append(f'{e.get("id")} {state_of(s)[0]}')
    for s in sessions_of(c):
        parts.append(f'card {state_of(s)[0]}')
    return ('session: ' + ', '.join(parts)) if parts else ''


def cmd_link(args, cards, root):
    c, e, _ = parse_ref(cards, args.ref, args.project)
    if args.unlink:
        with lock(root, c['slug']):
            fresh = parse_card(c['path'], c['slug'])
            tgt = fresh['fm'] if e is None else next(x for x in exps(fresh) if x.get('id') == e.get('id'))
            before = tgt.get('sessions') or []
            keep = [s for s in before if not str(s.get('id')).startswith(args.unlink)]
            if len(keep) == len(before):
                raise SystemExit(f'no linked session with id prefix {args.unlink!r}')
            tgt['sessions'] = keep
            fresh['fm']['updated'] = today()
            write_card(fresh)
        print(f'unlinked {len(before) - len(keep)} session(s) from {args.ref}')
        return 0
    if sum(map(bool, (args.here, args.terminal, args.session))) != 1:
        raise SystemExit('give exactly one of --here, --terminal HANDLE, --session PATH|ID')
    if args.here:
        hits = here_session()
    elif args.terminal:
        hits = [s for s in (scan_omp() or []) if s['handle'] == args.terminal]
        if not hits:
            raise SystemExit(f'no omp process with an open session found for terminal {args.terminal}')
    else:
        hits = [dict(path=str(resolve_session_file(args.session)), cwd=None)]
    if len(hits) != 1:
        raise SystemExit('ambiguous: multiple session files held open; use --session')
    entry = session_entry(hits[0]['path'], hits[0].get('cwd'))
    with lock(root, c['slug']):
        fresh = parse_card(c['path'], c['slug'])
        tgt = fresh['fm'] if e is None else next(x for x in exps(fresh) if x.get('id') == e.get('id'))
        lst = tgt.setdefault('sessions', [])
        if any(str(x.get('id')) == entry['id'] for x in lst):
            print(f'already linked: {entry["id"]}')
            return 0
        lst.append(entry)
        fresh['fm']['updated'] = today()
        write_card(fresh)
    print(f'linked session {entry["id"][:8]} "{entry["title"]}" to {args.ref}')
    return 0


def cmd_sessions(args, cards):
    scan = scan_omp()
    if scan is None:
        raise SystemExit('needs Linux /proc')
    linked = defaultdict(list)
    for c in cards:
        for s in sessions_of(c):
            linked[str(s.get('id'))].append(cid(c))
        for e in exps(c):
            for s in sessions_of(c, e):
                linked[str(s.get('id'))].append(f'{cid(c)}/{e.get("id")}')
    hs = live_handles()
    for x in sorted(scan, key=lambda x: (x['cwd'], x['id'])):
        title = session_header(x['path'])[2] or ''
        tag = x['handle'] or '(outside Orca)'
        if x['handle'] and hs is not None and x['handle'] not in hs:
            tag += ' (stale handle)'
        if x.get('via') == 'argv':
            tag += ' [idle: matched by --resume argument]'
        print(f'{tag}  pid={x["pid"]}  {short(x["cwd"])}  "{title}"  -> ' + (', '.join(linked.get(x['id'], [])) or 'unlinked'))
    return 0


def resume_in_orca(label, s, c, dry, focus):
    p = xp(s['path'])
    cwd = xp(s.get('cwd') or session_header(p)[1] or '')
    if not cwd.is_dir():
        print(f'cannot resume: cwd {cwd} does not exist')
        return 1
    cmd = f'omp --resume {shlex.quote(str(p))}'
    title = f'{label} {c["fm"].get("title", "")}'[:60]
    a = ['terminal', 'create', '--worktree', f'path:{cwd}', '--title', title, '--command', cmd] + (['--focus'] if focus else [])
    print(f'resume: orca {" ".join(shlex.quote(x) for x in a)}')
    if dry:
        return 0
    ok, _, txt = orca(*a)
    if not ok:
        print(f'orca terminal create failed: {txt.strip()[:400]}\nmanual: cd {shlex.quote(str(cwd))} && {cmd}')
        return 1
    for _ in range(40):
        _CACHE.pop('scan', None)
        hit = [x for x in scan_omp() or [] if x['id'] == str(s.get('id')) and x['handle']]
        if hit:
            print(f'resumed in {hit[0]["handle"]} (pid {hit[0]["pid"]})')
            return 0
        time.sleep(0.5)
    print('terminal created but no omp process holds the session yet (still starting, or omp --resume failed); check the tab')
    return 1


def cmd_open(args, cards):
    c, e, _ = parse_ref(cards, args.ref, args.project)
    cand = []
    if e is not None:
        cand = [(f'{cid(c)}/{e.get("id")}', s) for s in sessions_of(c, e)]
    else:
        for x in exps(c):
            if x.get('status') in ('running', 'analyzing'):
                cand += [(f'{cid(c)}/{x.get("id")}', s) for s in sessions_of(c, x)]
        cand += [(cid(c), s) for s in sessions_of(c)]
        if not cand:
            for x in exps(c):
                cand += [(f'{cid(c)}/{x.get("id")}', s) for s in sessions_of(c, x)]
    cand.sort(key=lambda t: dstr(t[1].get('linked_at')), reverse=True)
    if not cand:
        print(f'{args.ref}: no linked session (rboard link {args.ref} --here)')
        return 1
    for i, (lbl, s) in enumerate(cand, 1):
        print(f'  {i}. {lbl} {str(s.get("id"))[:8]} [{state_of(s)[0]}] "{s.get("title", "")}" linked {dstr(s.get("linked_at"))}')
    if not 1 <= args.pick <= len(cand):
        raise SystemExit(f'--pick must be 1..{len(cand)}')
    label, s = cand[args.pick - 1]
    st, hit = state_of(s)
    if st == 'live':
        if args.dry_run:
            print(f'would switch to {hit["handle"]}')
            return 0
        ok, _, txt = orca('terminal', 'switch', '--terminal', hit['handle'])
        print(f'switched to {hit["handle"]}' if ok else f'switch failed: {txt.strip()[:300]}')
        return 0 if ok else 1
    if st == 'live-stale-handle':
        print(f'session is held open by pid {hit["pid"]} but Orca no longer lists {hit["handle"]} (runtime restarted?); '
              'not resuming, to avoid two writers on one session file')
        return 1
    if st == 'live-outside-orca':
        print(f'session is open in pid {hit["pid"]} outside Orca (cwd {hit["cwd"]}); '
              'not resuming, to avoid two writers on one session file')
        return 1
    if st == 'missing':
        print(f'session file missing: {s.get("path")}')
        return 1
    if st == 'unknown' and not args.dry_run:
        print('cannot verify the session is not already open (no /proc); refusing to resume')
        return 1
    return resume_in_orca(label, s, c, args.dry_run, not args.no_focus)


# ------------------------------------------------------------------ main

def main(argv=None):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `rboard ... | head` must not traceback
    ap = argparse.ArgumentParser(prog='rboard', description=__doc__.splitlines()[0])
    ap.add_argument('--root', help='store root (default ~/.research or $RBOARD_ROOT)')
    ap.add_argument('-p', '--project', help='limit to one project slug')
    common = argparse.ArgumentParser(add_help=False)  # --root/-p also valid after the subcommand
    common.add_argument('--root', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument('-p', '--project', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest='cmd')

    def add(name, **kw):
        return sub.add_parser(name, parents=[common], **kw)

    b = add('board', help='text board (default)')
    b.add_argument('--closed', action='store_true')
    s = add('show', help='one card, resume view')
    s.add_argument('ref')
    c = add('compare', help='compare experiments (card id = all its experiments)')
    c.add_argument('refs', nargs='+')
    c.add_argument('--html')
    r = add('refresh', help='recompute metrics and source hashes (dry run unless --accept)')
    r.add_argument('ref', nargs='?')
    r.add_argument('--accept', action='store_true')
    add('lint', help='schema errors and state warnings')
    lk = add('link', help='link the Orca/omp session working on a card or experiment')
    lk.add_argument('ref', help='slug:Qn or slug:Qn/En')
    lk.add_argument('--here', action='store_true', help='the omp session running this command')
    lk.add_argument('--terminal', help='Orca terminal handle of the session')
    lk.add_argument('--session', help='session file path or id prefix')
    lk.add_argument('--unlink', metavar='ID', help='remove the link to the session with this id prefix')
    op = add('open', help='switch to the linked session in Orca, or resume it there')
    op.add_argument('ref')
    op.add_argument('--pick', type=int, default=1, help='1 = newest linked session')
    op.add_argument('--dry-run', action='store_true')
    op.add_argument('--no-focus', action='store_true')
    add('sessions', help='live omp sessions in Orca and their card links')
    h = add('html', help='static HTML board + card pages')
    h.add_argument('-o', '--out')
    sv = add('serve', help='serve the board on localhost, rebuilt on every page load (needed for Orca links)')
    sv.add_argument('-o', '--out')
    sv.add_argument('--port', type=int, default=8765)
    rd = add('render', help='run a plot recipe: slug:Qn/En/pn')
    rd.add_argument('ref')
    args = ap.parse_args(argv)
    if args.cmd is None:
        args.cmd, args.closed = 'board', False
    root = store_root(args)
    cards, pre = load_all(root, args.project)
    if args.cmd == 'board':
        cmd_board(args, cards)
    elif args.cmd == 'show':
        cmd_show(args, cards)
    elif args.cmd == 'compare':
        cmd_compare(args, cards)
    elif args.cmd == 'refresh':
        cmd_refresh(args, cards, root)
    elif args.cmd == 'lint':
        return cmd_lint(args, cards, pre)
    elif args.cmd == 'html':
        cmd_html(args, cards, pre, root)
    elif args.cmd == 'serve':
        return cmd_serve(args, root)
    elif args.cmd == 'render':
        return cmd_render(args, cards, root)
    elif args.cmd == 'link':
        return cmd_link(args, cards, root)
    elif args.cmd == 'open':
        return cmd_open(args, cards)
    elif args.cmd == 'sessions':
        return cmd_sessions(args, cards)
    return 0


if __name__ == '__main__':
    sys.exit(main())
