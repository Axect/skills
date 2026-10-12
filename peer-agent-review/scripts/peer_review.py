#!/usr/bin/env python3
"""Ask another AI agent to review or discuss a brief, and collect its answer.

Two transports:
  session  a live agent session in an Orca terminal (omp, Claude Code or Codex TUI).
           A one-line pointer to the brief file is typed into the terminal, delivery is
           verified in the agent's session store, and the answer is read from that store.
           If no live reviewer exists in the worktree, one is launched in a new Orca terminal
           (the target's `launch` command) and kept running, so later briefs go to the same
           session and the discussion can continue until agreement. The handle is remembered in
           ~/.cache/peer-agent-review/reviewers.json per (worktree, target).
  oneshot  a headless CLI call (omp -p, codex exec, claude -p) with the brief on stdin. Used only
           with --oneshot: a one-shot reviewer forgets everything after one answer.

Targets come from built-in defaults merged with an optional JSON file
($PEER_REVIEW_TARGETS, default ~/.config/peer-agent-review/targets.json). The default
target is "astra": the live omp session in the current worktree whose model matches /astra/.

Commands
  targets                      list targets and what each resolves to here (never launches)
  resolve  [-t T]              show the terminal handle and session file for a target
  spawn    [-t T] [--thinking L]   launch (or reuse) the permanent reviewer and print its handle
  close    [-t T]              close the reviewer terminal and forget it
  send     [-t T] --brief F --marker M [--mode accept|discuss|free] [--note TEXT]
  wait     [-t T] --marker M [--out FILE] [--timeout S]
  ask      [-t T] --brief F --marker M [...]       send, then wait (session or oneshot)
  read     [-t T] --marker M                       print an answer that already exists

Exit codes: 0 ok, 2 resolution failure, 3 delivery failure, 4 timeout, 5 composer busy.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
ORCA = os.environ.get('ORCA_CLI', 'orca-ide')
CONFIG = Path(os.environ.get('PEER_REVIEW_TARGETS', HOME / '.config/peer-agent-review/targets.json'))
DEFAULT_TARGET = os.environ.get('PEER_REVIEW_DEFAULT', 'astra')

# Busy markers that appear in the terminal tail while an agent is still working.
BUSY = {
    'omp': ['Working', '⟨esc⟩', 'Completing'],
    'claude': ['esc to interrupt'],
    'codex': ['esc to interrupt', 'Working'],
}

# `launch` starts the permanent reviewer in an Orca terminal (thinking level from --thinking or
# the target's `thinking`); `oneshot` is the headless fallback used only with --oneshot.
BUILTIN_TARGETS = {
    'astra': {'transport': 'session', 'agent': 'omp', 'model': r'astra', 'thinking': 'medium',
              'launch': ['omp', '--model', 'gpt-6-astra'],
              'oneshot': ['omp', '-p', '--no-session', '--model', 'gpt-6-astra']},
    'sol': {'transport': 'session', 'agent': 'omp', 'model': r'\bsol\b|-sol', 'thinking': 'medium',
            'launch': ['omp', '--model', 'sol'],
            'oneshot': ['omp', '-p', '--no-session', '--model', 'sol']},
    'luna': {'transport': 'session', 'agent': 'omp', 'model': r'luna', 'thinking': 'medium',
             'launch': ['omp', '--model', 'luna']},
    'opus': {'transport': 'session', 'agent': 'omp', 'model': r'opus', 'thinking': 'medium',
             'launch': ['omp', '--model', 'opus']},
    'codex': {'transport': 'session', 'agent': 'codex', 'launch': ['codex', '-s', 'read-only'],
              'oneshot': ['codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-']},
    'claude': {'transport': 'session', 'agent': 'claude', 'launch': ['claude', '--permission-mode', 'plan'],
               'oneshot': ['claude', '-p', '--permission-mode', 'plan']},
}
REGISTRY = HOME / '.cache/peer-agent-review/reviewers.json'


MODE_SUFFIX = {
    'accept': "첫 줄에 '수락' 또는 '수정 필요'를 쓰고, 필수 수정은 대안 문장으로 줘. 파일은 수정하지 마.",
    'discuss': "수락 판정이 아니라 쟁점별 판단·이유·반론과 네가 생각하는 최선안을 줘. 파일은 수정하지 마.",
    'free': "파일은 수정하지 마.",
}


def load_targets() -> dict:
    targets = {k: dict(v) for k, v in BUILTIN_TARGETS.items()}
    if CONFIG.exists():
        for name, spec in json.loads(CONFIG.read_text()).items():
            targets.setdefault(name, {}).update(spec)
    return targets


def target_spec(name: str) -> dict:
    targets = load_targets()
    if name in targets:
        return {'name': name, **targets[name]}
    # Unknown name: treat it as a model regex for a live omp session.
    return {'name': name, 'transport': 'session', 'agent': 'omp', 'model': name}


# ---------------------------------------------------------------- orca helpers
def orca(*args: str) -> dict:
    """Run the Orca CLI with --json; parse defensively (TUI glyphs can break UTF-8)."""
    out = subprocess.run([ORCA, *args, '--json'], capture_output=True)
    text = out.stdout.decode('utf-8', 'replace').replace('\x00', '')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'ok': False, 'error': {'code': 'unparsable', 'message': text[:400]}}


def terminals() -> list[dict]:
    d = orca('terminal', 'list')
    return d.get('result', {}).get('terminals', []) if d.get('ok', True) else []


def terminal_tail(handle: str, limit: int = 25) -> str:
    d = orca('terminal', 'read', '--terminal', handle, '--limit', str(limit))
    return '\n'.join(d.get('result', {}).get('terminal', {}).get('tail', []))


# ---------------------------------------------------------------- permanent reviewers
def registry() -> dict:
    try:
        return json.loads(REGISTRY.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def remember(cwd: str, target: str, handle: str | None) -> None:
    reg = registry()
    key = f'{cwd}::{target}'
    if handle:
        reg[key] = handle
    else:
        reg.pop(key, None)
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=1))


def launch_command(spec: dict, thinking: str | None) -> str:
    cmd = list(spec.get('launch') or [])
    if not cmd:
        raise SystemExit(f"spawn: target '{spec['name']}' has no launch command; add 'launch' in the targets file")
    level = thinking or spec.get('thinking')
    if level and spec.get('agent', 'omp') == 'omp':
        cmd += ['--thinking', level]
    elif level and spec.get('agent') == 'codex':
        cmd += ['-c', f'model_reasoning_effort="{level}"']
    return ' '.join(cmd if all(re.fullmatch(r'[\w@%+=:,./-]+', c) for c in cmd)
                    else [json.dumps(c) for c in cmd])


def spawn(spec: dict, cwd: str, thinking: str | None) -> str:
    """Launch the target's agent in a new Orca terminal of this worktree and wait until its TUI is ready."""
    terms = terminals()
    wt = next((t.get('worktreeId') for t in terms
               if os.path.realpath(t.get('worktreePath', '')) == os.path.realpath(cwd) and t.get('worktreeId')), None)
    if not wt:
        raise SystemExit(f'spawn: no Orca worktree found for {cwd}; open it in Orca first')
    r = orca('terminal', 'create', '--worktree', f'id:{wt}', '--title', f"{spec['name']} reviewer",
             '--command', launch_command(spec, thinking))
    handle = r.get('result', {}).get('terminal', {}).get('handle')
    if not r.get('ok', False) or not handle:
        raise SystemExit(f"spawn: terminal create failed: {r.get('error')}")
    w = orca('terminal', 'wait', '--terminal', handle, '--for', 'tui-idle', '--timeout-ms', '120000')
    if not w.get('result', {}).get('wait', {}).get('satisfied'):
        w = orca('terminal', 'wait', '--terminal', handle, '--for', 'tui-idle', '--timeout-ms', '240000')
        if not w.get('result', {}).get('wait', {}).get('satisfied'):
            raise SystemExit(f'spawn: {handle} did not become ready; check the terminal before sending')
    remember(cwd, spec['name'], handle)
    print(f"spawn: launched {spec['name']} reviewer in {handle}", file=sys.stderr)
    return handle


