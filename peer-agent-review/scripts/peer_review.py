#!/usr/bin/env python3
"""Ask another AI agent to review or discuss a brief, and collect its answer.

Two transports:
  session  a live agent session in an adash terminal (a window of adash's private tmux server,
           reached with `adash term`): omp, Claude Code, Codex or Antigravity TUI.
           A one-line pointer to the brief file is typed into the terminal, delivery is
           verified in the agent's session store, and the answer is read from that store.
           A live reviewer already running in the worktree is reused (found by its remembered handle,
           or through `adash ls --all --json`, which names the agent kind, model and session of every
           live terminal); only if none exists is one launched in a new terminal opened in the worktree
           directory (`adash term new --cwd`, the target's `launch` command) and kept running, so later
           briefs go to the same session and the discussion can continue until agreement. Terminal
           handles (`t_…`) are stable, also across a tmux restart, and are remembered in
           ~/.cache/peer-agent-review/reviewers.json per (worktree, target).
  oneshot  a headless CLI call (omp -p, codex exec, claude -p) with the brief on stdin. Used only
           with --oneshot: a one-shot reviewer forgets everything after one answer.

Turn completion (omp, Claude Code, Codex) is read from the reviewer's own session record: the file
in its session store (omp: ~/.omp/agent/sessions/<cwd-slug>/) that holds the user record with
[marker]. The turn is done when, after that record, the last message is an assistant message that
ends the turn (omp stopReason stop/length, Claude stop_reason end_turn or a turn_duration record,
Codex task_complete) rather than one with a pending tool call, and the file is unchanged SETTLE (3)
seconds later (a finished background job can resume the turn). A turn that ended in error or abort
must stay unchanged for --settle seconds (omp retries provider errors). The session record is written
by the agent itself, so this needs neither busy tokens on the screen nor a quiet period; adash's own
`ls` state is derived from the same records but costs a full collection per read.

Agents without a readable session store (Antigravity `agy`, target "argon") use the session
transport with a file answer: the pointer line asks the reviewer to write its whole answer to
~/.cache/peer-agent-review/answers/<target>/<marker>.md, delivery is checked on the terminal
screen, and the answer is complete when that file is non-empty, unchanged for --settle seconds
and the agent is not working (adash state of the handle, else no busy token on the screen).

Targets come from built-in defaults merged with an optional JSON file
($PEER_REVIEW_TARGETS, default ~/.config/peer-agent-review/targets.json). The default
target is "astra": the live omp session in the current worktree whose model matches /astra/.

Commands
  targets                      list targets and what each resolves to here (never launches)
  resolve  [-t T]              show the terminal handle and session file for a target
  spawn    [-t T] [--thinking L]   launch (or reuse) the permanent reviewer and print its handle
  close    [-t T]              close the reviewer terminal and forget it
  send     [-t T] --brief F --marker M [--mode accept|discuss|free|propose] [--note TEXT]
  wait     [-t T] --marker M [--out FILE] [--timeout S]
  ask      [-t T] --brief F --marker M [...]       send, then wait (session or oneshot)
  read     [-t T] --marker M                       print an answer that already exists

Exit codes: 0 ok, 2 resolution failure, 3 delivery failure, 4 timeout, 5 composer busy.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
CONFIG = Path(os.environ.get('PEER_REVIEW_TARGETS', HOME / '.config/peer-agent-review/targets.json'))
DEFAULT_TARGET = os.environ.get('PEER_REVIEW_DEFAULT', 'astra')

# Busy markers that appear on the terminal screen while an agent is still working.
BUSY = {
    'omp': ['Working', '⟨esc⟩', 'Completing'],
    'claude': ['esc to interrupt'],
    'codex': ['esc to interrupt', 'Working'],
    'agy': ['esc to', 'Thinking', 'Working'],
}
# Agents whose answer is collected from a file the reviewer writes (no readable session store).
FILE_ANSWER_AGENTS = {'agy'}
ANSWERS = HOME / '.cache/peer-agent-review/answers'

# `launch` starts the permanent reviewer in an adash terminal (thinking level from --thinking or
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
    # 'opus' alone also matches google-antigravity/claude-opus-*, which omp may pick and which
    # bills Antigravity's shared Claude & GPT quota: pin the Anthropic provider
    'opus': {'transport': 'session', 'agent': 'omp', 'model': r'^(?!google-antigravity/).*opus', 'thinking': 'medium',
             'launch': ['omp', '--model', 'anthropic/claude-opus-5-5']},
    'codex': {'transport': 'session', 'agent': 'codex', 'launch': ['codex', '-s', 'read-only'],
              'oneshot': ['codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-']},
    'claude': {'transport': 'session', 'agent': 'claude', 'launch': ['claude', '--permission-mode', 'plan'],
               'oneshot': ['claude', '-p', '--permission-mode', 'plan']},
    # Antigravity CLI; '{level}' in launch is replaced by the thinking level (low|medium|high).
    'argon': {'transport': 'session', 'agent': 'agy', 'thinking': 'medium',
              'launch': ['agy', '--model', 'gemini-4-argon-{level}', '--mode', 'accept-edits']},
}
REGISTRY = HOME / '.cache/peer-agent-review/reviewers.json'
POLL = 2           # seconds between session-record reads while waiting (re-parsed only when the file changed)
SETTLE = 3         # a finished turn must stay finished this long (a background job can resume the turn)
READY_TIMEOUT = 360  # seconds a newly launched reviewer may take to draw its TUI
# adash's agentType (`adash ls --json`) for each agent kind of a target.
AGENT_KIND = {'omp': 'omp', 'agy': 'antigravity', 'claude': 'claude', 'codex': 'codex'}
# Turn-ending stop reasons: omp stopReason, Claude stop_reason.
DONE_STOPS = {'stop', 'length', 'end_turn', 'stop_sequence', 'max_tokens', 'refusal'}
FAILED_STOPS = {'error', 'aborted'}


# Default stance: hostile. The reviewer looks for reasons to reject, not to approve.
HOSTILE = ("적대적(hostile) 검토자로서 이 결과물을 거절할 이유를 찾는 가장 비판적인 심사자처럼 읽어줘. "
           "근거 없는 주장, 과장, 논리 비약, 출처·수치 오류, 빠진 반례를 원문 인용과 함께 지적하고, "
           "결정을 바꾸지 않는 칭찬은 하지 마.")
MODE_SUFFIX = {
    'accept': HOSTILE + " 첫 줄에 '수락' 또는 '수정 필요'를 쓰고, 필수 수정은 대안 문장으로 줘. 파일은 수정하지 마.",
    'discuss': HOSTILE + " 수락 판정이 아니라 쟁점별 판단·이유·반론과 네가 생각하는 최선안을 줘. 파일은 수정하지 마.",
    'free': HOSTILE + " 파일은 수정하지 마.",
    # Generative stance for a proposer (magi-research uses it for Argon). Not hostile.
    'propose': ("제안자로서 읽어줘. 기존 형태나 현재 안에 얽매이지 말고 서로 다른 대안 2~3개를 구체 사양, "
                "독자에게 요구하는 사전 지식, 장단점, 위험과 함께 제안하고 하나를 추천해. 시안(그림·스크립트)은 "
                "브리프가 지정한 폴더에만 만들고, 사실·수치는 파일에서 확인한 것만 써. 파일은 수정하지 마."),
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


# ---------------------------------------------------------------- adash terminals
def adash_exe() -> str:
    exe = shutil.which('adash')
    if not exe:
        raise SystemExit('adash not found on PATH: the session transport needs `adash term`')
    return exe


def term(*args: str) -> tuple[int, object, str]:
    """Run `adash term …`: (exit code, parsed JSON stdout or None, stderr). Output is decoded defensively
    (TUI glyphs on a screen can break UTF-8)."""
    out = subprocess.run([adash_exe(), 'term', *args], capture_output=True)
    text = out.stdout.decode('utf-8', 'replace').replace('\x00', '')
    try:
        data = json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        data = None
    return out.returncode, data, out.stderr.decode('utf-8', 'replace').strip()


def terminals() -> list[dict]:
    rc, data, _ = term('list')
    return [t for t in data if not t.get('dead')] if rc == 0 and isinstance(data, list) else []


def in_worktree(t: dict, cwd: str) -> bool:
    """The terminal was opened in this worktree directory."""
    return os.path.realpath(t.get('cwd') or t.get('currentPath') or '') == os.path.realpath(cwd)


def terminal_tail(handle: str, limit: int = 25, screen: bool = False) -> str:
    """Rendered screen (screen=True; for a TUI it includes the live input box) or the last `limit` lines
    including scrollback."""
    rc, data, _ = term('read', handle) if screen else term('read', handle, '--lines', str(limit))
    return '\n'.join(data.get('lines', [])) if rc == 0 and isinstance(data, dict) else ''


def live_agents() -> dict[str, dict] | None:
    """adash's live agents by terminal handle (agentType, model, state, identity), or None when
    `adash ls` fails. One call is a full collection (~1 s), so it is not used in tight loops."""
    try:
        out = subprocess.run([adash_exe(), 'ls', '--all', '--json'], capture_output=True, timeout=60)
        st = json.loads(out.stdout.decode('utf-8', 'replace'))
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None
    if out.returncode != 0 or not isinstance(st, dict):
        return None
    return {a['handle']: a for a in st.get('agents', []) if isinstance(a, dict) and a.get('handle')}


# ---------------------------------------------------------------- permanent reviewers
def registry() -> dict:
    try:
        return json.loads(REGISTRY.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def remembered(cwd: str, target: str) -> str | None:
    """Handle of the permanent reviewer."""
    v = registry().get(f'{cwd}::{target}')
    return v if isinstance(v, str) else None


def remember(cwd: str, target: str, handle: str | None) -> None:
    reg = registry()
    key = f'{cwd}::{target}'
    if handle:
        reg[key] = handle
    else:
        reg.pop(key, None)
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=1))


def kind_ok(spec: dict, agent: dict | None) -> bool:
    """adash sees the target's agent kind running in the terminal."""
    return bool(agent) and agent.get('agentType') == AGENT_KIND.get(spec.get('agent', 'omp'))


