#!/usr/bin/env python3
"""magi.py: route a brief to the proposer (Argon) or the critic (Astra) inside Orca.

  magi.py propose  --brief F --marker M [--out FILE] [--thinking L]
      Argon through agy, peer-agent-review mode `propose` (non-hostile, mockups allowed in the
      folder the brief names).
  magi.py critique --brief F --marker M [--mode accept|discuss] [--out FILE] [--thinking L]
      Astra through omp (GPT-6-Astra). Falls back to a Codex session (read-only) when omp is
      not installed or the Astra session cannot be resolved, launched, or reached.
  magi.py both     --brief F --marker M [--out-dir DIR]
      Same brief to both at once: Argon `propose`, critic `discuss`. Prints both answers.

Requires Orca: both reviewers run as permanent sessions in Orca terminals of the current
worktree, reached with the Orca CLI (`orca-ide`, override with ORCA_CLI). Transport is
peer-agent-review's `peer_review.py` (override its path with PEER_REVIEW).
Exit codes: as peer_review.py (2 resolution, 3 not delivered, 4 timeout, 5 composer busy);
6 Orca CLI missing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
PEER = Path(os.environ.get('PEER_REVIEW', HERE.parent.parent / 'peer-agent-review/scripts/peer_review.py'))
ORCA = os.environ.get('ORCA_CLI', 'orca-ide')
FALLBACK_CODES = {2, 3}  # resolution failure, not delivered: the critic is unreachable
# Argon runs agy with tool permissions auto-approved so it can build mockups unattended.
# MAGI_ARGON_SAFE=1 keeps peer-agent-review's default launch (accept-edits, prompts on tools).
ARGON_LAUNCH = ['agy', '--model', 'gemini-4-argon-{level}', '--mode', 'accept-edits',
                '--dangerously-skip-permissions']


def argon_env() -> dict:
    """Environment whose PEER_REVIEW_TARGETS adds the skip-permissions flag to the argon launch."""
    env = dict(os.environ)
    if env.get('MAGI_ARGON_SAFE') == '1':
        return env
    base = Path(env.get('PEER_REVIEW_TARGETS', Path.home() / '.config/peer-agent-review/targets.json'))
    targets = json.loads(base.read_text()) if base.exists() else {}
    targets.setdefault('argon', {})['launch'] = ARGON_LAUNCH
    path = Path.home() / '.cache/magi-research/targets.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(targets, ensure_ascii=False, indent=1))
    env['PEER_REVIEW_TARGETS'] = str(path)
    return env


def run(target: str, mode: str, a, out: str | None) -> int:
    cmd = [sys.executable, str(PEER), 'ask', '-t', target, '--mode', mode,
           '--brief', a.brief, '--marker', a.marker if target != 'codex' else f'{a.marker} (codex)']
    if a.thinking and target != 'codex':
        cmd += ['--thinking', a.thinking]
    if out:
        cmd += ['--out', out]
    print(f'[magi] {target} ({mode}): {a.marker}', file=sys.stderr)
    return subprocess.run(cmd, env=argon_env() if target == 'argon' else None).returncode


def critique(a, mode: str, out: str | None) -> int:
    if shutil.which('omp'):
        rc = run('astra', mode, a, out)
        if rc not in FALLBACK_CODES:
            return rc
        print(f'[magi] Astra unreachable (exit {rc}); falling back to Codex', file=sys.stderr)
    else:
        print('[magi] omp not found; critic falls back to Codex', file=sys.stderr)
    if not shutil.which('codex'):
        print('[magi] codex not found either; no critic available', file=sys.stderr)
        return 2
    return run('codex', mode, a, out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('role', choices=['propose', 'critique', 'both'])
    ap.add_argument('--brief', required=True)
    ap.add_argument('--marker', required=True, help='unique per request')
    ap.add_argument('--mode', choices=['accept', 'discuss'], default='accept', help='critic mode')
    ap.add_argument('--thinking', help='reasoning level passed to the launched session')
    ap.add_argument('--out', help='also write the answer to this file')
    ap.add_argument('--out-dir', help='for `both`: write argon.md and critic.md here')
    a = ap.parse_args()
    if not shutil.which(ORCA):
        print(f'[magi] Orca CLI `{ORCA}` not found: magi-research runs inside Orca only', file=sys.stderr)
        return 6
    if not PEER.exists():
        print(f'[magi] peer_review.py not found at {PEER} (set PEER_REVIEW)', file=sys.stderr)
        return 2
    if a.role == 'propose':
        return run('argon', 'propose', a, a.out)
    if a.role == 'critique':
        return critique(a, a.mode, a.out)
    outs = {}
    if a.out_dir:
        Path(a.out_dir).mkdir(parents=True, exist_ok=True)
        outs = {k: str(Path(a.out_dir) / f'{k}.md') for k in ('argon', 'critic')}
    rcs = {}
    t = threading.Thread(target=lambda: rcs.__setitem__('argon', run('argon', 'propose', a, outs.get('argon'))))
    t.start()
    rcs['critic'] = critique(a, 'discuss', outs.get('critic'))
    t.join()
    print(f'[magi] exit codes: {rcs}', file=sys.stderr)
    return max(rcs.values())


if __name__ == '__main__':
    sys.exit(main())
