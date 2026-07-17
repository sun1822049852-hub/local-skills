import json
import re
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def require_contract_files(agents, manual, layout_name):
    missing = [str(path) for path in (agents, manual) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            f"{layout_name} missing contract file(s): {', '.join(missing)}"
        )
    return agents, manual


def resolve_contract_files():
    test_file = Path(__file__).resolve()
    if test_file.parents[2].name == "skills-local":
        repo_root = test_file.parents[3]
        return require_contract_files(
            repo_root / "AGENTS.md",
            repo_root / "workflow-manual.md",
            "repository layout",
        )

    if test_file.parents[2].name == "local" and test_file.parents[3].name == "skills":
        home = Path.home()
        return require_contract_files(
            home / ".codex" / "AGENTS.md",
            home / "Desktop" / "Codex 工作流说明书.md",
            "installed live layout",
        )

    repo_root = test_file.parents[3]
    return require_contract_files(
        repo_root / "AGENTS.md",
        repo_root / "workflow-manual.md",
        "repository layout",
    )


AGENTS, WORKFLOW_MANUAL = resolve_contract_files()
SELECTOR_HEADING = "## 2. Unified Workflow Selector / 统一工作流选择器"
REQUIRED_ROUTING_KEYS = [
    "must_use",
    "conditional",
    "not_triggered",
    "first_required_action",
    "stop_or_ask_conditions",
    "workflow_state_findings",
]
EARLY_SELECTOR_MARKERS = [
    "Rule Placement Fast Gate",
    "Coding Session Start Gate",
    "Known-Change Debugging",
    "Live Evidence To Contract Gate",
    "Consumer State Convergence Gate",
    "Cross-Context Wakeup And Delivery Gate",
    "Subagent Dispatch And Lifecycle",
    "Architecture Baseline And Learning Loop",
    "Workflow Discovery",
    "Direction Challenge And Red-Team Review",
    "Workflow Manual Sync",
    "Constraint Benchmarking",
    "Context Budget And Auto Compact Ban",
    "Handoff Resume Approval Gate",
    "Verification Before Completion",
    "Completion Commit Reminder",
    "Verified Operation Map",
    "Code Review Scope",
]


def agents_bytes():
    return AGENTS.read_bytes()


def agents_text():
    return agents_bytes().decode("utf-8-sig")


def manual_text():
    return WORKFLOW_MANUAL.read_text(encoding="utf-8-sig")


def markdown_section(text, heading):
    start = text.index(heading)
    next_heading = re.search(r"(?m)^## ", text[start + len(heading) :])
    if not next_heading:
        return text[start:]
    return text[start : start + len(heading) + next_heading.start()]


def skill_text():
    return SKILL.read_text(encoding="utf-8")


def routing_contract_blocks():
    blocks = []
    for match in re.finditer(r"```json\s*(.*?)```", skill_text(), flags=re.DOTALL):
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and set(parsed) == set(REQUIRED_ROUTING_KEYS):
            blocks.append(parsed)
    return blocks