def launch_command(spec: dict, thinking: str | None) -> str:
    cmd = list(spec.get('launch') or [])
    if not cmd:
        raise SystemExit(f"spawn: target '{spec['name']}' has no launch command; add 'launch' in the targets file")
    level = thinking or spec.get('thinking')
    if any('{level}' in c for c in cmd):
        cmd = [c.replace('{level}', level or 'medium') for c in cmd]
    elif level and spec.get('agent', 'omp') == 'omp':
        cmd += ['--thinking', level]
    elif level and spec.get('agent') == 'codex':
        cmd += ['-c', f'model_reasoning_effort="{level}"']
    return ' '.join(cmd if all(re.fullmatch(r'[\w@%+=:,./-]+', c) for c in cmd)
                    else [json.dumps(c) for c in cmd])


def file_answer(spec: dict) -> bool:
    return spec.get('agent', 'omp') in FILE_ANSWER_AGENTS


def answer_path(spec: dict, marker: str) -> Path:
    slug = re.sub(r'[^\w.-]+', '_', marker).strip('_') or 'answer'
    return ANSWERS / spec['name'] / f'{slug}.md'


def tui_ready(screen: str, agent: str) -> bool:
    """The TUI has drawn its input area: omp and agy draw full-width rule lines around it. Claude and
    Codex are taken as ready once their screen is quiet."""
    if agent not in ('omp', 'agy'):
        return bool(screen.strip())
    return any(l.strip() and set(l.strip()) <= set('─━') for l in screen.splitlines())


