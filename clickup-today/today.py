#!/usr/bin/env python3
"""Local Markdown day sheet backed by the installed clickup-cli."""

import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys


CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
START = "## 오늘 작업"
END = "## 메모"
LEGACY_START = "<!-- clickup-today:start -->"
LEGACY_END = "<!-- clickup-today:end -->"
ROW = re.compile(r"^\s*- \[([ xX])\] \[.*\]\(https://app\.clickup\.com/t/([a-zA-Z0-9]+)\)", re.M)
FOCUS = re.compile(r"<!-- clickup:([a-zA-Z0-9]+) focus -->")
LINK = re.compile(r"https://app\.clickup\.com/t/([a-zA-Z0-9]+)")


def configured_lists():
    if not CONFIG_PATH.is_file():
        raise RuntimeError(f"Missing {CONFIG_PATH}; create it with {{\"lists\": [\"LIST_ID\"]}}")
    try:
        config = json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {CONFIG_PATH}: {exc}") from exc
    if not isinstance(config, dict) or not isinstance(config.get("lists"), list) or not config["lists"]:
        raise RuntimeError(f"{CONFIG_PATH} must contain a nonempty \"lists\" array of list IDs")
    lists = config["lists"]
    if any(not isinstance(list_id, str) or not list_id.strip() for list_id in lists) or len(set(lists)) != len(lists):
        raise RuntimeError(f"{CONFIG_PATH} must contain unique, nonempty string list IDs")
    return tuple(lists)


def local_items(text):
    """Keep user-written bullets under their nearest linked ClickUp ancestor."""
    if START not in text or END not in text:
        return {}
    block = text.split(START, 1)[1].split(END, 1)[0]
    items = {}
    parents = []
    for line in block.splitlines():
        if not line.lstrip().startswith("- "):
            continue
        indent = len(line) - len(line.lstrip())
        match = LINK.search(line)
        if match:
            while parents and parents[-1][0] >= indent:
                parents.pop()
            parents.append((indent, match.group(1)))
        else:
            parent_indent, parent_id = parents[-1] if parents else (-2, None)
            items.setdefault(parent_id, []).append((max(0, indent - parent_indent - 2), line.lstrip()))
    return items


def cli(*args):
    command = [os.environ.get("CLICKUP_CLI") or "clickup-cli", "--output", "json", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"{' '.join(command[3:])}: {result.stderr.strip() or result.stdout.strip()}")
    data = json.loads(result.stdout)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected ClickUp response for {args[0]}: expected an array")
    return data


def one(*args):
    result = cli(*args)
    if len(result) != 1:
        raise RuntimeError(f"Expected one result for {args[0]} {args[1]}")
    return result[0]


def completed(task):
    return task["status"]["type"] in ("done", "closed")


def due_by(task, day):
    value = task.get("due_date")
    return value is not None and datetime.fromtimestamp(int(value) / 1000).date() <= day


def rows(text):
    return {task_id: checked != " " for checked, task_id in ROW.findall(text)}


def sheet_path(day):
    return Path(__file__).resolve().parent / "days" / f"{day.isoformat()}.md"


def focus_path(day):
    return sheet_path(day).with_name(f".{day.isoformat()}-focus.json")


def title(task):
    name = str(task["name"]).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")
    return f"[{name}]({task.get('url') or 'https://app.clickup.com/t/' + task['id']})"


def render(task, checked=False, depth=0):
    box = "x" if checked else " "
    due = task.get("due_date")
    label = ""
    if due:
        when = datetime.fromtimestamp(int(due) / 1000)
        label = f" · {when:%m-%d}" + (f" {when:%H:%M}" if task.get("due_date_time") else "")
    return f"{'  ' * depth}- [{box}] {title(task)}{label}"