# ---------------------------------------------------------------- session stores
def omp_store(cwd: str) -> Path:
    rel = os.path.relpath(cwd, HOME)
    return HOME / '.omp/agent/sessions' / ('-' + rel.replace('/', '-'))


def store_files(agent: str, cwd: str) -> list[Path]:
    if agent == 'omp':
        d = omp_store(cwd)
        files = list(d.glob('*.jsonl')) if d.is_dir() else []
    elif agent == 'claude':
        d = HOME / '.claude/projects' / re.sub(r'[^A-Za-z0-9]', '-', cwd)
        files = list(d.glob('*.jsonl')) if d.is_dir() else []
    elif agent == 'codex':
        files = list((HOME / '.codex/sessions').rglob('rollout-*.jsonl'))
    else:
        files = []
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def records(path: Path):
    """Yield (role, text) for user/assistant records across omp, Claude Code and Codex formats."""
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = d.get('message') if isinstance(d.get('message'), dict) else None
            if msg is None and isinstance(d.get('payload'), dict) and d['payload'].get('type') == 'message':
                msg = d['payload']                     # Codex rollout
            if msg is None:
                continue
            role = msg.get('role')
            if role not in ('user', 'assistant'):
                continue
            c = msg.get('content')
            if isinstance(c, list):
                text = ''.join(b.get('text', '') for b in c if isinstance(b, dict)
                               and b.get('type') in ('text', 'output_text', 'input_text'))
            else:
                text = c or ''
            yield role, text