def spawn(spec: dict, cwd: str, thinking: str | None) -> str:
    """Launch the target's agent in a new adash terminal in this worktree and wait until its TUI is ready
    (screen quiet for 2 s and the input area drawn); a prompt typed into a TUI that is still starting is lost."""
    rc, data, err = term('new', '--cwd', cwd, '--title', f"{spec['name']} reviewer",
                         '--command', launch_command(spec, thinking))
    handle = data.get('handle') if rc == 0 and isinstance(data, dict) else None
    if not handle:
        raise SystemExit(f'spawn: adash term new failed: {err or data}')
    agent = spec.get('agent', 'omp')
    deadline = time.time() + READY_TIMEOUT
    while True:
        left = int((deadline - time.time()) * 1000)
        if left <= 0:
            raise SystemExit(f'spawn: {handle} did not become ready; check the terminal before sending')
        term('wait', handle, '--quiet-ms', '2000', '--timeout-ms', str(left))
        if tui_ready(terminal_tail(handle, screen=True), agent):
            break
        if not any(t.get('handle') == handle for t in terminals()):
            raise SystemExit(f'spawn: terminal {handle} closed while starting `{launch_command(spec, thinking)}`')
        time.sleep(1)
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


def entries(path: Path):
    """Yield (role, text, stop) across omp, Claude Code and Codex session records.

    role is the message role (user, assistant, toolResult, …) with stop its stop reason, or 'end' for a
    turn-end record (Claude turn_duration, Codex task_complete / turn_aborted) with stop 'stop' or
    'aborted', or 'start' for a Codex task_started record."""
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get('type') == 'system' and d.get('subtype') == 'turn_duration':
                yield 'end', '', 'stop'
                continue
            payload = d.get('payload') if isinstance(d.get('payload'), dict) else None
            if d.get('type') == 'event_msg' and payload:
                kind = payload.get('type')
                if kind in ('task_complete', 'turn_aborted'):
                    yield 'end', '', 'stop' if kind == 'task_complete' else 'aborted'
                elif kind == 'task_started':
                    yield 'start', '', None
                continue
            msg = d.get('message') if isinstance(d.get('message'), dict) else None
            if msg is None and payload and payload.get('type') == 'message':
                msg = payload                          # Codex rollout
            if msg is None or not msg.get('role'):
                continue
            c = msg.get('content')
            if isinstance(c, list):
                text = ''.join(b.get('text', '') for b in c if isinstance(b, dict)
                               and b.get('type') in ('text', 'output_text', 'input_text'))
            else:
                text = c if isinstance(c, str) else ''
            yield msg['role'], text, msg.get('stopReason') or msg.get('stop_reason')


