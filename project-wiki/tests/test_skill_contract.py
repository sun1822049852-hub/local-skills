import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
MAP_TEMPLATE = ROOT / "assets" / "PROJECT_MAP.md"
TOPIC_TEMPLATE = ROOT / "assets" / "wiki-topic.md"
SCENARIOS = ROOT / "tests" / "scenarios.md"
FORWARD_FIXTURE = ROOT / "tests" / "fixtures" / "PROJECT_MAP.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SkillPackagingTests(unittest.TestCase):
    def test_skill_is_valid_compact_utf8(self):
        raw = SKILL.read_bytes()
        text = raw.decode("utf-8")
        self.assertTrue(raw.startswith(b"---\n"))
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertRegex(text, r"(?s)^---\nname: project-wiki\ndescription: .+\n---\n")
        self.assertLessEqual(len(re.findall(r"\S+", text)), 500)

    def test_root_template_has_budget_and_required_orientation(self):
        raw = MAP_TEMPLATE.read_bytes()
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

    def test_topic_template_preserves_evidence_and_gaps(self):
        text = read(TOPIC_TEMPLATE)
        for marker in [
            "When to read",
            "Current Behavior",
            "Source Refs",
            "Stable symbol/section",
            "Invariants",
            "Verification",
            "Known gaps or stale claims",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_forward_fixture_is_bounded_and_references_real_sources(self):
        raw = FORWARD_FIXTURE.read_bytes()
        text = raw.decode("utf-8")
        self.assertLessEqual(len(raw), 8 * 1024)
        self.assertLessEqual(len(text.splitlines()), 150)
        self.assertIn("Test-only fixture", text)
        if ROOT.parent.name != "skills-local":
            return
        repo_root = ROOT.parents[1]
        for relative_path in [
            "AGENTS.md",
            "workflow-manual.md",
            "working-principles.md",
            "skills-local",
            "skills",
            "docs/validation/workflow-validation",
            "opencode-config",
        ]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((repo_root / relative_path).exists())


class ScenarioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = read(SKILL)
        cls.scenarios = read(SCENARIOS)

    def test_empty_and_existing_project_behavior(self):
        for marker in [
            "empty or evidence-poor repository",
            "never invent modules, commands, or flows",
            "existing root map as the first orientation source",
            "directly relevant current sources",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)
        self.assertIn("## Empty Repository", self.scenarios)
        self.assertIn("## Existing Repository", self.scenarios)

    def test_dirty_unmapped_and_stale_diff_behavior(self):
        for marker in [
            "record dirty state",
            "staged, and working changes",
            "validate `base-ref`",
            "proven merge-base",
            "changed path cannot be mapped",
            "explicit gap",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)
        for heading in [
            "## Dirty Worktree",
            "## Unmapped Diff",
            "## Stale Or Missing Base Ref",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.scenarios)

    def test_update_classifies_added_modified_and_deleted_paths(self):
        for marker in ["added paths", "modified paths", "deleted paths"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)

    def test_add_is_root_first_and_splits_only_after_threshold(self):
        skill = self.skill.lower()
        self.assertIn("add the topic to the root", skill)
        self.assertIn("split it only when", skill)
        self.assertNotIn("add one focused `docs/wiki/NN-topic.md`", self.skill)

    def test_split_threshold_is_progressive(self):
        for marker in ["8 KB", "40 lines", "repeatedly", "Do not pre-create"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)
        self.assertIn("## Topic Split", self.scenarios)

    def test_sensitive_information_is_excluded(self):
        for marker in ["secrets", "private URLs", "payloads", "personal data"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)
        self.assertIn("## Sensitive Evidence", self.scenarios)

    def test_stale_refs_and_verified_deletion_are_distinct(self):
        for marker in [
            "Recheck every affected source reference",
            "mark it stale",
            "source deletion is verified",
            "remove its claim",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)
        self.assertIn("## Source Deletion", self.scenarios)

    def test_module_agents_and_vom_boundaries_are_narrow(self):
        for marker in [
            "local hard constraints that differ from the parent",
            "5-10 lines",
            "truth/projection/observation",
            "navigation, never authority",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.skill)


if __name__ == "__main__":
    unittest.main()
