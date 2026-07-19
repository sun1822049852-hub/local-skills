import ast
import re
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
IS_REPOSITORY_LAYOUT = TEST_FILE.parents[2].name == "skills-local"

if IS_REPOSITORY_LAYOUT:
    REPO_ROOT = TEST_FILE.parents[3]
    AGENTS = REPO_ROOT / "AGENTS.md"
    MANUAL = REPO_ROOT / "workflow-manual.md"
    PRINCIPLES = REPO_ROOT / "working-principles.md"
    LOCAL_SKILLS = REPO_ROOT / "skills-local"
    VOM_SKILL = REPO_ROOT / "skills" / "verified-operation-map" / "SKILL.md"
else:
    HOME = Path.home()
    AGENTS = HOME / ".codex" / "AGENTS.md"
    MANUAL = HOME / "Desktop" / "Codex 工作流说明书.md"
    PRINCIPLES = HOME / ".codex" / "working-principles.md"
    LOCAL_SKILLS = HOME / ".agents" / "skills" / "local"
    VOM_SKILL = HOME / ".codex" / "skills" / "verified-operation-map" / "SKILL.md"

START_GATE = LOCAL_SKILLS / "coding-session-start-gate" / "SKILL.md"
SAVE_HANDOFF = LOCAL_SKILLS / "save-status-handoff" / "SKILL.md"
RESUME_HANDOFF = LOCAL_SKILLS / "resume-from-handoff" / "SKILL.md"
HANDOFF_REFERENCE = LOCAL_SKILLS / "save-status-handoff" / "references" / "handoff-schema.md"
PROJECT_WIKI = LOCAL_SKILLS / "project-wiki"
AUDIT_SCRIPT = LOCAL_SKILLS / "coding-session-start-gate" / "scripts" / "audit_workflow_state.py"


def read(path: Path, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)


def word_count(path: Path) -> int:
    return len(re.findall(r"\S+", read(path)))


class AlwaysOnBudgetTests(unittest.TestCase):
    def test_agents_is_utf8_bom_and_within_startup_budget(self):
        raw = AGENTS.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertLessEqual(len(raw), 10 * 1024)
        self.assertLessEqual(len(raw.decode("utf-8-sig").splitlines()), 60)

    def test_agents_no_longer_requires_public_routing_json(self):
        text = read(AGENTS, "utf-8-sig")
        for obsolete in ["six routing fields", "`must_use`", "workflow_state_findings"]:
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, text)
        self.assertIn("silent", text.lower())