def records(path: Path):
    """Yield (role, text) for user/assistant records."""
    for role, text, _ in entries(path):
        if role in ('user', 'assistant'):
            yield role, text


def turn_state(path: Path, marker: str, agent: str) -> str | None:
    """State of the turn that the [marker] pointer started: 'working', 'done', 'failed' (error/abort), or
    None when the record has no user message with the marker. A later user message with text also ends it."""
    state = None
    for role, text, stop in entries(path):
        if role == 'user' and marker in text:
            state = 'working'
        elif state is None:
            continue
        elif role == 'end':
            state = 'done' if stop == 'stop' else 'failed'
        elif role == 'start':
            state = 'working'
        elif role == 'assistant' and agent != 'codex':     # Codex turns end only with task_complete
            state = 'done' if stop in DONE_STOPS else 'failed' if stop in FAILED_STOPS else 'working'
        elif role == 'user' and text.strip() and state != 'working':
            state = 'done'
        elif role not in ('assistant', 'user'):
            state = 'working'                              # tool results: the turn continues
    return state


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
    needles = {marker, json.dumps(marker)[1:-1], json.dumps(marker, ensure_ascii=False)[1:-1]}
    for p in store_files(agent, cwd)[:60]:
        raw = p.read_text(encoding='utf-8', errors='replace')
        if not any(n in raw for n in needles):
            continue
        if any(r == 'user' and marker in t for r, t in records(p)):
            return p
    return None


# ---------------------------------------------------------------- resolution
def resolve(spec: dict, cwd: str, handle: str | None = None, launch: bool = False,
            thinking: str | None = None, adopt: bool = False) -> tuple[str, Path | None]:
    """Return (terminal handle, session file) for a session target in this worktree.

    Order: explicit handle; the remembered permanent reviewer (its terminal must still run the target's
    agent kind); a 'title' regex; a live terminal of the target's agent kind (and model) from
    `adash ls`; the omp session store. adopt=True remembers a reviewer found live as the permanent one;
    with launch=True a missing reviewer is spawned."""
    if handle:
        return handle, None
    self_handle = os.environ.get('ADASH_HANDLE')   # never review with yourself
    terms = [t for t in terminals() if in_worktree(t, cwd) and t.get('handle') != self_handle]
    agents = live_agents()
    term_ = known_terminal(spec, cwd, terms, agents)
    if term_:
        return term_['handle'], None
    try:
        term_, path = _resolve_live(spec, cwd, terms, agents)
    except SystemExit:
        if not launch:
            raise
        return spawn(spec, cwd, thinking), None
    if adopt:
        remember(cwd, spec['name'], term_['handle'])
    return term_['handle'], path


def known_terminal(spec: dict, cwd: str, terms: list[dict], agents: dict | None) -> dict | None:
    """Live terminal of the remembered reviewer. A terminal whose agent has exited (a bare shell) is not
    reused: the pointer would be typed into the shell."""
    known = remembered(cwd, spec['name'])
    hit = next((t for t in terms if known and t.get('handle') == known), None)
    if hit and agents is not None and not kind_ok(spec, agents.get(hit['handle'])):
        print(f"resolve: remembered {spec['name']} terminal {known} no longer runs "
              f"{spec.get('agent', 'omp')}; not reusing it", file=sys.stderr)
        return None
    return hit


