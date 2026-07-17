import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "audit_workflow_state.py"
REQUIREMENTS = SKILL_ROOT / "requirements.txt"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_text(path, text, encoding="utf-8", newline=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding, newline=newline)


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def frontmatter(data, body="body\n"):
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {json.dumps(item)}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    lines.extend(["---", body])
    return "\n".join(lines)


def plain_yaml_mapping(data):
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {json.dumps(item)}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    return "\n".join(lines) + "\n"


class TempAuditFixture:
    def __init__(self, case):
        self.case = case
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.worktree = self.repo
        self.registry_dir = self.root / "registry"
        self.handoff_dir = self.root / "handoffs"
        self.manual_a = self.root / "manual-a.md"
        self.manual_b = self.root / "manual-b.md"
        self.por = self.root / "por;kept-as-argv.json"
        self.por_schema = self.root / "schema.json"
        self.validator = self.root / "fake validator.py"
        self.seen = self.root / "seen-argv.json"
        self.current_id = "current-task"
        self.branch = "feature/audit"
        self.task_path = "src/current.py"
        self._make_repo()
        self.registry_dir.mkdir()
        self.handoff_dir.mkdir()
        write_text(self.manual_a, "# Manual\nsame\n", newline="\r\n")
        self.manual_b.write_bytes(b"\xef\xbb\xbf# Manual\nsame\n")
        write_text(self.por_schema, "{}\n")
        write_text(self.por, "{}\n")
        self.add_registry(
            "current-task",
            status="active",
            target="Current task",
            parent_handoff_id="parent-task",
            allowed_paths=["src/current.py"],
            forbidden_paths=["runtime/**"],
        )
        self.add_registry(
            "parent-task",
            status="archived",
            target="Parent task",
            parent_handoff_id=None,
            allowed_paths=["docs/old.md"],
        )
        self.add_handoff(
            "parent-task",
            status="complete",
            parent_handoff_id=None,
            allowed_paths=["docs/old.md"],
        )
        self.add_handoff(
            "current-task",
            status="in_progress",
            parent_handoff_id="parent-task",
            allowed_paths=["src/current.py"],
        )
        self.write_validator(0)

    def cleanup(self):
        self.temp.cleanup()

    def _make_repo(self):
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "audit@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Audit Test"], cwd=self.repo, check=True)
        write_text(self.repo / "src" / "current.py", "print('current')\n")
        write_text(self.repo / "docs" / "old.md", "old\n")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.repo, check=True)
        subprocess.run(["git", "checkout", "-qb", self.branch], cwd=self.repo, check=True)

    def add_registry(self, handoff_id, **overrides):
        data = {
            "status": overrides.pop("status", "active"),
            "target": overrides.pop("target", handoff_id),
            "handoff_id": handoff_id,
            "parent_handoff_id": overrides.pop("parent_handoff_id", None),
            "branch": overrides.pop("branch", self.branch),
            "worktree": overrides.pop("worktree", str(self.worktree)),
            "allowed_paths": overrides.pop("allowed_paths", []),
            "forbidden_paths": overrides.pop("forbidden_paths", []),
            "updated_at": overrides.pop("updated_at", "2026-07-12T00:00:00+08:00"),
            "last_verified": overrides.pop("last_verified", "2026-07-12T00:00:00+08:00"),
        }
        data.update(overrides)
        write_text(self.registry_dir / f"{handoff_id}.md", frontmatter(data))

    def add_registry_file(self, filename, handoff_id, **overrides):
        data = {
            "status": overrides.pop("status", "active"),
            "target": overrides.pop("target", handoff_id),
            "handoff_id": handoff_id,
            "parent_handoff_id": overrides.pop("parent_handoff_id", None),
            "branch": overrides.pop("branch", self.branch),
            "worktree": overrides.pop("worktree", str(self.worktree)),
            "allowed_paths": overrides.pop("allowed_paths", []),
            "forbidden_paths": overrides.pop("forbidden_paths", []),
            "updated_at": overrides.pop("updated_at", "2026-07-12T00:00:00+08:00"),
            "last_verified": overrides.pop("last_verified", "2026-07-12T00:00:00+08:00"),
        }
        data.update(overrides)
        write_text(self.registry_dir / filename, frontmatter(data))

    def add_handoff(self, handoff_id, **overrides):
        data = {
            "handoff_id": handoff_id,
            "parent_handoff_id": overrides.pop("parent_handoff_id", None),
            "status": overrides.pop("status", "in_progress"),
            "branch": overrides.pop("branch", self.branch),
            "worktree": overrides.pop("worktree", str(self.worktree)),
            "allowed_paths": overrides.pop("allowed_paths", []),
        }
        data.update(overrides)
        write_text(self.handoff_dir / f"{handoff_id}.md", frontmatter(data))

    def add_handoff_file(self, filename, handoff_id, **overrides):
        data = {
            "handoff_id": handoff_id,
            "parent_handoff_id": overrides.pop("parent_handoff_id", None),
            "status": overrides.pop("status", "in_progress"),
            "branch": overrides.pop("branch", self.branch),
            "worktree": overrides.pop("worktree", str(self.worktree)),
            "allowed_paths": overrides.pop("allowed_paths", []),
        }
        data.update(overrides)
        write_text(self.handoff_dir / filename, frontmatter(data))

    def remove_registry_field(self, handoff_id, field):
        path = self.registry_dir / f"{handoff_id}.md"
        data = self._read_frontmatter_for_rewrite(path)
        data.pop(field)
        write_text(path, frontmatter(data))

    def _read_frontmatter_for_rewrite(self, path):
        # Test helper only; production parser is covered by source assertions.
        import yaml

        text = path.read_text(encoding="utf-8")
        block = text.split("---", 2)[1]
        return yaml.safe_load(block)

    def write_validator(self, exit_code, writes_seen=False):
        body = [
            "import json, pathlib, sys",
            f"exit_code = {exit_code}",
        ]
        if writes_seen:
            body.append(f"pathlib.Path({str(self.seen)!r}).write_text(json.dumps(sys.argv), encoding='utf-8')")
        body.append("sys.exit(exit_code)")
        write_text(self.validator, "\n".join(body) + "\n")

    def args(self, *extra):
        return [
            "--repo-root", str(self.repo),
            "--worktree", str(self.worktree),
            "--branch", self.branch,
            "--task-path", self.task_path,
            "--registry-dir", str(self.registry_dir),
            "--handoff-dir", str(self.handoff_dir),
            "--current-handoff-id", self.current_id,
            "--terminal-status", "complete",
            "--terminal-status", "abandoned",
            "--terminal-status", "archived",
            "--manual", f"primary={self.manual_a}",
            "--manual", f"backup={self.manual_b}",
            "--por", str(self.por),
            "--por-repo-root", str(self.repo),
            "--por-schema", str(self.por_schema),
            "--vom-validator", str(self.validator),
            *extra,
        ]

    def snapshot(self):
        files = {}
        directories = []
        for current, dirs, names in os.walk(self.root):
            current_path = Path(current)
            if ".git" in current_path.parts:
                continue
            directories.append(str(current_path.relative_to(self.root)).replace("\\", "/"))
            for name in names:
                path = current_path / name
                files[str(path.relative_to(self.root)).replace("\\", "/")] = path.read_bytes()
        return directories, files, self.git_status()

    def git_status(self):
        return subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout


class AuditTestCase(unittest.TestCase):
    def setUp(self):
        self.fixture = TempAuditFixture(self)

    def tearDown(self):
        self.fixture.cleanup()

    def run_audit(self, args=None, python_args=None):
        self.assertTrue(SCRIPT.is_file(), f"missing audit script: {SCRIPT}")
        command = [sys.executable]
        if python_args:
            command.extend(python_args)
        command.extend(["-B", str(SCRIPT)])
        command.extend(self.fixture.args() if args is None else args)
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stdout is not stable JSON: {exc}; stdout={result.stdout!r}; stderr={result.stderr!r}")
        self.assertEqual("", result.stderr)
        self.assertEqual(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", result.stdout)
        for finding in payload.get("findings", []):
            self.assertEqual(
                {"subject", "evidence", "task_relevance", "actionability", "severity"},
                set(finding),
            )
        return result.returncode, payload

    def assert_has_finding(self, payload, subject, *, evidence=None, relevance=None, actionability=None, severity=None):
        matches = [item for item in payload["findings"] if item["subject"] == subject]
        if evidence is not None:
            matches = [item for item in matches if evidence in item["evidence"]]
        self.assertTrue(matches, f"missing finding {subject!r} evidence={evidence!r}; findings={payload['findings']!r}")
        item = matches[0]
        if relevance is not None:
            self.assertEqual(relevance, item["task_relevance"])
        if actionability is not None:
            self.assertEqual(actionability, item["actionability"])
        if severity is not None:
            self.assertEqual(severity, item["severity"])
        return item


class RequirementsTests(unittest.TestCase):
    def test_pyyaml_requirement_is_exactly_pinned(self):
        self.assertTrue(REQUIREMENTS.is_file())
        self.assertEqual("PyYAML==6.0.3\n", REQUIREMENTS.read_text(encoding="utf-8"))


class CliAndReadOnlyTests(AuditTestCase):
    def test_required_and_unknown_arguments_return_json_exit_2(self):
        for args in ([], self.fixture.args("--fix")):
            with self.subTest(args=args[-1:] if args else "missing"):
                code, payload = self.run_audit(args=args)
                self.assertEqual(2, code)
                self.assertFalse(payload["complete"])
                self.assertTrue(any(item["subject"] == "cli.arguments" for item in payload["findings"]))

    def test_valid_audit_is_read_only_and_stable(self):
        before = self.fixture.snapshot()
        code, first = self.run_audit()
        second_code, second = self.run_audit()
        after = self.fixture.snapshot()
        self.assertEqual(0, code)
        self.assertEqual(0, second_code)
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertFalse((self.fixture.root / "__pycache__").exists())
        self.assertEqual("valid", first["por"]["status"])

    def test_invalid_paths_utf8_and_yaml_errors_are_incomplete(self):
        cases = []
        bad_registry = self.fixture.registry_dir / "bad-utf8.md"
        bad_registry.write_bytes(b"---\nstatus: \xff\n---\n")
        cases.append("invalid utf8")
        bad_yaml = self.fixture.handoff_dir / "bad-yaml.md"
        write_text(bad_yaml, "---\nstatus: [unterminated\n---\n")
        cases.append("invalid yaml")
        missing_registry = self.fixture.root / "missing-registry"
        code, payload = self.run_audit(args=[
            *self.fixture.args(),
            "--registry-dir", str(missing_registry),
        ])
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        code, payload = self.run_audit()
        self.assertEqual(2, code, cases)
        self.assertFalse(payload["complete"])
        subjects = {item["subject"] for item in payload["findings"]}
        self.assertIn("registry:bad-utf8.md", subjects)
        self.assertIn("handoff:bad-yaml.md", subjects)

    def test_bom_frontmatter_loads_and_invalid_utf8_still_fails(self):
        registry_path = self.fixture.registry_dir / "current-task.md"
        handoff_path = self.fixture.handoff_dir / "current-task.md"
        registry_path.write_bytes(b"\xef\xbb\xbf" + registry_path.read_bytes())
        handoff_path.write_bytes(b"\xef\xbb\xbf" + handoff_path.read_bytes())

        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertTrue(payload["registry"]["current_found"])
        self.assertFalse(payload["findings"])

        write_bytes(self.fixture.registry_dir / "bad-utf8.md", b"\xef\xbb\xbf---\nstatus: \xff\n---\n")
        code, payload = self.run_audit()
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        self.assert_has_finding(payload, "registry:bad-utf8.md", evidence="invalid UTF-8")


class PyYamlAndParserTests(AuditTestCase):
    def test_missing_pyyaml_is_reported_as_json_without_installing(self):
        code, payload = self.run_audit(python_args=["-S"])
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        evidence = "\n".join(item["evidence"] for item in payload["findings"])
        self.assertIn("PyYAML", evidence)
        self.assertIn("requirements.txt", evidence)

    def test_source_uses_safe_load_and_no_regex_or_shell_parser(self):
        self.assertTrue(SCRIPT.is_file(), f"missing audit script: {SCRIPT}")
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("yaml.safe_load", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("import re", source)
        self.assertNotIn("re.", source)
        self.assertNotIn("--repair", source)
        self.assertNotIn("--archive", source)
        self.assertNotIn("--close", source)


class RegistryTests(AuditTestCase):
    def test_registry_required_fields_current_id_and_unknown_status(self):
        self.fixture.remove_registry_field("current-task", "last_verified")
        self.fixture.add_registry("unknown-status", status="paused", allowed_paths=["src/current.py"])
        code, payload = self.run_audit()
        self.assertEqual(1, code)
        subjects = {item["subject"] for item in payload["findings"]}
        self.assertIn("registry:current-task", subjects)
        self.assertIn("registry:unknown-status", subjects)
        self.assertTrue(payload["registry"]["current_found"])

    def test_registry_path_conflict_is_related_stop(self):
        self.fixture.add_registry("related-active", status="active", allowed_paths=["src/current.py"])
        code, payload = self.run_audit()
        self.assertEqual(1, code)
        self.assert_has_finding(payload, "registry:related-active", evidence="path", relevance="related", actionability="stop", severity="high")

    def test_same_branch_only_and_same_worktree_only_are_related_stop_conflicts(self):
        other_worktree = self.fixture.root / "other-worktree"
        other_worktree.mkdir()
        self.fixture.add_registry(
            "same-branch-only",
            status="active",
            worktree=str(other_worktree),
            allowed_paths=["docs/other.md"],
        )
        self.fixture.add_registry(
            "same-worktree-only",
            status="active",
            branch="feature/other",
            allowed_paths=["docs/other.md"],
        )

        code, payload = self.run_audit()
        self.assertEqual(1, code)
        self.assert_has_finding(payload, "registry:same-branch-only", evidence="branch", relevance="related", actionability="stop", severity="high")
        self.assert_has_finding(payload, "registry:same-worktree-only", evidence="worktree", relevance="related", actionability="stop", severity="high")

    def test_active_transitive_registry_ancestors_are_not_parallel_overlaps_but_sibling_is(self):
        self.fixture.add_registry(
            "root-task",
            status="active",
            parent_handoff_id=None,
            allowed_paths=["src/current.py"],
        )
        self.fixture.add_registry(
            "grandparent-task",
            status="active",
            parent_handoff_id="root-task",
            allowed_paths=["src/current.py"],
        )
        self.fixture.add_registry(
            "parent-task",
            status="active",
            parent_handoff_id="grandparent-task",
            allowed_paths=["src/current.py"],
        )
        self.fixture.add_registry(
            "sibling-task",
            status="active",
            parent_handoff_id="parent-task",
            allowed_paths=["src/current.py"],
        )

        code, payload = self.run_audit()

        self.assertEqual(1, code)
        overlap_subjects = {
            item["subject"]
            for item in payload["findings"]
            if item["evidence"].startswith("active registry overlaps")
        }
        self.assertFalse(
            {"registry:root-task", "registry:grandparent-task", "registry:parent-task"} & overlap_subjects,
            payload["findings"],
        )
        self.assert_has_finding(
            payload,
            "registry:sibling-task",
            evidence="active registry overlaps",
            relevance="related",
            actionability="stop",
            severity="high",
        )

    @unittest.skipUnless(os.name == "nt", "Windows drive-letter case behavior")
    def test_windows_absolute_worktree_case_variation_is_same_path(self):
        path = str(self.fixture.worktree)
        drive_variant = path[:1].swapcase() + path[1:]
        self.assertNotEqual(path, drive_variant)
        self.fixture.add_registry(
            "same-worktree-case",
            status="active",
            branch="feature/other",
            worktree=drive_variant.replace("\\", "/"),
            allowed_paths=["docs/other.md"],
        )

        code, payload = self.run_audit()
        self.assertEqual(1, code)
        self.assert_has_finding(payload, "registry:same-worktree-case", evidence="worktree", relevance="related", actionability="stop", severity="high")

    def test_current_registry_mismatches_are_related_stop_findings(self):
        self.fixture.add_registry(
            "current-task",
            status="archived",
            branch="feature/other",
            worktree=str(self.fixture.root / "other-worktree"),
            allowed_paths=["docs/other.md"],
            forbidden_paths=["src/**"],
        )

        code, payload = self.run_audit()
        self.assertEqual(1, code)
        self.assertTrue(payload["registry"]["current_found"])
        for expected in (
            "current registry status must be active",
            "current registry branch mismatch",
            "current registry worktree mismatch",
            "task path not covered by current allowed_paths: src/current.py",
            "task path matches current forbidden_paths: src/current.py",
        ):
            self.assert_has_finding(payload, "registry:current-task", evidence=expected, relevance="related", actionability="stop", severity="high")

    def test_duplicate_registry_handoff_id_is_incomplete(self):
        self.fixture.add_registry_file("duplicate-current.md", "current-task", status="active", allowed_paths=["docs/other.md"])

        code, payload = self.run_audit()
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        self.assertTrue(payload["registry"]["current_found"])
        self.assert_has_finding(payload, "registry:current-task", evidence="duplicate handoff_id", relevance="related", actionability="stop", severity="high")

    def test_old_last_verified_date_is_not_stale_by_time_threshold(self):
        self.fixture.add_registry(
            "old-but-valid",
            status="archived",
            allowed_paths=["docs/old.md"],
            last_verified="2000-01-01T00:00:00Z",
        )
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertFalse(any("old-but-valid" in item["subject"] for item in payload["findings"]))

    def test_legacy_registry_plain_yaml_mapping_is_accepted(self):
        write_text(self.fixture.registry_dir / "current-task.md", plain_yaml_mapping({
            "status": "active",
            "target": "Current task",
            "handoff_id": "current-task",
            "parent_handoff_id": "parent-task",
            "branch": self.fixture.branch,
            "worktree": str(self.fixture.worktree),
            "allowed_paths": ["src/current.py"],
            "forbidden_paths": ["runtime/**"],
            "updated_at": "2026-07-12T00:00:00+08:00",
            "last_verified": "2026-07-12T00:00:00+08:00",
        }))

        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertTrue(payload["registry"]["current_found"])
        self.assertIn("current-task", payload["registry"]["checked"])
        self.assertFalse(payload["findings"])

    def test_legacy_registry_metadata_header_with_notes_body_is_accepted(self):
        metadata = plain_yaml_mapping({
            "status": "active",
            "target": "Current task",
            "handoff_id": "current-task",
            "parent_handoff_id": "parent-task",
            "branch": self.fixture.branch,
            "worktree": str(self.fixture.worktree),
            "allowed_paths": ["src/current.py"],
            "forbidden_paths": ["runtime/**"],
            "updated_at": "2026-07-12T00:00:00+08:00",
            "last_verified": "2026-07-12T00:00:00+08:00",
        })
        write_text(
            self.fixture.registry_dir / "current-task.md",
            metadata + "\nNotes:\n- Reviewed: `handoff_id` and `status` stay readable.\n",
        )

        code, payload = self.run_audit()
        self.assertEqual(0, code, payload["findings"])
        self.assertTrue(payload["registry"]["current_found"])
        self.assertIn("current-task", payload["registry"]["checked"])
        self.assertFalse(payload["findings"])

    def test_delimiter_free_markdown_or_invalid_yaml_registry_is_incomplete(self):
        write_text(self.fixture.registry_dir / "notes.md", "# Notes\nThis is ordinary Markdown, not a registry mapping.\n")
        write_text(self.fixture.registry_dir / "invalid-plain.md", "status: [unterminated\n")

        code, payload = self.run_audit()
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        self.assert_has_finding(payload, "registry:notes.md", relevance="related", actionability="stop", severity="high")
        self.assert_has_finding(payload, "registry:invalid-plain.md", relevance="related", actionability="stop", severity="high")


class HandoffDagTests(AuditTestCase):
    def test_missing_parent_cycle_and_conflicting_related_active_leaves(self):
        self.fixture.add_handoff("missing-parent-child", status="in_progress", parent_handoff_id="missing-parent", allowed_paths=["src/current.py"])
        self.fixture.add_handoff("cycle-a", status="in_progress", parent_handoff_id="cycle-b", allowed_paths=["src/current.py"])
        self.fixture.add_handoff("cycle-b", status="in_progress", parent_handoff_id="cycle-a", allowed_paths=["src/current.py"])
        self.fixture.add_handoff("leaf-a", status="in_progress", parent_handoff_id="parent-task", allowed_paths=["src/current.py"])
        self.fixture.add_handoff("leaf-b", status="continuation_started", parent_handoff_id="parent-task", allowed_paths=["src/current.py"])
        code, payload = self.run_audit()
        self.assertEqual(1, code)
        subjects = {item["subject"] for item in payload["findings"]}
        self.assertIn("handoff:missing-parent-child", subjects)
        self.assertIn("handoff:cycle-a", subjects)
        self.assertIn("handoff:parent-task", subjects)
        parent_finding = next(item for item in payload["findings"] if item["subject"] == "handoff:parent-task")
        self.assertEqual("related", parent_finding["task_relevance"])
        self.assertEqual("stop", parent_finding["actionability"])

    def test_terminal_parent_with_active_child_is_normal_lineage(self):
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertEqual(["current-task"], payload["handoffs"]["active_leaves"])
        self.assertFalse(payload["findings"])

    def test_string_none_parent_is_treated_as_root(self):
        self.fixture.add_handoff(
            "root-string-none",
            status="complete",
            parent_handoff_id="none",
            allowed_paths=["docs/old.md"],
        )

        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertFalse(any("missing parent handoff: none" in item["evidence"] for item in payload["findings"]))

    def test_related_nonterminal_leaves_conflict_across_dag(self):
        self.fixture.add_handoff(
            "other-parent",
            status="complete",
            parent_handoff_id=None,
            allowed_paths=["docs/old.md"],
        )
        self.fixture.add_handoff(
            "other-active-leaf",
            status="continuation_started",
            parent_handoff_id="other-parent",
            allowed_paths=["src/current.py"],
        )

        code, payload = self.run_audit()
        self.assertEqual(1, code)
        finding = self.assert_has_finding(payload, "handoff:active_leaves", evidence="multiple related nonterminal leaves", relevance="related", actionability="stop", severity="high")
        self.assertIn("current-task", finding["evidence"])
        self.assertIn("other-active-leaf", finding["evidence"])

    def test_partial_emergency_is_nonterminal_and_participates_in_leaf_conflicts(self):
        self.fixture.add_handoff(
            "emergency-leaf",
            status="partial_emergency",
            parent_handoff_id="parent-task",
            allowed_paths=["src/current.py"],
        )

        code, payload = self.run_audit()
        self.assertEqual(1, code)
        self.assertFalse(any(
            item["subject"] == "handoff:emergency-leaf" and "unknown handoff status" in item["evidence"]
            for item in payload["findings"]
        ))
        self.assertIn("emergency-leaf", payload["handoffs"]["active_leaves"])
        finding = self.assert_has_finding(payload, "handoff:parent-task", evidence="multiple related nonterminal leaves", relevance="related", actionability="stop", severity="high")
        self.assertIn("current-task", finding["evidence"])
        self.assertIn("emergency-leaf", finding["evidence"])

    def test_duplicate_handoff_id_is_incomplete(self):
        self.fixture.add_handoff_file(
            "duplicate-current.md",
            "current-task",
            status="in_progress",
            parent_handoff_id="parent-task",
            allowed_paths=["docs/other.md"],
        )

        code, payload = self.run_audit()
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        self.assert_has_finding(payload, "handoff:current-task", evidence="duplicate handoff_id", relevance="related", actionability="stop", severity="high")

    def test_terminal_statuses_only_come_from_cli_and_registry_active_is_separate(self):
        args = []
        source = self.fixture.args()
        skip_next_terminal = False
        for item in source:
            if skip_next_terminal:
                skip_next_terminal = False
                continue
            if item == "--terminal-status":
                skip_next_terminal = True
                continue
            args.append(item)
        args.extend(["--terminal-status", "done"])
        code, payload = self.run_audit(args=args)
        self.assertEqual(1, code)
        subjects = {item["subject"] for item in payload["findings"]}
        self.assertIn("handoff:parent-task", subjects)
        self.assertNotIn("registry:current-task", subjects)

    def test_known_nonterminal_statuses_are_not_unknown(self):
        for status in ("initial_marker", "continuation_started", "in_progress"):
            with self.subTest(status=status):
                self.fixture.add_handoff(f"known-{status}", status=status, parent_handoff_id="parent-task", allowed_paths=["docs/unrelated.md"])
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertFalse(any("known-" in item["subject"] for item in payload["findings"]))


class ManualTests(AuditTestCase):
    def test_manual_exact_and_normalized_hashes_distinguish_newline_and_content_drift(self):
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        primary = payload["manuals"]["primary"]
        backup = payload["manuals"]["backup"]
        self.assertNotEqual(primary["exact_sha256"], backup["exact_sha256"])
        self.assertEqual(primary["normalized_sha256"], backup["normalized_sha256"])
        self.assertFalse(payload["findings"])

        write_text(self.fixture.manual_b, "# Manual\nchanged\n")
        code, payload = self.run_audit()
        self.assertEqual(1, code)
        finding = next(item for item in payload["findings"] if item["subject"] == "manuals")
        self.assertEqual("related", finding["task_relevance"])
        self.assertEqual("stop", finding["actionability"])

    def test_manual_argument_and_utf8_errors_are_incomplete(self):
        bad_manual = self.fixture.root / "bad-manual.md"
        bad_manual.write_bytes(b"\xff")
        code, payload = self.run_audit(args=[
            *self.fixture.args("--manual", f"bad={bad_manual}"),
        ])
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        code, payload = self.run_audit(args=[
            *self.fixture.args("--manual", str(self.fixture.manual_a)),
        ])
        self.assertEqual(2, code)
        self.assertTrue(any(item["subject"] == "manual" for item in payload["findings"]))

    def test_duplicate_or_empty_manual_logical_names_are_incomplete(self):
        cases = (
            (
                "duplicate",
                self.fixture.args("--manual", f"primary={self.fixture.manual_b}"),
                "manual:primary",
                "duplicate manual logical name: primary",
            ),
            (
                "empty",
                self.fixture.args("--manual", f"={self.fixture.manual_a}"),
                "manual",
                "manual logical name must be non-empty",
            ),
        )
        for label, args, subject, evidence in cases:
            with self.subTest(label=label):
                code, payload = self.run_audit(args=args)
                self.assertEqual(2, code)
                self.assertFalse(payload["complete"])
                self.assert_has_finding(payload, subject, evidence=evidence, relevance="related", actionability="stop", severity="high")


class PorTests(AuditTestCase):
    def test_por_absent_is_explicit_status_not_valid(self):
        self.fixture.por.unlink()
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        self.assertEqual("absent", payload["por"]["status"])
        self.assertFalse(payload["findings"])

    def test_por_validator_exit_codes_map_to_four_states_and_incomplete(self):
        for validator_exit, expected_code, expected_status in (
            (0, 0, "valid"),
            (1, 1, "invalid"),
            (3, 1, "stale"),
        ):
            with self.subTest(validator_exit=validator_exit):
                self.fixture.write_validator(validator_exit)
                code, payload = self.run_audit()
                self.assertEqual(expected_code, code)
                self.assertEqual(expected_status, payload["por"]["status"])
        for validator_exit in (2, 9):
            with self.subTest(validator_exit=validator_exit):
                self.fixture.write_validator(validator_exit)
                code, payload = self.run_audit()
                self.assertEqual(2, code)
                self.assertFalse(payload["complete"])
                self.assertEqual("incomplete", payload["por"]["status"])

    def test_por_validator_uses_python_b_and_argv_list(self):
        self.fixture.write_validator(0, writes_seen=True)
        code, payload = self.run_audit()
        self.assertEqual(0, code)
        argv = json.loads(self.fixture.seen.read_text(encoding="utf-8"))
        self.assertEqual(str(self.fixture.validator), argv[0])
        self.assertIn(str(self.fixture.por), argv)
        self.assertIn(str(self.fixture.repo), argv)
        self.assertIn(str(self.fixture.por_schema), argv)
        self.assertEqual("valid", payload["por"]["status"])
        self.assertFalse(any(path.name == "__pycache__" for path in self.fixture.root.rglob("__pycache__")))

    def test_por_startup_failure_is_incomplete(self):
        self.fixture.validator.unlink()
        code, payload = self.run_audit()
        self.assertEqual(2, code)
        self.assertFalse(payload["complete"])
        self.assertEqual("incomplete", payload["por"]["status"])


if __name__ == "__main__":
    unittest.main()