def session_title(path: Path) -> str:
    try:
        first = json.loads(path.open(encoding='utf-8').readline())
        return first.get('title', '') if first.get('type') == 'title' else ''
    except Exception:
        return ''


def dominant_model(path: Path) -> str:
    counts: dict[str, int] = {}
    for m in re.findall(r'"model":"([^"]+)"', path.read_text(encoding='utf-8', errors='replace')):
        counts[m] = counts.get(m, 0) + 1
    return max(counts, key=counts.get) if counts else ''


def find_marker_file(agent: str, cwd: str, marker: str) -> Path | None:
    for p in store_files(agent, cwd)[:60]:
        if any(r == 'user' and marker in t for r, t in records(p)):
            return p
    return None


# ---------------------------------------------------------------- resolution
def resolve(spec: dict, cwd: str, handle: str | None = None, launch: bool = False,
            thinking: str | None = None) -> tuple[str, Path | None]:
    """Return (terminal handle, session file) for a session target in this worktree.

    Order: explicit handle, the remembered permanent reviewer (if its terminal still exists), a
    'title' regex, the omp session store; with launch=True a missing reviewer is spawned."""
    self_handle = os.environ.get('ORCA_TERMINAL_HANDLE')   # never review with yourself
    terms = [t for t in terminals() if os.path.realpath(t.get('worktreePath', '')) == os.path.realpath(cwd)
             and t.get('handle') != self_handle]
    if handle:
        return handle, None
    known = registry().get(f"{cwd}::{spec['name']}")
    if known and any(t.get('handle') == known for t in terms):
        return known, None
    try:
        return _resolve_live(spec, cwd, terms)
    except SystemExit:
        if not launch:
            raise
        return spawn(spec, cwd, thinking), None


def _resolve_live(spec: dict, cwd: str, terms: list[dict]) -> tuple[str, Path | None]:
    if spec.get('title'):
        hits = [t for t in terms if re.search(spec['title'], t.get('title') or '')]
        if len(hits) == 1:
            return hits[0]['handle'], None
        raise SystemExit(f"resolve: title /{spec['title']}/ matched {len(hits)} terminals")
    agent = spec.get('agent', 'omp')
    if agent != 'omp':
        raise SystemExit(f"resolve: agent '{agent}' needs --handle or a 'title' regex in the target spec")
    rx = re.compile(spec['model'], re.I)
    for path in store_files('omp', cwd):
        model = dominant_model(path)
        if not rx.search(model):
            continue
        title = session_title(path)
        # agentIdentity can be empty for a while after an Orca restart; the title match decides.
        hits = [t for t in terms if t.get('agentIdentity') in ('omp', None) and title
                and title in (t.get('title') or '')]
        if len(hits) == 1:
            return hits[0]['handle'], path
    cands = '\n'.join(f"  {t['handle']}  {t.get('title')}" for t in terms)
    raise SystemExit(f"resolve: no live omp terminal in {cwd} whose session model matches "
                     f"/{spec['model']}/. Terminals here:\n{cands}\nUse --handle.")