def _resolve_live(spec: dict, cwd: str, terms: list[dict], agents: dict | None) -> tuple[dict, Path | None]:
    if spec.get('title'):
        hits = [t for t in terms if re.search(spec['title'], t.get('title') or '')
                or re.search(spec['title'], t.get('windowName') or '')]
        if len(hits) == 1:
            return hits[0], None
        raise SystemExit(f"resolve: title /{spec['title']}/ matched {len(hits)} terminals")
    found = _resolve_agents(spec, terms, agents) if agents is not None else None
    if found:
        return found
    agent = spec.get('agent', 'omp')
    if agent != 'omp':
        raise SystemExit(f"resolve: no live '{agent}' terminal in {cwd}; use --handle or a 'title' regex")
    rx = re.compile(spec['model'], re.I)
    for path in store_files('omp', cwd):
        model = dominant_model(path)
        if not rx.search(model):
            continue
        title = session_title(path)
        hits = [t for t in terms if (agents is None or kind_ok(spec, agents.get(t['handle'])))
                and title and title in f"{t.get('title') or ''} {t.get('windowName') or ''}"]
        if len(hits) == 1:
            return hits[0], path
    cands = '\n'.join(f"  {t['handle']}  {t.get('windowName')}  {t.get('title')}" for t in terms)
    raise SystemExit(f"resolve: no live omp terminal in {cwd} whose session model matches "
                     f"/{spec['model']}/. Terminals here:\n{cands}\nUse --handle.")


def _resolve_agents(spec: dict, terms: list[dict], agents: dict) -> tuple[dict, Path | None] | None:
    """A live terminal whose agent (per `adash ls`) is the target's kind and, if the target names one, model.

    adash maps each terminal to its agent process and session record, so a reviewer restarted by hand or
    restored after a tmux restart (generic title such as 'OMP ready') is still found."""
    rx = re.compile(spec['model'], re.I) if spec.get('model') else None
    cands = []
    for t in terms:
        a = agents.get(t['handle'])
        if not kind_ok(spec, a):
            continue
        ident = a.get('identity') or ''
        path = Path(ident) if ident.startswith('/') and Path(ident).is_file() else None
        if rx and not rx.search(a.get('model') or (dominant_model(path) if path else '')):
            continue
        cands.append((a.get('stateSince') or 0, t, path))
    if not cands:
        return None
    cands.sort(key=lambda c: c[0], reverse=True)
    if len(cands) > 1:
        print(f"resolve: {len(cands)} live {spec['name']} sessions here; using the most recently active, "
              f"{cands[0][1]['handle']}", file=sys.stderr)
    return cands[0][1], cands[0][2]


# ---------------------------------------------------------------- adash threads (optional)
def adash_hook(args: list[str], stdin: str | None = None) -> None:
    """Tell adash about this exchange (draws the review/propose edge).
    No-op when adash is not installed or ADASH_HOOK=0; never affects the review itself."""
    exe = shutil.which('adash')
    if not exe or os.environ.get('ADASH_HOOK') == '0':
        return
    try:
        subprocess.run([exe, 'thread', *args], input=stdin, text=True, capture_output=True, timeout=5)
    except Exception:
        pass


def adash_register(a, handle: str, brief: Path, role: str) -> None:
    """--role names the helper session '<requester>-<role>' in adash unless it already has a name."""
    me = os.environ.get('ADASH_HANDLE')
    if me:
        adash_hook(['register', '--from', me, '--to', handle, '--marker', a.marker, '--brief', str(brief.resolve()),
                    '--kind', 'propose' if a.mode == 'propose' else 'review', '--mode', a.mode, '--role', role])


# ---------------------------------------------------------------- commands
def pointer_line(brief: Path, cwd: str, marker: str, mode: str, note: str | None,
                 answer_file: Path | None = None) -> str:
    try:
        ref = os.path.relpath(brief.resolve(), cwd)
        ref = ref if not ref.startswith('..') else str(brief.resolve())
    except ValueError:
        ref = str(brief.resolve())
    parts = [f"[{marker}]", f"@{ref} 를 읽고 답해줘."]
    if note:
        parts.append(note.replace('\n', ' '))
    suffix = MODE_SUFFIX[mode]
    if answer_file:
        rest = ('시안 폴더 밖의 다른 파일은 수정하지 마.' if mode == 'propose'
                else '그 밖의 파일은 만들거나 수정하지 마.')
        suffix = suffix.replace('파일은 수정하지 마.', f'답 전체를 {answer_file} 한 파일에 쓰고, {rest}')
    parts.append(suffix)
    return ' '.join(parts)