def refresh(day, focus):
    configured = configured_lists()
    path = sheet_path(day)
    old = path.read_text() if path.exists() else ""
    if old and END not in old:
        raise RuntimeError(f"Cannot safely refresh document without {END}: {path}")
    checked = rows(old.split(START, 1)[1].split(END, 1)[0]) if START in old else rows(old)
    handwritten = local_items(old)
    saved_focus = focus_path(day)
    focused = set(json.loads(saved_focus.read_text())) if saved_focus.exists() else set()
    focused.update(FOCUS.findall(old))  # Migrate the first version's inline IDs.
    focused.update(focus)
    tasks = {}
    for list_id in configured:
        for task in cli("--all", "task", "list", "--list", list_id, "--include-closed", "--subtasks"):
            tasks[task["id"]] = task
    for task_id in focused:
        if task_id not in tasks:
            task = one("task", "get", task_id)
            if task["list"]["id"] not in configured:
                raise RuntimeError(f"Task outside configured lists: {task_id}")
            tasks[task_id] = task

    # A due parent exposes its entire unfinished subtree, including undated subtasks.
    selected = {task_id for task_id, task in tasks.items() if not completed(task) and
                (due_by(task, day) or task_id in focused or checked.get(task_id, False))}
    children = {}
    for task in tasks.values():
        children.setdefault(task.get("parent"), []).append(task["id"])
    stack = list(selected)
    while stack:
        for child_id in children.get(stack.pop(), []):
            if child_id not in selected and not completed(tasks[child_id]):
                selected.add(child_id)
                stack.append(child_id)
    # Keep only the ancestor chain of each displayed task as non-actionable context.
    visible = set(selected)
    for task_id in selected:
        parent = tasks[task_id].get("parent")
        while parent in tasks and parent not in visible:
            visible.add(parent)
            parent = tasks[parent].get("parent")
    focused &= selected

    def order(task_id):
        task = tasks[task_id]
        due = task.get("due_date")
        return (int(due) if due else float("inf"), task["name"].casefold())

    def branch(task_id, depth, seen):
        if task_id in seen:
            return []
        seen.add(task_id)
        task = tasks[task_id]
        line = render(task, checked.get(task_id, False), depth) if task_id in selected else (
            f"{'  ' * depth}- **{title(task)}**")
        lines = [line]
        for extra_indent, manual in handwritten.pop(task_id, []):
            lines.append(f"{'  ' * (depth + 1) + ' ' * extra_indent}{manual}")
        for child_id in sorted(children.get(task_id, []), key=order):
            if child_id in visible:
                lines.extend(branch(child_id, depth + 1, seen))
        return lines

    def root_order(task_id):
        pending = [task_id]
        seen_ids = set()
        earliest = float("inf")
        while pending:
            current = pending.pop()
            if current in seen_ids:
                continue
            seen_ids.add(current)
            due = tasks[current].get("due_date")
            if current in selected and due:
                earliest = min(earliest, int(due))
            pending.extend(child for child in children.get(current, ()) if child in visible)
        return (earliest, tasks[task_id]["name"].casefold())

    groups = []
    seen = set()
    for list_id in configured:
        roots = [task_id for task_id in visible if tasks[task_id]["list"]["id"] == list_id
                 and tasks[task_id].get("parent") not in visible]
        if roots:
            name = tasks[roots[0]]["list"]["name"]
            groups.append(f"### {name}\n")
            for root in sorted(roots, key=root_order):
                groups.extend(branch(root, 0, seen))
            groups.append("")
    if handwritten:
        groups.append("### 로컬 항목\n")
        for entries in handwritten.values():
            groups.extend("  " * (extra_indent // 2) + manual for extra_indent, manual in entries)
        groups.append("")
    notes = old.split(END, 1)[1] if old else "\n\n"
    content = (f"# {day.isoformat()} 오늘 할 일\n\n"
               "오늘까지 기한이 지난 미완료 작업과 관련 하위 작업입니다. 체크는 로컬에 저장됩니다.\n\n"
               + START + "\n\n" + ("\n".join(groups).rstrip() if groups else "오늘 표시할 작업이 없습니다.")
               + "\n\n" + END + notes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    saved_focus.write_text(json.dumps(sorted(focused)))
    print(f"{path} ({len(selected)} tasks, {len(visible) - len(selected)} context)")


def completion_status(list_id):
    statuses = one("list", "get", list_id)["statuses"]
    candidates = [status for status in statuses if status["type"] in ("done", "closed")
                  and status["status"].casefold() not in ("cancelled", "canceled")]
    for preferred in ("completed", "complete", "done"):
        for status in candidates:
            if status["status"].casefold() == preferred:
                return status["status"]
    if len(candidates) == 1:
        return candidates[0]["status"]
    raise RuntimeError(f"No unambiguous completion status for list {list_id}")


def push(day):
    configured = configured_lists()
    path = sheet_path(day)
    text = path.read_text()
    if text.count(START) != 1 or text.count(END) != 1:
        raise RuntimeError("Day sheet is missing its managed section")
    block = text.split(START, 1)[1].split(END, 1)[0]
    ids = [task_id for checked, task_id in ROW.findall(block) if checked.lower() == "x"]
    statuses = {}
    for task_id in dict.fromkeys(ids):
        task = one("task", "get", task_id)
        if completed(task):
            print(f"Already complete: {task_id}")
            continue
        list_id = task["list"]["id"]
        if list_id not in configured:
            raise RuntimeError(f"Refusing to update task outside configured lists: {task_id}")
        if list_id not in statuses:
            statuses[list_id] = completion_status(list_id)
        status = statuses[list_id]
        cli("task", "update", task_id, "--status", status)
        saved = one("task", "get", task_id)
        if saved["status"]["status"] != status or not completed(saved):
            raise RuntimeError(f"ClickUp did not save completion for {task_id}")
        print(f"Completed: {saved['name']} ({task_id})")
    # Re-read from ClickUp only after every requested update is verified.
    refresh(day, ())


def publish(day):
    """Register local checkboxes as subtasks; never infer completion from a local tick."""
    configured = configured_lists()
    path = sheet_path(day)
    text = path.read_text()
    if text.count(START) != 1 or text.count(END) != 1:
        raise RuntimeError("Day sheet is missing its managed section")
    lists = {
        list_id: cli("--all", "task", "list", "--list", list_id, "--include-closed", "--subtasks")
        for list_id in configured
    }
    published = 0
    while True:
        lines = text.splitlines(keepends=True)
        parents = []
        candidate = None
        inside = False
        for index, line in enumerate(lines):
            if line.strip() == START:
                inside = True
                continue
            if line.strip() == END:
                break
            if not inside or not line.lstrip().startswith("- "):
                continue
            indent = len(line) - len(line.lstrip())
            while parents and parents[-1][0] >= indent:
                parents.pop()
            linked = LINK.search(line)
            if linked:
                parents.append((indent, linked.group(1)))
                continue
            manual = re.fullmatch(r"(\s*)- \[([ xX])\] (.+)", line.rstrip("\n"))
            if manual:
                if not parents:
                    raise RuntimeError(f"Local item without a linked ClickUp parent: {manual.group(3)}")
                candidate = index, parents[-1][1], manual
                break
        if candidate is None:
            break
        index, parent_id, manual = candidate
        name = manual.group(3).strip()
        if not name:
            raise RuntimeError("Local checkbox has an empty task name")
        parent = one("task", "get", parent_id)
        list_id = parent["list"]["id"]
        if list_id not in configured:
            raise RuntimeError(f"Parent outside configured lists: {parent_id}")
        same = [task for task in lists[list_id] if task.get("parent") == parent_id
                and task["name"].strip().casefold() == name.casefold()]
        if len(same) > 1:
            raise RuntimeError(f"Ambiguous sibling tasks named {name!r} under {parent_id}")
        if same:
            saved = one("task", "get", same[0]["id"])
            disposition = "Existing"
        else:
            try:
                created = one("task", "create", "--list", list_id, "--name", name, "--parent", parent_id)
            except RuntimeError:
                # A lost response may follow a successful create. Reconcile; never retry blindly.
                lists[list_id] = cli("--all", "task", "list", "--list", list_id, "--include-closed", "--subtasks")
                matches = [task for task in lists[list_id] if task.get("parent") == parent_id
                           and task["name"].strip().casefold() == name.casefold()]
                if len(matches) != 1:
                    raise
                created = matches[0]
            saved = one("task", "get", created["id"])
            disposition = "Created"
        if saved["name"].strip().casefold() != name.casefold() or saved.get("parent") != parent_id or saved["list"]["id"] != list_id:
            raise RuntimeError(f"ClickUp task mismatch after registration: {saved['id']}")
        if not same:
            lists[list_id].append(saved)
        escaped = name.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        newline = "\n" if lines[index].endswith("\n") else ""
        lines[index] = (f"{manual.group(1)}- [{manual.group(2)}] "
                        f"[{escaped}](https://app.clickup.com/t/{saved['id']}){newline}")
        text = "".join(lines)
        path.write_text(text)
        published += 1
        print(f"{disposition}: {name} ({saved['id']})")
    if published:
        refresh(day, ())
    else:
        print("No local checkboxes to register")


def main():
    parser = argparse.ArgumentParser(description="ClickUp daily Markdown sheet for Typora")
    parser.add_argument("action", choices=("refresh", "publish", "push"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="local YYYY-MM-DD (default: today)")
    parser.add_argument("--focus", action="append", default=[], metavar="TASK_ID", help="include an undated task; repeatable (refresh only)")
    args = parser.parse_args()
    if args.focus and args.action != "refresh":
        parser.error("--focus is only supported with refresh")
    try:
        if args.action == "refresh":
            refresh(args.date, args.focus)
        elif args.action == "publish":
            publish(args.date)
        else:
            push(args.date)
    except (RuntimeError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