# ---------------------------------------------------------------- commands
def pointer_line(brief: Path, cwd: str, marker: str, mode: str, note: str | None) -> str:
    try:
        ref = os.path.relpath(brief.resolve(), cwd)
        ref = ref if not ref.startswith('..') else str(brief.resolve())
    except ValueError:
        ref = str(brief.resolve())
    parts = [f"[{marker}]", f"@{ref} 를 읽고 답해줘."]
    if note:
        parts.append(note.replace('\n', ' '))
    parts.append(MODE_SUFFIX[mode])
    return ' '.join(parts)


def composer_busy(tail: str) -> bool:
    """True when the input area holds text (an unsubmitted user draft).

    The omp/Claude/Codex TUIs draw the input area between the last two full-width rule
    lines (────). Boxed tool output (│ … │) higher up in the transcript is not the composer.
    """
    lines = tail.splitlines()
    rules = [i for i, l in enumerate(lines) if l.strip() and set(l.strip()) <= set('─━')]
    if len(rules) < 2:
        return False
    inner = lines[rules[-2] + 1:rules[-1]]
    return any(re.sub(r'[│┃\s>❯›]', '', l) for l in inner)


def cmd_send(a, spec, cwd) -> int:
    handle, _ = resolve(spec, cwd, a.handle, launch=not a.no_launch, thinking=a.thinking)
    brief = Path(a.brief)
    if not brief.exists():
        print(f'send: brief {brief} not found', file=sys.stderr)
        return 3
    if not a.force and composer_busy(terminal_tail(handle)):
        print('send: the target composer holds unsubmitted text; ask the user (or --force)', file=sys.stderr)
        return 5
    line = pointer_line(brief, cwd, a.marker, a.mode, a.note)
    agent = spec.get('agent', 'omp')
    for attempt in range(2):
        r = orca('terminal', 'send', '--terminal', handle, '--text', line, '--enter')
        if not r.get('ok', False):
            code = r.get('error', {}).get('code', '?')
            if code == 'terminal_handle_stale' and attempt == 0:
                remember(cwd, spec['name'], None)
                handle, _ = resolve(spec, cwd, None, launch=not a.no_launch, thinking=a.thinking)
                continue
            print(f'send: orca error {code}', file=sys.stderr)
            return 3
        for _ in range(15):
            time.sleep(2)
            path = find_marker_file(agent, cwd, a.marker)
            if path:
                print(json.dumps({'handle': handle, 'session': str(path), 'marker': a.marker}, ensure_ascii=False))
                return 0
        if attempt == 0 and not a.handle:
            handle, _ = resolve(spec, cwd, None)
    print('send: accepted by Orca but not found in the session store (not delivered)', file=sys.stderr)
    return 3


def answer_after(path: Path, marker: str) -> str:
    recs = list(records(path))
    idx = [i for i, (r, t) in enumerate(recs) if r == 'user' and marker in t]
    if not idx:
        return ''
    return '\n\n'.join(t for r, t in recs[idx[-1] + 1:] if r == 'assistant' and t.strip())


def is_busy(handle: str | None, agent: str) -> bool:
    if not handle:
        return False
    tail = terminal_tail(handle, 15)
    return any(tok in tail for tok in BUSY.get(agent, []))


def cmd_wait(a, spec, cwd) -> int:
    agent = spec.get('agent', 'omp')
    try:
        handle, _ = resolve(spec, cwd, a.handle)
    except SystemExit:
        handle = a.handle
    deadline = time.time() + a.timeout
    path = None
    while time.time() < deadline:
        path = path or find_marker_file(agent, cwd, a.marker)
        if path:
            ans = answer_after(path, a.marker)
            if ans and not is_busy(handle, agent):
                m0 = path.stat().st_mtime
                time.sleep(a.settle)
                if not is_busy(handle, agent) and path.stat().st_mtime == m0:
                    ans = answer_after(path, a.marker)
                    emit(ans, a.out)
                    return 0
        time.sleep(a.poll)
    print('wait: timeout', file=sys.stderr)
    return 4


def emit(text: str, out: str | None) -> None:
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text)
    print(text)


