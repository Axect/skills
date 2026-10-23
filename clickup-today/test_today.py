"""Behavioural checks using fake list IDs and in-memory ClickUp responses."""

from datetime import date, datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import today

REAL_CONFIGURED_LISTS = today.configured_lists


class DaySheetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lists = ("list-alpha", "list-beta")
        lists_patch = patch.object(today, "configured_lists", return_value=self.lists)
        lists_patch.start()
        self.addCleanup(lists_patch.stop)
        self.path = Path(self.tmp.name) / "2026-09-29.md"
        self.tasks = [
            self.task("overdue", "2026-09-28", "open"),
            self.task("today", "2026-09-29", "custom"),
            self.task("future", "2026-10-01", "open"),
            self.task("closed", "2026-09-27", "closed"),
            self.task("undated", None, "open"),
            self.task("grandchild", None, "open"),
            self.task("closed-child", None, "closed"),
            self.task("standalone", None, "open"),
        ]
        self.tasks[4]["parent"] = "overdue"
        self.tasks[5]["parent"] = "undated"
        self.tasks[6]["parent"] = "overdue"
        self.tasks[1]["parent"] = "future"
        self.day = date(2026, 9, 29)

    @staticmethod
    def task(identifier, due, status):
        return {
            "id": identifier, "name": identifier, "url": f"https://app.clickup.com/t/{identifier}",
            "list": {"id": "list-alpha", "name": "Example list"},
            "status": {"type": status, "status": "completed" if status == "closed" else status},
            "due_date": str(int(datetime.fromisoformat(due).timestamp() * 1000)) if due else None,
            "parent": None,
        }

    def test_refresh_preserves_notes_and_checks_without_future_or_done_tasks(self):
        with patch.object(today, "sheet_path", return_value=self.path), patch.object(today, "cli", side_effect=[self.tasks, []]):
            today.refresh(self.day, ())
        content = self.path.read_text()
        self.assertIn("- [ ] [overdue]", content)
        self.assertIn("  - [ ] [undated]", content)
        self.assertIn("    - [ ] [grandchild]", content)
        self.assertIn("- **[future]", content)  # Future parent is context, not actionable today.
        self.assertIn("  - [ ] [today]", content)
        self.assertNotIn("[closed-child]", content)
        self.assertNotIn("[standalone]", content)
        self.assertNotIn("<!--", content)
        content = content.replace(
            "  - [ ] [undated](https://app.clickup.com/t/undated)",
            "  - [ ] [undated](https://app.clickup.com/t/undated)\n"
            "    - [x] Draft\n    - [ ] Review",
        )
        self.path.write_text(content.replace("  - [ ] [today]", "  - [x] [today]") + "Local note\n")
        with patch.object(today, "sheet_path", return_value=self.path), patch.object(today, "cli", side_effect=[self.tasks, []]):
            today.refresh(self.day, ("standalone",))
        refreshed = self.path.read_text()
        self.assertIn("  - [x] [today]", refreshed)
        self.assertIn("Local note", refreshed)
        self.assertIn("[standalone]", refreshed)
        self.assertIn("    - [x] Draft\n    - [ ] Review", refreshed)
        self.assertEqual(set(today.rows(refreshed)), {"overdue", "undated", "grandchild", "today", "standalone"})
        with patch.object(today, "sheet_path", return_value=self.path), patch.object(today, "cli", side_effect=[self.tasks, []]):
            today.refresh(self.day, ())
        self.assertIn("[standalone]", self.path.read_text())
        self.assertIn("    - [x] Draft", self.path.read_text())

    def test_publish_creates_missing_siblings_and_links_existing_without_completing(self):
        parent = self.tasks[0]
        existing = {**self.task("existing", None, "open"), "name": "Review",
                    "parent": parent["id"]}
        remote = {parent["id"]: parent, existing["id"]: existing}
        created = []
        self.path.write_text(
            f"{today.START}\n{today.render(parent)}\n"
            "  - [x] Draft\n    - [ ] Outline\n  - [ ] Review\n  - [ ] Submit\n"
            f"{today.END}\n"
        )

        def fake_cli(*args):
            if args[0] == "--all":
                return list(remote.values()) if args[4] == self.lists[0] else []
            if args[:2] == ("task", "get"):
                return [remote[args[2]]]
            if args[:2] == ("task", "create"):
                identifier = f"new{len(created)}"
                task = {**self.task(identifier, None, "open"), "name": args[args.index("--name") + 1],
                        "parent": args[args.index("--parent") + 1]}
                remote[identifier] = task
                created.append(task)
                return [task]
            self.fail(f"Unexpected remote write: {args}")

        with patch.object(today, "sheet_path", return_value=self.path), \
             patch.object(today, "cli", side_effect=fake_cli), \
             patch.object(today, "refresh"):
            today.publish(self.day)
            today.publish(self.day)
        content = self.path.read_text()
        self.assertEqual([task["name"] for task in created], ["Draft", "Outline", "Submit"])
        self.assertIn("- [x] [Draft](https://app.clickup.com/t/new0)", content)
        self.assertIn("- [ ] [Review](https://app.clickup.com/t/existing)", content)
        self.assertNotIn("- [ ] Review\n", content)
        self.assertEqual([task["parent"] for task in created], [parent["id"], "new0", parent["id"]])
        self.assertTrue(all(task["status"]["type"] == "open" for task in created))

    def test_push_uses_list_completion_not_cancelled_and_verifies_saved_status(self):
        self.path.write_text(f"{today.START}\n{today.render(self.tasks[0], True)}\n{today.END}\n")
        remote = self.tasks[0]
        saved = {**remote, "status": {"type": "closed", "status": "completed"}}
        list_metadata = {"statuses": [
            {"type": "done", "status": "cancelled"},
            {"type": "closed", "status": "completed"},
        ]}
        with patch.object(today, "sheet_path", return_value=self.path), \
             patch.object(today, "one", side_effect=[remote, list_metadata, saved]) as get, \
             patch.object(today, "cli", return_value=[]) as command, \
             patch.object(today, "refresh"):
            today.push(self.day)
        command.assert_called_once_with("task", "update", "overdue", "--status", "completed")
        self.assertEqual(get.call_count, 3)


    def test_config_is_private_and_required(self):
        config = Path(self.tmp.name) / "config.json"
        with patch.object(today, "CONFIG_PATH", config):
            with self.assertRaisesRegex(RuntimeError, "Missing .*config.json"):
                REAL_CONFIGURED_LISTS()
            config.write_text(json.dumps({"lists": ["list-alpha", "list-beta"]}))
            self.assertEqual(REAL_CONFIGURED_LISTS(), self.lists)
            config.write_text(json.dumps({"lists": []}))
            with self.assertRaisesRegex(RuntimeError, "nonempty"):
                REAL_CONFIGURED_LISTS()


    def test_cli_binary_override(self):
        with patch.dict(os.environ, {"CLICKUP_CLI": "/tmp/fake-clickup-cli"}), \
             patch.object(today.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "[]"
            self.assertEqual(today.cli("task", "get", "fake-id"), [])
        self.assertEqual(run.call_args.args[0],
                         ["/tmp/fake-clickup-cli", "--output", "json", "task", "get", "fake-id"])

if __name__ == "__main__":
    unittest.main()