def composer_busy(screen: str, agent: str = 'omp') -> bool:
    """True when the input area holds text (an unsubmitted user draft).

    The omp/Claude/Codex TUIs draw the input area between the last two full-width rule
    lines (────). Boxed tool output (│ … │) higher up in the transcript is not the composer.
    The agy TUI draws one rule and the '>' prompt line directly below it; in a permission mode
    such as accept-edits the empty prompt shows a placeholder ending in '(shift+tab to cycle)'.
    """
    lines = screen.splitlines()
    rules = [i for i, l in enumerate(lines) if l.strip() and set(l.strip()) <= set('─━')]
    if agent == 'agy':
        if not rules:
            return False
        start = rules[-2] if len(rules) >= 2 and rules[-1] - rules[-2] <= 3 else rules[-1]
        inner = [l for l in lines[start + 1:start + 3] if not (set(l.strip()) <= set('─━'))]
        inner = [l for l in inner if '(shift+tab to cycle)' not in l]
        return any(re.sub(r'[\s>]', '', l) for l in inner[:1])
    if len(rules) < 2:
        return False
    inner = [re.sub(r'[│┃\s>❯›]', '', l) for l in lines[rules[-2] + 1:rules[-1]]]
    # an empty omp box can show a key hint ("<⇧><⇥> to change thinking effort") that starts with
    # Nerd Font key glyphs (private use area); typed text never does (same rule as adash)
    pua = lambda c: 0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0xFFFFD
    return any(t and not pua(t[0]) for t in inner)


def cmd_send(a, spec, cwd) -> int:
    handle, _ = resolve(spec, cwd, a.handle, launch=not a.no_launch, thinking=a.thinking, adopt=True)
    brief = Path(a.brief)
    if not brief.exists():
        print(f'send: brief {brief} not found', file=sys.stderr)
        return 3
    agent = spec.get('agent', 'omp')
    if not a.force and composer_busy(terminal_tail(handle, screen=True), agent):
        print('send: the target composer holds unsubmitted text; ask the user (or --force)', file=sys.stderr)
        return 5
    ans = None
    if file_answer(spec):
        ans = answer_path(spec, a.marker)
        if ans.exists():
            print(f'send: answer file {ans} already exists; use a new marker', file=sys.stderr)
            return 3
        ans.parent.mkdir(parents=True, exist_ok=True)
    line = pointer_line(brief, cwd, a.marker, a.mode, a.note, ans)
    for attempt in range(2):
        rc, _, err = term('send', handle, '--text', line, '--enter')
        if rc != 0:
            gone = not any(t.get('handle') == handle for t in terminals())
            if gone and attempt == 0 and not a.handle:
                remember(cwd, spec['name'], None)
                handle, _ = resolve(spec, cwd, None, launch=not a.no_launch, thinking=a.thinking, adopt=True)
                continue
            print(f'send: adash term send failed: {err}', file=sys.stderr)
            return 3
        for _ in range(15):
            time.sleep(2)
            if file_answer(spec):
                if a.marker in terminal_tail(handle, 60) or a.marker in terminal_tail(handle, screen=True):
                    print(json.dumps({'handle': handle, 'answer_file': str(answer_path(spec, a.marker)),
                                      'marker': a.marker}, ensure_ascii=False))
                    adash_register(a, handle, brief, spec['name'])
                    return 0
                continue
            path = find_marker_file(agent, cwd, a.marker)
            if path:
                print(json.dumps({'handle': handle, 'session': str(path), 'marker': a.marker}, ensure_ascii=False))
                adash_register(a, handle, brief, spec['name'])
                return 0
        if attempt == 0 and not a.handle:
            handle, _ = resolve(spec, cwd, None, adopt=True)
    print(f'send: typed into {handle} but not seen by the agent (not delivered)', file=sys.stderr)
    return 3


def answer_after(path: Path, marker: str) -> str:
    recs = list(records(path))
    idx = [i for i, (r, t) in enumerate(recs) if r == 'user' and marker in t]
    if not idx:
        return ''
    return '\n\n'.join(t for r, t in recs[idx[-1] + 1:] if r == 'assistant' and t.strip())