class SkillContractTests(unittest.TestCase):
    def test_skill_file_is_utf8_without_bom_with_frontmatter(self):
        raw = SKILL.read_bytes()
        self.assertEqual(raw[:3], b"---")
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8")
        lines = text.splitlines()
        self.assertEqual(lines[0], "---")
        self.assertIn("name: coding-session-start-gate", lines)
        self.assertTrue(any(line.startswith("description: ") for line in lines))

    def test_skill_file_uses_one_newline_style_without_bom(self):
        raw = SKILL.read_bytes()
        self.assertEqual(raw[:3], b"---")
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        raw.decode("utf-8")
        crlf_count = raw.count(b"\r\n")
        bare_lf_count = raw.count(b"\n") - crlf_count
        bare_cr_count = raw.count(b"\r") - crlf_count
        self.assertGreater(crlf_count + bare_lf_count + bare_cr_count, 0)
        used_styles = sum(count > 0 for count in (crlf_count, bare_lf_count, bare_cr_count))
        self.assertEqual(
            used_styles,
            1,
            f"mixed newline styles: crlf={crlf_count}, bare_lf={bare_lf_count}, bare_cr={bare_cr_count}",
        )

    def test_routing_contract_template_has_exact_six_keys_once(self):
        blocks = routing_contract_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(list(blocks[0]), REQUIRED_ROUTING_KEYS)

    def test_routing_contract_template_is_neutral_until_evidence_populates_it(self):
        block = routing_contract_blocks()[0]
        self.assertEqual(block["must_use"], ["Coding Session Start Gate"])
        self.assertEqual(block["conditional"], [])
        self.assertEqual(block["not_triggered"], [])
        self.assertEqual(block["stop_or_ask_conditions"], [])

        first_action = block["first_required_action"]
        self.assertIsInstance(first_action, str)
        self.assertIn("placeholder", first_action.lower())
        self.assertNotIn("run start-gate read-only checks", first_action)
        self.assertNotIn("stop/ask", first_action)

        workflow_state = block["workflow_state_findings"]
        self.assertIsInstance(workflow_state, dict)
        self.assertIn("placeholder", workflow_state["audit_exit"].lower())
        self.assertEqual(workflow_state["related_stop_findings"], [])
        self.assertEqual(workflow_state["unrelated_warnings"], [])
        self.assertEqual(len(workflow_state["evidence"]), 1)
        self.assertIn("placeholder", workflow_state["evidence"][0].lower())
        self.assertIn("concrete reason/evidence", workflow_state["evidence"][0])

        serialized = json.dumps(block, ensure_ascii=False)
        forbidden_seeded_claims = [
            "Known-Change Debugging",
            "Live Evidence To Contract Gate",
            "unresolved resume approval",
            "handoff approval gap",
            "related active registry collision",
            "audit exit 2 is incomplete",
            "dirty-overlap ambiguity",
            "missing authority",
        ]
        for claim in forbidden_seeded_claims:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, serialized)

        text = skill_text()
        self.assertRegex(text, r"replace every placeholder")
        self.assertRegex(text, r"populate only[\s\S]{0,120}supported by current task evidence")
        self.assertRegex(text, r"never copy template placeholders")
        self.assertRegex(text, r"potential stop conditions[\s\S]{0,80}facts")

    def test_first_required_action_is_one_scalar_action(self):
        block = routing_contract_blocks()[0]
        action = block["first_required_action"]
        self.assertIsInstance(action, str)
        self.assertNotIn("\n", action)
        self.assertNotRegex(action, r"\b(or|and then|, then)\b")

    def test_canonical_trigger_references_and_plausible_candidate_limits_exist(self):
        text = skill_text()
        required_references = [
            "Handoff Resume Approval Gate",
            "Coding Session Start Gate",
            "Known-Change Debugging",
            "Live Evidence To Contract Gate",
            "Consumer State Convergence Gate",
            "Cross-Context Wakeup And Delivery Gate",
            "Architecture Baseline And Learning Loop",
            "Workflow Discovery",
            "Direction Challenge And Red-Team Review",
            "Rule Placement Gate",
            "Constraint Benchmarking",
            "Workflow Manual Sync",
            "Verified Operation Map",
            "Subagent Dispatch And Lifecycle",
            "Completion Commit Reminder",
        ]
        for reference in required_references:
            with self.subTest(reference=reference):
                self.assertIn(reference, text)
        self.assertRegex(text, r"canonical trigger")
        self.assertRegex(text, r"plausible candidate")
        self.assertRegex(text, r"not_triggered[\s\S]{0,240}not[\s-]+(?:dump|list).*catalog|catalog[\s\S]{0,240}not_triggered")

    def test_low_risk_existing_pattern_fast_path_is_preserved(self):
        text = skill_text()
        for marker in [
            "low-risk",
            "single-goal",
            "existing-pattern",
            "light coding start path",
            "Ordinary verbs",
            "do not activate heavy workflows",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_stop_semantics_cover_resume_collisions_audit_and_authority(self):
        text = skill_text()
        stop_markers = [
            "unresolved resume approval",
            "related active registry collision",
            "branch/worktree/path",
            "audit exit 2",
            "incomplete, never clean",
            "dirty-overlap ambiguity",
            "missing authority",
            "stop/ask",
            "first_required_action",
        ]
        for marker in stop_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertRegex(text, r"Related stop findings[\s\S]{0,160}not be downgraded")
        self.assertRegex(text, r"Unrelated warnings[\s\S]{0,180}without activating unrelated workflows")

    def test_workflow_state_audit_step_is_referenced_and_bounded(self):
        text = skill_text()
        required_markers = [
            "Workflow State Audit",
            "scripts/audit_workflow_state.py",
            "explicit arguments only",
            "read-only/report-only",
            "never fixes, archives, closes, or copies",
            "before finalizing the routing result",
            "resume/continuation",
            "long or multi-agent",
            "workflow/rule/manual/skill/VOM assets",
            "registry/handoff/manual/POR state",
            "audit asset plus explicit inputs are available",
            "does not have to manufacture absent workflow assets",
            "audit_exit=not_run",
            "not applicable",
            "audit asset is unavailable",
            "concrete reason",
            "required explicit inputs are missing",
            "incomplete/stop-or-ask",
            "exit 0",
            "exit 1",
            "exit 2",
            "findings to classify by relevance/actionability",
            "Related stop findings cannot dispatch a writer",
            "unrelated warnings do not activate unrelated workflows",
            "AGENTS.md is the canonical source",
        ]
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertRegex(text, r"exit 2[\s\S]{0,120}incomplete[\s\S]{0,80}stop/ask")

    def test_existing_start_gate_registry_dirty_handoff_and_cleanup_protections_remain(self):
        text = skill_text()
        required_existing_markers = [
            "git rev-parse --show-toplevel",
            "git worktree list --porcelain",
            "git status --short",
            "docs/agent/worktrees/<handoff_id>.md",
            "`status`: `active` / `merged` / `abandoned` / `archived`",
            "`target`",
            "`handoff_id`",
            "`parent_handoff_id`",
            "`branch`",
            "`worktree`",
            "`allowed_paths`",
            "`forbidden_paths`",
            "`updated_at`",
            "`last_verified`",
            "fast-path",
            "已有未提交改动和本轮允许路径不重叠",
            "save-status-handoff",
            "partial_emergency",
            "不默认删除 worktree",
            "用户明确确认",
        ]
        for marker in required_existing_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_agents_global_contract_is_compact_enough_for_early_loading(self):
        raw = agents_bytes()
        self.assertLess(len(raw), 32768, "AGENTS.md must stay below the 32 KiB startup budget including BOM")
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), "AGENTS.md must remain UTF-8 with BOM")

    def test_agents_unified_workflow_selector_and_all_trigger_markers_are_early(self):
        raw = agents_bytes()
        selector_heading = b"Unified Workflow Selector"
        selector_offset = raw.find(selector_heading)
        self.assertNotEqual(selector_offset, -1, "AGENTS.md needs a clearly named unified workflow selector")
        self.assertLess(selector_offset, 10240)

        for marker in EARLY_SELECTOR_MARKERS:
            with self.subTest(marker=marker):
                offset = raw.find(marker.encode("utf-8"))
                self.assertNotEqual(offset, -1)
                self.assertLess(offset, 10240)

        text = agents_text()
        selector_window = markdown_section(text, SELECTOR_HEADING)
        self.assertNotIn("byte 10,240", selector_window)
        self.assertNotIn("Early trigger markers", selector_window)
        for marker in EARLY_SELECTOR_MARKERS:
            with self.subTest(bare_marker=marker):
                self.assertNotRegex(selector_window, rf"(?m)^- {re.escape(marker)}\s*$")

        required_semantics = [
            "six routing fields",
            "only plausible",
            "one first action",
            "low-risk fast-path",
            "coding-session-start-gate",
        ]
        for marker in required_semantics:
            with self.subTest(marker=marker):
                self.assertIn(marker, selector_window)

        required_signal_rows = {
            "代码 / 恢复 / 生命周期": [
                "Coding Session Start Gate",
                "Handoff Resume Approval Gate",
                "Context Budget And Auto Compact Ban",
                "Subagent Dispatch And Lifecycle",
            ],
            "已知改动 / live 取证 / 状态 / 跨上下文": [
                "Known-Change Debugging",
                "Live Evidence To Contract Gate",
                "Consumer State Convergence Gate",
                "Cross-Context Wakeup And Delivery Gate",
            ],
            "架构 / 发现 / 方向 / 规则变化": [
                "Architecture Baseline And Learning Loop",
                "Workflow Discovery",
                "Direction Challenge And Red-Team Review",
                "Rule Placement Fast Gate",
                "Workflow Manual Sync",
                "Constraint Benchmarking",
            ],
            "VOM / map": ["Verified Operation Map"],
            "review / verification / completion": [
                "Code Review Scope",
                "Verification Before Completion",
                "Completion Commit Reminder",
            ],
        }
        table_lines = [line for line in selector_window.splitlines() if line.strip().startswith("|")]
        self.assertGreaterEqual(len(table_lines), len(required_signal_rows) + 2)
        for signal, gates in required_signal_rows.items():
            with self.subTest(signal=signal):
                matches = [line for line in table_lines if signal in line]
                self.assertEqual(len(matches), 1)
                for gate in gates:
                    self.assertIn(gate, matches[0])

    def test_agents_has_one_canonical_rule_placement_global_heading(self):
        headings = [heading.strip() for heading in re.findall(r"(?m)^## .*Rule Placement.*Gate.*$", agents_text())]
        self.assertEqual(headings, ["## 2b. Rule Placement Gate / 规则放置闸门"])

    def test_agents_compact_contracts_keep_required_no_downgrade_semantics_locatable(self):
        text = agents_text()
        required_groups = {
            "core_communication_security": [
                "User explicit instruction wins",
                "Chinese/plain-language",
                "technical terms stay literal",
                "examples never become hidden boundaries",
                "Hardware target",
                "No hardcoded secrets",
            ],
            "runtime_tool_worktree_review": [
                "PowerShell",
                "forward paths",
                "Get-Content",
                "byte-level",
                "SKILL.md",
                "UTF-8 without BOM",
                "required parameters",
                "current cwd never implies repo-wide review",
                "paramiko",
                "OpenSSH",
            ],
            "live_evidence": [
                "universal",
                "official schema first",
                "business conclusion",
                "structural contract",
                "sanitized",
                "real consumed paths",
                "success/error envelope",
                "contract/parser test",
                "live evidence",
            ],
            "consumer_convergence": [
                "truth/source of truth",
                "projection/read model/cache",
                "actual consumer entry",
                "update owner",
                "propagation",
                "stale-reader",
                "persistence succeeds before success event",
            ],
            "cross_context": [
                "producer context",
                "consumer context",
                "delivery primitive",
                "wakeup",
                "known working example",
                "different context",
                "manual refresh",
            ],
            "subagents": [
                "`Codex Ultra` is the only subagent dispatcher",
                "native dispatch adds real value",
                "chooses each subagent's model and reasoning effort",
                "Only an explicit user choice or a genuine hard model requirement overrides that choice",
                "`SPP` must not create, select, reassign, or manage subagents",
                "must not take over planning, execution, or reviewer dispatch",
                "Honor explicit user requests for subagent/multi-agent/parallel-agent/main-agent-review-only work",
                "small tasks, strictly serial tasks, and shared-write conflicts stay single-agent",
                "review is read-only unless authorized",
                "Parallel implementation requires proven non-conflicting",
                "main verifies allowed paths, diff, tests, and conflicts",
                "Do not use `SPP`, `codex exec`, `claude -p`, or another CLI process as a fallback dispatcher",
                "closes finished subagents",
            ],
            "architecture_and_rules": [
                "project architecture baseline first",
                "ordinary low-risk fix fast-path",
                "ordinary verbs alone",
                "Direction Challenge",
                "Constraint Benchmarking",
                "only short every-session hard constraints",
                "Rule Change Maturity Radar",
            ],
            "compact_handoff_start_gate": [
                "Never rely on auto compact",
                "initial_marker",
                "partial_emergency",
                "continuation_started",
                "read-only first",
                "explicit user approval",
                "git rev-parse --show-toplevel",
                "docs/agent/worktrees/<handoff_id>.md",
                "active same path/branch/worktree collision stops",
            ],
            "verification_completion_sync": [
                "Verification Before Completion",
                "fresh evidence",
                "precise git status",
                "never auto commit/push/stash/clean",
                "Workflow Manual Sync",
                "personal/workflow skill changes",
                "unsynced/risk",
            ],
            "vom": [
                "VOM is the broad project-level umbrella",
                "Project Cognition Map",
                "POR is only page view",
                "never truth",
                "canonical validator",
                "complete page",
                "exact locators",
                "fresh ancestor commit",
                "truth/projection/observation",
            ],
            "general_engineering_review": [
                "Phase > Milestone > Task > Step",
                "sample before scale",
                "STATUS",
                "user-identified change package",
                "simple maintainable",
                "tests proportional",
                "target + direct impact",
                "actual coverage/evidence/blind spots",
            ],
        }
        for group, markers in required_groups.items():
            with self.subTest(group=group):
                missing = [marker for marker in markers if marker not in text]
                self.assertEqual(missing, [])

    def test_agents_restores_reviewed_slimming_contracts_without_reexpanding(self):
        text = agents_text()
        required_groups = {
            "long_automation": [
                "exponential backoff 1s/2s/4s/8s",
                "progress monitoring",
                "periodic checkpoint",
                "resume from checkpoint",
                "failed-item retry list",
                "file size/word count/error-keyword",
                "5-10 minutes",
            ],
            "debugging_error_discipline": [
                "known working example first",
                "do not retry the same approach more than twice",
                "validate integrity/output quality",
                "quote command + error",
                "two failures on same issue stop/ask",
                "do not broad-edit before evidence",
                "known-change hypothesis is insufficient or disproved",
            ],
            "learning_boundary_direction": [
                "Learning Loop",
                "small tasks",
                "cannot generalize",
                "Constraint Benchmarking / Architecture Baseline / Direction Challenge",
                "cognitive-boundary sync",
                "code/tests/docs first",
                "CONTEXT",
                "ADR",
                "minimal directory/file/responsibility explanation",
                "user confirmation",
                "high-confidence direction risk pauses implementation",
            ],
            "subagent_review": [
                "Use concise briefings",
                "fork full context only when genuinely required",
                "implementation/review/security/release roles",
                "review is read-only unless authorized",
                "state the failure and affected scope and ask before changing method",
                "Do not use `SPP`, `codex exec`, `claude -p`",
                "summary/blocking/non-blocking/evidence/reasoning/user impact/severity/confidence/suggested handling/verified vs inferred/unverified areas/limitations",
                "main de-duplicates",
                "unresolved high-risk disagreement",
                "purpose/user impact/acceptance/known risks/testing/rollback/limitations",
                "rollback risk",
            ],
            "other_losses": [
                "Confirm scope in one sentence",
                "explicit timeouts",
                "stdout/stderr/exit status",
                "no secrets",
                "SFTP",
                "handoff/session-log/map records",
                "business conclusion and structural contract",
                "mock/path mismatch is a bug",
                "submit / handoff / leave-for-user-or-other-session",
                "one file per session",
                "INDEX is not truth",
            ],
        }
        for group, markers in required_groups.items():
            with self.subTest(group=group):
                missing = [marker for marker in markers if marker not in text]
                self.assertEqual(missing, [])

        forbidden_fragments = [
            "they asks",
            "- only short",
            "- tests proportional",
            "- active same",
            "- persistence succeeds",
            "write workers serial unless",
            "main verifies files",
            "Review agents use the highest exposed model",
            "`reasoning_effort: xhigh` where supported",
            "Built-in subagent unavailable may fall back",
            "default to the `superpowers` `dispatching-parallel-agents` workflow",
            "- project architecture",
            "personal/workflow skill changes sync",
        ]
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, text)

    def test_workflow_manual_explains_compact_layout_routing_and_audit_contract(self):
        text = manual_text()
        required_markers = [
            "只放每次会话都必须先看到的短硬约束",
            "AGENTS.md",
            "coding-session-start-gate",
            "`must_use`",
            "`conditional`",
            "`not_triggered`",
            "`first_required_action`",
            "`stop_or_ask_conditions`",
            "`workflow_state_findings`",
            "只展开和当前任务有关",
            "第一步只能有一个",
            "低风险 fast-path",
            "workflow-state audit",
            "`not_run` 必须写清具体原因",
            "`exit 2` 表示未完成",
            "这是瘦身，不是降级",
        ]
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        forbidden_fragments = [
            "compact always-on hard-contract layer",
            "details remain in this manual and skills",
            "slimming, not reduced protection",
            "only plausible workflows expand",
            "one first action",
            "not_run needs a concrete reason",
            "exit 2 is incomplete",
        ]
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, text)

    def test_workflow_manual_has_restored_procedure_details_for_slimmed_contracts(self):
        text = manual_text()
        required_groups = {
            "long_automation_manual": [
                "长自动化和内容生成流水线",
                "1s、2s、4s、8s",
                "进度监控",
                "checkpoint",
                "失败项重试列表",
                "文件大小",
                "词数",
                "错误关键词",
                "5-10 分钟",
            ],
            "subagent_review_manual": [
                "review 结果输出",
                "blocking",
                "non-blocking",
                "evidence",
                "user impact",
                "severity",
                "confidence",
                "verified vs inferred",
                "unverified areas",
                "limitations",
                "不能悄悄改成主 agent 自审",
            ],
            "learning_boundary_manual": [
                "Learning Loop",
                "哪些结论不能泛化",
                "认知边界同步",
                "CONTEXT",
                "ADR",
                "不能替代代码、测试、契约、日志或真实 trace",
            ],
        }
        for group, markers in required_groups.items():
            with self.subTest(group=group):
                missing = [marker for marker in markers if marker not in text]
                self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
