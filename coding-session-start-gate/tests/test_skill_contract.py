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
    VOM = REPO_ROOT / "skills" / "verified-operation-map" / "SKILL.md"
else:
    HOME = Path.home()
    AGENTS = HOME / ".codex" / "AGENTS.md"
    MANUAL = HOME / "Desktop" / "Codex 工作流说明书.md"
    PRINCIPLES = HOME / ".codex" / "working-principles.md"
    LOCAL_SKILLS = HOME / ".agents" / "skills" / "local"
    VOM = HOME / ".codex" / "skills" / "verified-operation-map" / "SKILL.md"

START_GATE = LOCAL_SKILLS / "coding-session-start-gate" / "SKILL.md"
SAVE_HANDOFF = LOCAL_SKILLS / "save-status-handoff" / "SKILL.md"
RESUME_HANDOFF = LOCAL_SKILLS / "resume-from-handoff" / "SKILL.md"
HANDOFF_REFERENCE = (
    LOCAL_SKILLS / "save-status-handoff" / "references" / "handoff-schema.md"
)
PROJECT_WIKI = LOCAL_SKILLS / "project-wiki" / "SKILL.md"
AUDIT_SCRIPT = LOCAL_SKILLS / "coding-session-start-gate" / "scripts" / "audit_workflow_state.py"


def read(path: Path, encoding: str = "utf-8") -> str:
    if not path.is_file():
        raise FileNotFoundError(f"required workflow asset is missing: {path}")
    return path.read_text(encoding=encoding)


def words(path: Path) -> int:
    return len(re.findall(r"\S+", read(path)))


class EncodingAndBudgetTests(unittest.TestCase):
    def test_agents_is_compact_utf8_bom(self):
        raw = AGENTS.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8-sig")
        self.assertLessEqual(len(raw), 10 * 1024)
        self.assertLessEqual(len(text.splitlines()), 60)

    def test_skill_files_have_frontmatter_without_bom(self):
        for path in [START_GATE, SAVE_HANDOFF, RESUME_HANDOFF, PROJECT_WIKI, VOM]:
            with self.subTest(path=path):
                raw = path.read_bytes()
                self.assertTrue(raw.startswith(b"---\n"))
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
                text = raw.decode("utf-8")
                self.assertRegex(text, r"(?s)^---\nname: .+\ndescription: .+\n---\n")
                self.assertTrue(text.endswith("\n"))
                self.assertFalse(text.endswith("\n\n"))

    def test_common_entry_skills_are_small(self):
        self.assertLessEqual(words(START_GATE), 200)
        self.assertLessEqual(words(SAVE_HANDOFF), 250)
        self.assertLessEqual(words(RESUME_HANDOFF), 250)


class AlwaysOnProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agents = read(AGENTS, "utf-8-sig")

    def assert_markers(self, markers):
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.agents.lower())

    def test_scope_security_and_runtime_contracts_remain(self):
        self.assert_markers(
            [
                "Chinese/plain language",
                "must-not-change",
                "Hardware target is immutable",
                "secrets",
                "PowerShell",
                "UTF-8 BOM",
                "SKILL.md",
                "prerequisite",
                "paramiko",
            ]
        )

    def test_worktree_registry_and_git_authority_remain(self):
        self.assert_markers(
            [
                "git rev-parse --show-toplevel",
                "git worktree list --porcelain",
                "git status --short",
                "active registry",
                "allowed_paths",
                "forbidden_paths",
                "dirty overlap",
                "Never commit, push, stash, clean, reset, checkout, merge",
                "explicit user authority",
            ]
        )

    def test_knowledge_evidence_state_and_architecture_remain(self):
        self.assert_markers(
            [
                "PROJECT_MAP.md",
                "VOM/POR",
                "high-risk",
                "live evidence",
                "truth",
                "projection/cache",
                "Cross-context",
                "architecture baseline",
            ]
        )

    def test_resume_subagent_review_and_completion_remain(self):
        self.assert_markers(
            [
                "Never rely on auto compact",
                "Resume is read-only first",
                "explicit approval",
                "Codex Ultra",
                "Verification",
                "actual coverage",
                "Completion",
                "No commit or push is implied",
            ]
        )


class SilentRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start = read(START_GATE)

    def test_success_path_is_silent_and_has_no_public_json_contract(self):
        self.assertIn("continue silently", self.start)
        self.assertIn("do not emit routing JSON", self.start)
        for obsolete in ["```json", '"must_use"', "workflow_state_findings"]:
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, self.start)

    def test_start_checks_and_stop_conditions_remain(self):
        for marker in [
            "git rev-parse --show-toplevel",
            "git worktree list --porcelain",
            "git status --short",
            "PROJECT_MAP.md",
            "active registry",
            "dirty overlap",
            "allowed_paths",
            "forbidden_paths",
            "resume approval",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.start)

    def test_audit_is_available_but_risk_triggered(self):
        self.assertTrue(AUDIT_SCRIPT.is_file())
        self.assertIn("Do not run", self.start)
        for marker in [
            "multiple active registries",
            "resume lineage conflict",
            "explicit audit request",
            "release/final full audit",
            "Exit 2",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.start)


class RelocatedDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manual = read(MANUAL, "utf-8-sig")
        cls.principles = read(PRINCIPLES, "utf-8-sig")
        cls.handoff = read(HANDOFF_REFERENCE)
        cls.combined = "\n".join([cls.manual, cls.principles, cls.handoff])

    def test_detailed_safety_contracts_are_still_locatable(self):
        for marker in [
            "Live Evidence To Contract Gate",
            "Consumer State Convergence",
            "Cross-Context Wakeup",
            "Handoff Resume Approval Gate",
            "Completion Commit Reminder",
            "Rule Change Maturity Radar",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.combined)
        self.assertRegex(
            self.combined.lower(), r"verification[- ]before[- ]completion"
        )
        self.assertIn("同步检查这份说明书", self.manual)
        self.assertIn("同步到桌面版", self.manual)

    def test_handoff_lineage_and_emergency_details_moved_to_reference(self):
        for marker in [
            "parent_handoff_id",
            "initial_marker",
            "continuation_started",
            "partial_emergency",
            "explicit user approval",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.handoff)

    def test_project_map_is_general_and_vom_is_specialized(self):
        combined = "\n".join([self.manual, self.principles])
        self.assertIn("PROJECT_MAP.md", combined)
        self.assertIn("project-wiki", combined)
        vom = read(VOM)
        for marker in ["high-risk", "truth", "projection", "observation"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, vom)
        self.assertRegex(vom, r"(?i)not.*general project|不是.*通用项目")


if __name__ == "__main__":
    unittest.main()