def cmd_oneshot(a, spec, cwd) -> int:
    cmd = spec.get('oneshot')
    if not cmd:
        print(f"oneshot: target '{spec['name']}' has no oneshot command", file=sys.stderr)
        return 2
    brief = Path(a.brief).read_text()
    prompt = f"[{a.marker}]\n{brief}\n\n{MODE_SUFFIX[a.mode]}"
    if a.note:
        prompt += '\n' + a.note
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd, timeout=a.timeout)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        return 3
    emit(r.stdout.strip(), a.out)
    return 0


def cmd_targets(a, cwd) -> int:
    for name, spec in load_targets().items():
        where = ''
        if spec.get('transport') == 'session':
            try:
                h, p = resolve({'name': name, **spec}, cwd)
                where = f'{h}  {p.name if p else ""}'
            except SystemExit:
                where = '(no live session here)'
        print(f"{name:8s} {spec.get('transport'):8s} {spec.get('agent', ''):7s} {where}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['targets', 'resolve', 'spawn', 'close', 'send', 'wait', 'ask', 'read'])
    ap.add_argument('-t', '--target', default=DEFAULT_TARGET)
    ap.add_argument('--handle', help='explicit Orca terminal handle (skips resolution)')
    ap.add_argument('--cwd', default=os.getcwd(), help='worktree of the target session (default: here)')
    ap.add_argument('--brief')
    ap.add_argument('--marker', help='unique tag, e.g. "sec3 KO v2 check" (brackets optional)')
    ap.add_argument('--mode', choices=list(MODE_SUFFIX), default='accept')
    ap.add_argument('--note', help='one extra sentence appended to the pointer line')
    ap.add_argument('--out', help='also write the answer to this file')
    ap.add_argument('--timeout', type=float, default=3600)
    ap.add_argument('--poll', type=float, default=30)
    ap.add_argument('--settle', type=float, default=20)
    ap.add_argument('--oneshot', action='store_true', help='force the headless transport (no memory)')
    ap.add_argument('--no-launch', action='store_true', help='fail instead of launching a missing reviewer')
    ap.add_argument('--thinking', help='thinking level for a newly launched reviewer (default: target spec)')
    ap.add_argument('--force', action='store_true', help='send even if the composer holds text')
    a = ap.parse_args()
    cwd = os.path.realpath(a.cwd)
    if a.marker:
        a.marker = a.marker.strip('[]')
    if a.command == 'targets':
        return cmd_targets(a, cwd)
    spec = target_spec(a.target)
    if a.command == 'spawn':
        h, _ = resolve(spec, cwd, a.handle, launch=True, thinking=a.thinking)
        print(json.dumps({'target': spec['name'], 'handle': h}, ensure_ascii=False))
        return 0
    if a.command == 'close':
        h = a.handle or registry().get(f"{cwd}::{spec['name']}")
        if not h:
            print('close: no remembered reviewer here', file=sys.stderr)
            return 2
        orca('terminal', 'close', '--terminal', h)
        remember(cwd, spec['name'], None)
        print(json.dumps({'closed': h}))
        return 0
    if a.command == 'resolve':
        h, p = resolve(spec, cwd, a.handle)
        print(json.dumps({'target': spec['name'], 'handle': h, 'session': str(p) if p else None}, ensure_ascii=False))
        return 0
    if a.command in ('send', 'ask') and not (a.brief and a.marker):
        ap.error('--brief and --marker are required')
    if a.command in ('wait', 'read') and not a.marker:
        ap.error('--marker is required')
    oneshot = a.oneshot or spec.get('transport') == 'oneshot'
    if a.command == 'read':
        path = find_marker_file(spec.get('agent', 'omp'), cwd, a.marker)
        ans = answer_after(path, a.marker) if path else ''
        if not ans:
            print('read: no answer yet', file=sys.stderr)
            return 4
        emit(ans, a.out)
        return 0
    if a.command == 'send':
        return cmd_send(a, spec, cwd)
    if a.command == 'wait':
        return cmd_wait(a, spec, cwd)
    if oneshot:
        return cmd_oneshot(a, spec, cwd)
    rc = cmd_send(a, spec, cwd)
    return rc if rc else cmd_wait(a, spec, cwd)


if __name__ == '__main__':
    sys.exit(main())