def is_busy(handle: str | None, agent: str) -> bool:
    """The agent is working: adash's state for the handle when it knows it (asking counts as busy: a
    permission prompt holds the turn), else a busy token near the bottom of the screen."""
    if not handle:
        return False
    agents = live_agents()
    state = ((agents or {}).get(handle) or {}).get('state')
    if state:
        return state in ('working', 'asking')
    tail = '\n'.join(terminal_tail(handle, screen=True).splitlines()[-15:])
    return any(tok in tail for tok in BUSY.get(agent, []))


def file_sig(path: Path) -> tuple:
    try:
        st = path.stat()
        return st.st_size, st.st_mtime_ns
    except OSError:
        return ()


def cmd_wait(a, spec, cwd) -> int:
    agent = spec.get('agent', 'omp')
    try:
        handle, _ = resolve(spec, cwd, a.handle)
    except SystemExit:
        handle = a.handle
    ans_file = answer_path(spec, a.marker) if file_answer(spec) else None
    deadline = time.time() + a.timeout
    path, next_find, sig, state = None, 0.0, (), None
    while time.time() < deadline:
        if ans_file:
            ans = settled(ans_file, handle, agent, a.settle, lambda: ans_file.read_text()
                          if ans_file.exists() and ans_file.stat().st_size else '')
            if ans:
                emit(ans, a.out)
                adash_hook(['answered', '--marker', a.marker], stdin=ans)
                return 0
        elif path is None and time.time() >= next_find:
            path = find_marker_file(agent, cwd, a.marker)
            next_find = time.time() + 10
        if path is not None:
            now = file_sig(path)
            if now != sig:
                sig, state = now, turn_state(path, a.marker, agent)
            if state in ('done', 'failed'):
                time.sleep(SETTLE if state == 'done' else a.settle)   # a resumed or retried turn changes the file
                if file_sig(path) == sig:
                    ans = answer_after(path, a.marker)
                    if ans.strip():
                        emit(ans, a.out)
                        adash_hook(['answered', '--marker', a.marker], stdin=ans)
                        return 0
                    print(f"wait: the reviewer {'finished' if state == 'done' else 'stopped (error or abort) in'} "
                          f"the [{a.marker}] turn without an answer; read its terminal {handle}", file=sys.stderr)
                    return 4
                continue
        time.sleep(POLL)
    print('wait: timeout', file=sys.stderr)
    return 4


def settled(path: Path, handle: str | None, agent: str, settle: float, read) -> str:
    """Answer from read() once the agent is not working and path is unchanged for settle seconds."""
    if not read() or is_busy(handle, agent):
        return ''
    m0 = file_sig(path)
    time.sleep(settle)
    return read() if not is_busy(handle, agent) and file_sig(path) == m0 else ''


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
    ap.add_argument('--handle', help='explicit adash terminal handle t_… (skips resolution)')
    ap.add_argument('--cwd', default=os.getcwd(), help='worktree directory of the target session (default: here)')
    ap.add_argument('--brief')
    ap.add_argument('--marker', help='unique tag, e.g. "sec3 KO v2 check" (brackets optional)')
    ap.add_argument('--mode', choices=list(MODE_SUFFIX), default='accept')
    ap.add_argument('--note', help='one extra sentence appended to the pointer line')
    ap.add_argument('--out', help='also write the answer to this file')
    ap.add_argument('--timeout', type=float, default=3600)
    ap.add_argument('--settle', type=float, default=20,
                    help='quiet seconds for a file answer, or after an error/abort turn end')
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
        h, _ = resolve(spec, cwd, a.handle, launch=True, thinking=a.thinking, adopt=True)
        print(json.dumps({'target': spec['name'], 'handle': h}, ensure_ascii=False))
        return 0
    if a.command == 'close':
        known = None if a.handle else known_terminal(
            spec, cwd, [t for t in terminals() if in_worktree(t, cwd)], None)
        h = a.handle or (known or {}).get('handle')
        if not h:
            remember(cwd, spec['name'], None)
            print('close: no live remembered reviewer here', file=sys.stderr)
            return 2
        rc, _, err = term('close', h)
        if rc != 0:
            print(f'close: adash term close {h} failed: {err}', file=sys.stderr)
            return 2
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
        if file_answer(spec):
            f = answer_path(spec, a.marker)
            ans = f.read_text() if f.exists() else ''
        else:
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
