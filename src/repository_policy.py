"""Bounded static checks for current-paper firewalls and changed artifacts.

These checks are deliberately conservative supplements to human governance.
They can detect reachable local imports and statically resolvable read paths,
but cannot prove that protected data were never opened.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "repository_policy.json"
READ_CALLS = {
    "open", "read_csv", "read_parquet", "read_json", "read_pickle", "read_feather",
    "read_text", "read_bytes", "load", "loadtxt", "genfromtxt",
}
PATH_RECEIVER_CALLS = {"open", "read_text", "read_bytes"}
PATH_KEYWORDS = {
    "read_csv": {"filepath_or_buffer", "path_or_buf"},
    "read_parquet": {"path", "path_or_buf", "filepath_or_buffer"},
    "read_json": {"path_or_buf", "filepath_or_buffer"},
    "read_pickle": {"filepath_or_buffer", "path"},
    "read_feather": {"path", "path_or_buf"},
    "load": {"file", "path", "fname"},
    "loadtxt": {"fname", "path"},
    "genfromtxt": {"fname", "path"},
}


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    detail: str
    blocking: bool = True


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None = None
    size: int | None = None
    symlink_target: str | None = None


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_for_module(root: Path, module: str) -> Path | None:
    if not module:
        return None
    base = root / "src" / Path(*module.split("."))
    candidate = base.with_suffix(".py")
    if candidate.is_file():
        return candidate
    init = base / "__init__.py"
    return init if init.is_file() else None


def _source_from_base(base: Path) -> Path | None:
    candidate = base.with_suffix(".py")
    if candidate.is_file():
        return candidate
    init = base / "__init__.py"
    return init if init.is_file() else None


def _module_name(root: Path, source: Path) -> str:
    relative = source.relative_to(root / "src")
    parts = relative.with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _imports(tree: ast.AST, source: Path, root: Path) -> list[tuple[str, Path | None]]:
    imports: list[tuple[str, Path | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, _source_for_module(root, alias.name)))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                relative = source.parent
                for _ in range(node.level - 1):
                    relative = relative.parent
                if module:
                    target = _source_from_base(relative / Path(*module.split(".")))
                    imports.append((_module_name(root, target) if target is not None else module, target))
                else:
                    for alias in node.names:
                        target = _source_from_base(relative / alias.name)
                        imports.append((_module_name(root, target) if target is not None else alias.name, target))
                continue
            imports.append((module, _source_for_module(root, module)))
            for alias in node.names:
                child = f"{module}.{alias.name}" if module else alias.name
                child_source = _source_for_module(root, child)
                if child_source is not None:
                    imports.append((child, child_source))
    return imports


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _static_path(node: ast.AST, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left, right = _static_path(node.left, constants), _static_path(node.right, constants)
        if left is None or right is None:
            return None
        return f"{left.rstrip('/')}/{right.lstrip('/')}"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _static_path(node.left, constants), _static_path(node.right, constants)
        return None if left is None or right is None else f"{left}{right}"
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                resolved = _static_path(value.value, constants)
                if resolved is None:
                    return None
                parts.append(resolved)
            else:
                return None
        return "".join(parts)
    if isinstance(node, ast.Call) and _call_name(node.func) == "Path" and node.args:
        return _static_path(node.args[0], constants)
    return None


def _constants(tree: ast.AST) -> dict[str, str]:
    values: dict[str, str] = {"ROOT": ""}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = _static_path(node.value, values)
            if value is not None:
                values[node.targets[0].id] = value
    return values


def _path_is_protected(path: str, policy: dict[str, Any]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return (
        any(normalized.startswith(prefix) for prefix in policy["protected_path_prefixes"])
        or any(token in normalized for token in policy["protected_path_substrings"])
    )


def _read_path_argument(node: ast.Call) -> ast.AST | None:
    """Return the path-bearing expression for a bounded set of reader forms."""
    name = _call_name(node.func)
    if isinstance(node.func, ast.Attribute) and name in PATH_RECEIVER_CALLS:
        return node.func.value
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg in PATH_KEYWORDS.get(name, set()):
            return keyword.value
    return None


def audit_current_paper(root: Path = ROOT, policy: dict[str, Any] | None = None) -> list[Finding]:
    """Check only configured paper entry points and their local Python imports."""
    policy = load_policy(root / "config" / "repository_policy.json") if policy is None else policy
    queue: list[Path] = []
    visited: set[Path] = set()
    findings: list[Finding] = []
    for configured in policy["current_paper_entrypoints"]:
        source = root / configured
        if not source.is_file():
            findings.append(Finding("missing_entrypoint", configured, "configured current-paper entry point does not exist"))
        else:
            queue.append(source)
    while queue:
        source = queue.pop()
        if source in visited or not source.is_file():
            continue
        visited.add(source)
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for module, target in _imports(tree, source, root):
            if any(module == prefix or module.startswith(f"{prefix}.") for prefix in policy["protected_module_prefixes"]):
                findings.append(Finding("protected_module", str(source.relative_to(root)), module))
            if target is not None:
                queue.append(target)
        constants = _constants(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _call_name(node.func) not in READ_CALLS:
                continue
            argument = _read_path_argument(node)
            path = None if argument is None else _static_path(argument, constants)
            if path is not None and _path_is_protected(path, policy):
                findings.append(Finding("protected_read_path", str(source.relative_to(root)), path.replace("\\", "/").lstrip("./")))
            elif path is None and argument is not None:
                findings.append(Finding("unresolved_read_path", str(source.relative_to(root)), ast.unparse(argument), blocking=False))
    return sorted(set(findings), key=lambda item: (item.kind, item.path, item.detail))


def _exception(path: str, policy: dict[str, Any]) -> bool:
    for item in policy["artifact_policy"].get("exceptions", []):
        if item.get("path") == path and item.get("reason") and item.get("approval_reference"):
            return True
    return False


def audit_changes(changes: Iterable[Change], policy: dict[str, Any], root: Path = ROOT) -> list[Finding]:
    """Check changed paths only; unchanged historical artifacts are ignored."""
    rules = policy["artifact_policy"]
    findings: list[Finding] = []
    for change in changes:
        paths = [change.path, *([change.old_path] if change.old_path is not None else [])]
        for candidate in paths:
            path = candidate.replace("\\", "/")
            if _exception(path, policy):
                continue
            lower_name = Path(path).name.lower()
            if path.startswith("data/") and path not in rules["allowed_data_paths"]:
                findings.append(Finding("data_path", path, "changed paths under data/ are not public artifacts"))
            if any(token.lower() in lower_name for token in rules["raw_filename_substrings"]):
                findings.append(Finding("raw_provider_filename", path, "matches configured raw provider filename marker"))
            if any(token.lower() in lower_name for token in rules["reconstructive_name_substrings"]):
                findings.append(Finding("reconstructive_row_artifact", path, "matches configured row-artifact marker"))
        path = change.path.replace("\\", "/")
        if change.size is not None and change.size > int(rules["max_changed_file_bytes"]):
            findings.append(Finding("large_changed_file", path, f"{change.size} bytes exceeds configured limit"))
        if change.symlink_target is not None:
            target = (root / path).parent / change.symlink_target
            try:
                target.resolve().relative_to(root.resolve())
            except ValueError:
                findings.append(Finding("external_symlink", path, change.symlink_target))
    return sorted(set(findings), key=lambda item: (item.kind, item.path, item.detail))


def _git_changes(root: Path, base: str, target: str) -> list[Change]:
    raw = subprocess.check_output(["git", "diff", "--name-status", "-z", "--find-renames", "--find-copies-harder", base, target], cwd=root)
    fields = raw.decode("utf-8").split("\0")
    changes: list[Change] = []; i = 0
    while i < len(fields) - 1:
        status = fields[i]; i += 1
        if not status:
            continue
        if status[0] == "D":
            i += 1
            continue
        if status[0] in {"R", "C"}:
            old_path, path = fields[i], fields[i + 1]; i += 2
        else:
            old_path, path = None, fields[i]; i += 1
        size_text = subprocess.check_output(["git", "cat-file", "-s", f"{target}:{path}"], cwd=root, text=True).strip()
        mode = subprocess.check_output(["git", "ls-tree", target, "--", path], cwd=root, text=True).split(maxsplit=1)[0]
        target_text = subprocess.check_output(["git", "show", f"{target}:{path}"], cwd=root, text=True) if mode == "120000" else None
        changes.append(Change(status=status[0], path=path, old_path=old_path, size=int(size_text), symlink_target=target_text))
    return changes


def _worktree_changes(root: Path) -> list[Change]:
    raw = subprocess.check_output(["git", "status", "--untracked-files=all", "--porcelain=v1", "-z"], cwd=root).decode("utf-8")
    fields = raw.split("\0"); changes: list[Change] = []; i = 0
    while i < len(fields) - 1:
        record = fields[i]; i += 1
        if not record:
            continue
        code, path = record[:2], record[3:]
        old_path = fields[i] if code[0] in {"R", "C"} or code[1] in {"R", "C"} else None
        if old_path is not None:
            i += 1
        if code == "??":
            status = "A"
        else:
            status = next((char for char in code if char not in {" ", "?"}), "M")
        if status == "D":
            continue
        candidate = root / path
        changes.append(Change(status=status, path=path, old_path=old_path,
                              size=candidate.stat().st_size if candidate.exists() else None,
                              symlink_target=os.readlink(candidate) if candidate.is_symlink() else None))
    return changes


def _print(findings: list[Finding]) -> None:
    print(json.dumps([item.__dict__ for item in findings], indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("paper-firewall")
    changed = commands.add_parser("changed-artifacts")
    changed.add_argument("--base", required=True)
    changed.add_argument("--target", default="HEAD")
    changed.add_argument("--include-worktree", action="store_true")
    args = parser.parse_args()
    policy = load_policy(args.policy)
    if args.command == "paper-firewall":
        findings = audit_current_paper(ROOT, policy)
    else:
        changes = _git_changes(ROOT, args.base, args.target)
        if args.include_worktree:
            changes.extend(_worktree_changes(ROOT))
        findings = audit_changes(changes, policy, ROOT)
    _print(findings)
    return 1 if any(finding.blocking for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