class StartGateTests(unittest.TestCase):
    def test_start_gate_is_small_and_silent_on_success(self):
        text = read(START_GATE)
        self.assertLessEqual(word_count(START_GATE), 200)
        self.assertNotIn("```json", text)
        self.assertNotIn('"must_use"', text)
        self.assertRegex(text, r"(?i)silent|不输出")

    def test_start_gate_preserves_multi_session_protection(self):
        text = read(START_GATE)
        required = [
            "git rev-parse --show-toplevel",
            "git worktree list --porcelain",
            "git status --short",
            "PROJECT_MAP.md",
            "active registry",
            "dirty",
            "allowed_paths",
            "forbidden_paths",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_audit_is_only_for_observable_escalation(self):
        text = read(START_GATE)
        required = [
            "multiple active",
            "resume lineage",
            "explicit audit",
            "release",
            "scripts/audit_workflow_state.py",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertRegex(text, r"(?i)do not run|不运行")

    def test_registry_fields_match_audit_required_contract(self):
        start = read(START_GATE)
        tree = ast.parse(read(AUDIT_SCRIPT))
        required = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "REGISTRY_REQUIRED"
                for target in node.targets
            ):
                required = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(required)
        for field in sorted(required):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", start)


class HandoffTests(unittest.TestCase):
    def test_common_handoff_skills_are_compact(self):
        self.assertLessEqual(word_count(SAVE_HANDOFF), 250)
        self.assertLessEqual(word_count(RESUME_HANDOFF), 250)

    def test_default_handoff_shape_and_advanced_reference_exist(self):
        text = read(SAVE_HANDOFF)
        for marker in [
            "Goal:",
            "Done:",
            "Current:",
            "Next:",
            "Blockers:",
            "Verified:",
            "Must not change:",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        reference = read(HANDOFF_REFERENCE)
        for marker in ["parent_handoff_id", "initial_marker", "partial_emergency", "continuation_started"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, reference)

    def test_default_handoff_includes_required_metadata(self):
        text = read(SAVE_HANDOFF)
        for marker in ["created_at:", "project_root:", "task:"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)


class ProjectWikiTests(unittest.TestCase):
    def test_skill_and_interface_exist(self):
        skill = read(PROJECT_WIKI / "SKILL.md")
        for marker in ["project-wiki", "init", "read", "update", "add"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        self.assertLessEqual(word_count(PROJECT_WIKI / "SKILL.md"), 500)

    def test_project_map_template_is_small_and_complete(self):
        template = PROJECT_WIKI / "assets" / "PROJECT_MAP.md"
        raw = template.read_bytes()
        text = raw.decode("utf-8")
        self.assertLessEqual(len(raw), 8 * 1024)
        self.assertLessEqual(len(text.splitlines()), 150)
        for marker in [
            "Purpose And Stack",
            "Start And Verify",
            "Core Modules",
            "State Owners",
            "Key Flows",
            "Known Traps",
            "Wiki Index",
            "Verification And Gaps",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_skill_uses_progressive_expansion_and_stable_refs(self):
        skill = read(PROJECT_WIKI / "SKILL.md")
        for marker in ["8 KB", "40 lines", "repeatedly", "symbol", "source wins"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        self.assertNotIn("14", skill)
        self.assertNotRegex(skill, r"(?i)never delete|永不删除")
        self.assertRegex(skill, r"(?i)line number|行号")

    def test_topic_template_and_module_agents_boundary_exist(self):
        topic = read(PROJECT_WIKI / "assets" / "wiki-topic.md")
        for marker in ["When to read", "Current Behavior", "Source Refs", "Invariants", "Verification"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, topic)
        skill = read(PROJECT_WIKI / "SKILL.md")
        self.assertIn("5-10 lines", skill)
        self.assertRegex(skill, r"(?i)local hard constraints|局部硬约束")

    def test_update_and_add_have_unambiguous_write_targets(self):
        skill = read(PROJECT_WIKI / "SKILL.md")
        for marker in ["added paths", "modified paths", "deleted paths"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        self.assertIn("add the topic to the root", skill.lower())
        self.assertIn("split it only when", skill.lower())


class MirrorParityTests(unittest.TestCase):
    def test_owned_canonical_and_live_assets_match(self):
        canonical = Path.home() / "codex-working-rules"
        if not canonical.is_dir():
            self.skipTest("default canonical rules repository is absent")
        if IS_REPOSITORY_LAYOUT and REPO_ROOT.resolve() != canonical.resolve():
            self.skipTest("non-default repository checkout does not own live mirrors")

        home = Path.home()
        manifest = [
            (canonical / "AGENTS.md", home / ".codex" / "AGENTS.md"),
            (canonical / "working-principles.md", home / ".codex" / "working-principles.md"),
            (canonical / "workflow-manual.md", home / "Desktop" / "Codex 工作流说明书.md"),
            *[
                (
                    canonical / "skills-local" / relative,
                    home / ".agents" / "skills" / "local" / relative,
                )
                for relative in [
                    Path("coding-session-start-gate/SKILL.md"),
                    Path("coding-session-start-gate/tests/test_skill_contract.py"),
                    Path("coding-session-start-gate/tests/test_knowledge_first_contract.py"),
                    Path("resume-from-handoff/SKILL.md"),
                    Path("save-status-handoff/SKILL.md"),
                    Path("save-status-handoff/references/handoff-schema.md"),
                    Path("project-wiki/SKILL.md"),
                    Path("project-wiki/agents/openai.yaml"),
                    Path("project-wiki/assets/PROJECT_MAP.md"),
                    Path("project-wiki/assets/wiki-topic.md"),
                    Path("project-wiki/tests/scenarios.md"),
                    Path("project-wiki/tests/test_skill_contract.py"),
                    Path("project-wiki/tests/fixtures/PROJECT_MAP.md"),
                ]
            ],
            *[
                (
                    canonical / "skills" / "verified-operation-map" / relative,
                    home / ".codex" / "skills" / "verified-operation-map" / relative,
                )
                for relative in [
                    Path("SKILL.md"),
                    Path("agents/openai.yaml"),
                    Path("tests/test_skill_contract.py"),
                ]
            ],
        ]

        for source, live in manifest:
            with self.subTest(source=source, live=live):
                self.assertTrue(source.is_file(), f"missing canonical asset: {source}")
                self.assertTrue(live.is_file(), f"missing live asset: {live}")
                self.assertEqual(source.read_bytes(), live.read_bytes())


class MapLayeringTests(unittest.TestCase):
    def test_general_project_map_precedes_high_risk_vom(self):
        manual = read(MANUAL, "utf-8-sig")
        principles = read(PRINCIPLES, "utf-8-sig")
        vom = read(VOM_SKILL)
        for text in [manual, principles]:
            self.assertIn("PROJECT_MAP.md", text)
            self.assertIn("project-wiki", text)
        for marker in ["high-risk", "truth", "projection", "observation"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, vom)
        self.assertRegex(vom, r"(?i)not.*general project|不是.*通用项目")
        self.assertNotIn("A broad VOM umbrella", principles)
        self.assertIn("已满足高风险触发后", manual)

    def test_maturity_radar_names_all_changed_workflow_assets(self):
        principles = read(PRINCIPLES, "utf-8-sig")
        radar = principles.split("#### Rule Change Maturity Radar", 1)[1].split(
            "#### External Constraint Baseline", 1
        )[0]
        for marker in [
            "project-wiki",
            "coding-session-start-gate",
            "save-status-handoff",
            "resume-from-handoff",
            "verified-operation-map",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, radar)


if __name__ == "__main__":
    unittest.main()
