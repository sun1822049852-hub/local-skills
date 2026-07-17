#!/usr/bin/env python3
"""Read-only workflow state audit with stable JSON output."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REGISTRY_REQUIRED = {
    "status",
    "target",
    "handoff_id",
    "parent_handoff_id",
    "branch",
    "worktree",
    "allowed_paths",
    "forbidden_paths",
    "updated_at",
    "last_verified",
}
REGISTRY_STATUSES = {"active", "merged", "abandoned", "archived"}
HANDOFF_NONTERMINAL = {"initial_marker", "continuation_started", "in_progress", "partial_emergency"}
LEGACY_NOTES_HEADER_REQUIRED = {"handoff_id", "status", "parent_handoff_id"}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def finding(subject: str, evidence: str, task_relevance: str, actionability: str, severity: str) -> dict[str, str]:
    return {
        "subject": subject,
        "evidence": evidence,
        "task_relevance": task_relevance,
        "actionability": actionability,
        "severity": severity,
    }


def stable_output(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def base_payload(args: argparse.Namespace | None = None) -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    if args is not None:
        inputs = {
            "branch": args.branch,
            "current_handoff_id": args.current_handoff_id,
            "handoff_dir": str(args.handoff_dir),
            "por": str(args.por),
            "por_repo_root": str(args.por_repo_root),
            "por_schema": str(args.por_schema),
            "registry_dir": str(args.registry_dir),
            "repo_root": str(args.repo_root),
            "task_paths": sorted(args.task_path),
            "terminal_statuses": sorted(args.terminal_status),
            "vom_validator": str(args.vom_validator),
            "worktree": str(args.worktree),
        }
    return {
        "complete": True,
        "findings": [],
        "handoffs": {"active_leaves": [], "checked": []},
        "inputs": inputs,
        "manuals": {},
        "por": {"status": "not_checked"},
        "registry": {"checked": [], "current_found": False},
        "schema_version": "workflow_state_audit.v1",
    }


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--task-path", required=True, action="append")
    parser.add_argument("--registry-dir", required=True, type=Path)
    parser.add_argument("--handoff-dir", required=True, type=Path)
    parser.add_argument("--current-handoff-id", required=True)
    parser.add_argument("--terminal-status", required=True, action="append")
    parser.add_argument("--manual", required=True, action="append")
    parser.add_argument("--por", required=True, type=Path)
    parser.add_argument("--por-repo-root", required=True, type=Path)
    parser.add_argument("--por-schema", required=True, type=Path)
    parser.add_argument("--vom-validator", required=True, type=Path)
    return parser.parse_args(argv)


def load_yaml_module(payload: dict[str, Any]) -> Any | None:
    try:
        import yaml
    except ModuleNotFoundError:
        payload["complete"] = False
        payload["findings"].append(finding(
            "python.dependency",
            "PyYAML is required; install with requirements.txt for this skill",
            "related",
            "stop",
            "high",
        ))
        return None
    return yaml


def read_frontmatter(path: Path, yaml: Any) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, f"invalid UTF-8: {exc}"
    except OSError as exc:
        return None, f"read failed: {exc}"
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            for index, line in enumerate(lines[:-1]):
                if line == "" and lines[index + 1] == "Notes:":
                    try:
                        header = yaml.safe_load("\n".join(lines[:index]))
                    except yaml.YAMLError:
                        break
                    if isinstance(header, dict) and LEGACY_NOTES_HEADER_REQUIRED <= set(header):
                        return header, None
                    break
            return None, f"invalid YAML: {exc}"
        if not isinstance(data, dict):
            return None, "YAML document must be a mapping"
        return data, None
    block: list[str] = []
    found_end = False
    for line in lines[1:]:
        if line == "---":
            found_end = True
            break
        block.append(line)
    if not found_end:
        return None, "unterminated YAML frontmatter"
    try:
        data = yaml.safe_load("\n".join(block)) or {}
    except yaml.YAMLError as exc:
        return None, f"invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    return data, None


def normalize_path(raw: Any) -> str:
    return str(raw).replace("\\", "/").strip()


def is_windows_drive_path(path: str) -> bool:
    return len(path) >= 3 and path[1] == ":" and path[0].isalpha() and path[2] == "/"


def comparable_path(raw: Any) -> str:
    path = normalize_path(raw)
    if is_windows_drive_path(path):
        return path.casefold()
    return path


def paths_equal(left: Any, right: Any) -> bool:
    return comparable_path(left) == comparable_path(right)


def path_matches(pattern: str, task_path: str) -> bool:
    candidate = normalize_path(pattern)
    task = normalize_path(task_path)
    if not candidate:
        return False
    candidate_key = comparable_path(candidate)
    task_key = comparable_path(task)
    if candidate_key == task_key:
        return True
    if fnmatch.fnmatchcase(task_key, candidate_key):
        return True
    prefix = candidate_key.rstrip("/")
    for suffix in ("/**", "/*"):
        if prefix.endswith(suffix):
            prefix = prefix[: -len(suffix)]
    return bool(prefix and (task_key == prefix or task_key.startswith(prefix + "/")))


def paths_related(paths: Any, task_paths: list[str]) -> bool:
    if not isinstance(paths, list):
        return False
    for item in paths:
        for task_path in task_paths:
            if path_matches(str(item), task_path):
                return True
    return False


def item_related(data: dict[str, Any], task_paths: list[str]) -> bool:
    return paths_related(data.get("allowed_paths"), task_paths) or paths_related(data.get("forbidden_paths"), task_paths)


def parent_id(raw: Any) -> str:
    if raw is None:
        return ""
    parent = str(raw).strip()
    if not parent or parent.lower() == "none":
        return ""
    return parent


def validate_paths(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    checks = (
        ("repo-root", args.repo_root, "dir"),
        ("worktree", args.worktree, "dir"),
        ("registry-dir", args.registry_dir, "dir"),
        ("handoff-dir", args.handoff_dir, "dir"),
        ("por-repo-root", args.por_repo_root, "dir"),
        ("por-schema", args.por_schema, "file"),
    )
    for label, path, kind in checks:
        ok = path.is_dir() if kind == "dir" else path.is_file()
        if not ok:
            payload["complete"] = False
            payload["findings"].append(finding(
                f"path:{label}",
                f"expected {kind}: {path}",
                "related",
                "stop",
                "high",
            ))


def collect_docs(directory: Path, prefix: str, yaml: Any, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    sources: dict[str, str] = {}
    if not directory.is_dir():
        return docs
    for path in sorted(directory.glob("*.md"), key=lambda item: item.name):
        data, error = read_frontmatter(path, yaml)
        if error:
            payload["complete"] = False
            payload["findings"].append(finding(
                f"{prefix}:{path.name}",
                error,
                "related",
                "stop",
                "high",
            ))
            continue
        doc_id = str(data.get("handoff_id") or path.stem)
        if doc_id in docs:
            payload["complete"] = False
            payload["findings"].append(finding(
                f"{prefix}:{doc_id}",
                f"duplicate handoff_id: {doc_id} in {sources[doc_id]} and {path.name}",
                "related",
                "stop",
                "high",
            ))
            continue
        docs[doc_id] = data
        sources[doc_id] = path.name
    return docs


def audit_current_registry(args: argparse.Namespace, payload: dict[str, Any], data: dict[str, Any]) -> None:
    if data.get("status") != "active":
        payload["findings"].append(finding(
            f"registry:{args.current_handoff_id}",
            f"current registry status must be active: {data.get('status')!r}",
            "related",
            "stop",
            "high",
        ))
    if data.get("branch") != args.branch:
        payload["findings"].append(finding(
            f"registry:{args.current_handoff_id}",
            f"current registry branch mismatch: expected {args.branch!r}, got {data.get('branch')!r}",
            "related",
            "stop",
            "high",
        ))
    if not paths_equal(data.get("worktree"), args.worktree):
        payload["findings"].append(finding(
            f"registry:{args.current_handoff_id}",
            f"current registry worktree mismatch: expected {normalize_path(args.worktree)!r}, got {normalize_path(data.get('worktree'))!r}",
            "related",
            "stop",
            "high",
        ))
    for task_path in args.task_path:
        if not paths_related(data.get("allowed_paths"), [task_path]):
            payload["findings"].append(finding(
                f"registry:{args.current_handoff_id}",
                f"task path not covered by current allowed_paths: {task_path}",
                "related",
                "stop",
                "high",
            ))
        if paths_related(data.get("forbidden_paths"), [task_path]):
            payload["findings"].append(finding(
                f"registry:{args.current_handoff_id}",
                f"task path matches current forbidden_paths: {task_path}",
                "related",
                "stop",
                "high",
            ))


def registry_ancestor_ids(docs: dict[str, dict[str, Any]], current_id: str) -> set[str]:
    ancestors: set[str] = set()
    seen = {current_id}
    next_id = parent_id(docs.get(current_id, {}).get("parent_handoff_id"))
    while next_id and next_id in docs and next_id not in seen:
        ancestors.add(next_id)
        seen.add(next_id)
        next_id = parent_id(docs.get(next_id, {}).get("parent_handoff_id"))
    return ancestors


def audit_registry(args: argparse.Namespace, payload: dict[str, Any], yaml: Any) -> None:
    docs = collect_docs(args.registry_dir, "registry", yaml, payload)
    payload["registry"]["checked"] = sorted(docs)
    payload["registry"]["current_found"] = args.current_handoff_id in docs
    if not payload["registry"]["current_found"]:
        payload["findings"].append(finding(
            "registry:current",
            f"current handoff id not found: {args.current_handoff_id}",
            "related",
            "stop",
            "high",
        ))
    ancestor_ids = registry_ancestor_ids(docs, args.current_handoff_id)
    for doc_id, data in sorted(docs.items()):
        missing = sorted(REGISTRY_REQUIRED - set(data))
        if missing:
            payload["findings"].append(finding(
                f"registry:{doc_id}",
                "missing required fields: " + ", ".join(missing),
                "related" if doc_id == args.current_handoff_id else "unknown",
                "stop",
                "high",
            ))
        status = data.get("status")
        if status not in REGISTRY_STATUSES:
            payload["findings"].append(finding(
                f"registry:{doc_id}",
                f"unknown registry status: {status!r}",
                "related" if item_related(data, args.task_path) else "unknown",
                "stop",
                "high",
            ))
        if doc_id == args.current_handoff_id:
            audit_current_registry(args, payload, data)
            continue
        if status != "active":
            continue
        if doc_id in ancestor_ids:
            continue
        same_branch = data.get("branch") == args.branch
        same_worktree = paths_equal(data.get("worktree"), args.worktree)
        if same_branch or same_worktree or item_related(data, args.task_path):
            related = same_branch or same_worktree or item_related(data, args.task_path)
            payload["findings"].append(finding(
                f"registry:{doc_id}",
                "active registry overlaps by "
                + ", ".join(name for name, hit in (("branch", same_branch), ("worktree", same_worktree), ("path", item_related(data, args.task_path))) if hit),
                "related" if related else "unrelated",
                "stop" if related else "warn",
                "high" if related else "medium",
            ))


def audit_handoffs(args: argparse.Namespace, payload: dict[str, Any], yaml: Any) -> None:
    docs = collect_docs(args.handoff_dir, "handoff", yaml, payload)
    payload["handoffs"]["checked"] = sorted(docs)
    terminals = set(args.terminal_status)
    children: dict[str, list[str]] = {}
    nonterminal: set[str] = set()
    for doc_id, data in sorted(docs.items()):
        status = data.get("status")
        if status in HANDOFF_NONTERMINAL:
            nonterminal.add(doc_id)
        elif status not in terminals:
            payload["findings"].append(finding(
                f"handoff:{doc_id}",
                f"unknown handoff status for provided terminal set: {status!r}",
                "related" if item_related(data, args.task_path) else "unknown",
                "stop",
                "high",
            ))
        parent = parent_id(data.get("parent_handoff_id"))
        if parent:
            children.setdefault(parent, []).append(doc_id)
            if parent not in docs:
                payload["findings"].append(finding(
                    f"handoff:{doc_id}",
                    f"missing parent handoff: {parent}",
                    "related" if item_related(data, args.task_path) else "unknown",
                    "stop",
                    "high",
                ))
    for doc_id in sorted(docs):
        seen: set[str] = set()
        current = doc_id
        while current:
            if current in seen:
                payload["findings"].append(finding(
                    f"handoff:{doc_id}",
                    f"cycle detected at {current}",
                    "related" if item_related(docs.get(doc_id, {}), args.task_path) else "unknown",
                    "stop",
                    "high",
                ))
                break
            seen.add(current)
            current = parent_id(docs.get(current, {}).get("parent_handoff_id"))
    leaves = sorted(doc_id for doc_id in nonterminal if not children.get(doc_id))
    payload["handoffs"]["active_leaves"] = leaves
    related_active_leaves = [
        doc_id for doc_id in leaves
        if item_related(docs.get(doc_id, {}), args.task_path)
    ]
    if len(related_active_leaves) > 1:
        payload["findings"].append(finding(
            "handoff:active_leaves",
            "multiple related nonterminal leaves: " + ", ".join(related_active_leaves),
            "related",
            "stop",
            "high",
        ))
    for parent, child_ids in sorted(children.items()):
        related_leaves = [
            child_id for child_id in sorted(child_ids)
            if child_id in leaves and item_related(docs.get(child_id, {}), args.task_path)
        ]
        if len(related_leaves) > 1:
            payload["findings"].append(finding(
                f"handoff:{parent}",
                "multiple related nonterminal leaves: " + ", ".join(related_leaves),
                "related",
                "stop",
                "high",
            ))


def normalize_manual(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def audit_manuals(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    normalized_hashes: dict[str, str] = {}
    seen_names: set[str] = set()
    for raw in args.manual:
        if "=" not in raw:
            payload["complete"] = False
            payload["findings"].append(finding("manual", f"manual argument must be name=path: {raw}", "related", "stop", "high"))
            continue
        name, raw_path = raw.split("=", 1)
        if not name.strip():
            payload["complete"] = False
            payload["findings"].append(finding("manual", "manual logical name must be non-empty", "related", "stop", "high"))
            continue
        if name in seen_names:
            payload["complete"] = False
            payload["findings"].append(finding(f"manual:{name}", f"duplicate manual logical name: {name}", "related", "stop", "high"))
            continue
        seen_names.add(name)
        path = Path(raw_path)
        try:
            data = path.read_bytes()
            normalized = normalize_manual(data)
        except UnicodeDecodeError as exc:
            payload["complete"] = False
            payload["findings"].append(finding(f"manual:{name}", f"invalid UTF-8: {exc}", "related", "stop", "high"))
            continue
        except OSError as exc:
            payload["complete"] = False
            payload["findings"].append(finding(f"manual:{name}", f"read failed: {exc}", "related", "stop", "high"))
            continue
        exact_hash = hashlib.sha256(data).hexdigest()
        normalized_hash = hashlib.sha256(normalized).hexdigest()
        payload["manuals"][name] = {
            "exact_sha256": exact_hash,
            "normalized_sha256": normalized_hash,
            "path": str(path),
        }
        normalized_hashes[name] = normalized_hash
    if len(set(normalized_hashes.values())) > 1:
        payload["findings"].append(finding(
            "manuals",
            "normalized manual hashes differ: "
            + ", ".join(f"{name}={value}" for name, value in sorted(normalized_hashes.items())),
            "related",
            "stop",
            "high",
        ))


def audit_por(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    payload["por"] = {"path": str(args.por), "status": "absent"}
    if not args.por.exists():
        return
    command = [
        sys.executable,
        "-B",
        str(args.vom_validator),
        "--input",
        str(args.por),
        "--repo-root",
        str(args.por_repo_root),
        "--schema",
        str(args.por_schema),
    ]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as exc:
        payload["complete"] = False
        payload["por"] = {"path": str(args.por), "status": "incomplete", "validator_exit_code": None}
        payload["findings"].append(finding("por", f"validator failed to start: {exc}", "related", "stop", "high"))
        return
    payload["por"] = {
        "path": str(args.por),
        "status": "incomplete",
        "validator_exit_code": completed.returncode,
    }
    if completed.returncode == 0:
        payload["por"]["status"] = "valid"
    elif completed.returncode == 1:
        payload["por"]["status"] = "invalid"
        payload["findings"].append(finding("por", "VOM validator reported invalid POR", "related", "stop", "high"))
    elif completed.returncode == 3:
        payload["por"]["status"] = "stale"
        payload["findings"].append(finding("por", "VOM validator reported stale POR", "related", "warn", "medium"))
    else:
        payload["complete"] = False
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        payload["findings"].append(finding("por", f"VOM validator incomplete or unknown result: {detail}", "related", "stop", "high"))


def finalize(payload: dict[str, Any]) -> int:
    payload["findings"] = sorted(payload["findings"], key=lambda item: (
        item["subject"],
        item["severity"],
        item["actionability"],
        item["evidence"],
    ))
    stable_output(payload)
    if not payload["complete"]:
        return 2
    if payload["findings"]:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except ValueError as exc:
        payload = base_payload()
        payload["complete"] = False
        payload["findings"].append(finding("cli.arguments", str(exc), "related", "stop", "high"))
        return finalize(payload)
    payload = base_payload(args)
    validate_paths(args, payload)
    yaml = load_yaml_module(payload)
    if yaml is None:
        return finalize(payload)
    audit_registry(args, payload, yaml)
    audit_handoffs(args, payload, yaml)
    audit_manuals(args, payload)
    audit_por(args, payload)
    return finalize(payload)


if __name__ == "__main__":
    raise SystemExit(main())
