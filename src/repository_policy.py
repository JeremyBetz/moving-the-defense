"""Bounded static checks for paper firewalls and changed public artifacts.

The checks deliberately supplement human governance. They detect a defined
subset of local imports, path expressions, and Git changes; they cannot prove
that protected data were never opened.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "repository_policy.json"
MAX_SYMLINK_HOPS = 16

# Qualified reader names intentionally form a small allowlist. In particular,
# ``json.load`` consumes an already-open handle and is not a path-taking reader.
READER_ARGUMENTS: dict[str, tuple[int, ...]] = {
    "open": (0,),
    "pandas.read_csv": (0,), "pandas.read_parquet": (0,),
    "pandas.read_json": (0,), "pandas.read_pickle": (0,),
    "pandas.read_feather": (0,),
    "polars.read_csv": (0,), "polars.read_parquet": (0,),
    "polars.read_json": (0,),
    "numpy.load": (0,), "numpy.loadtxt": (0,), "numpy.genfromtxt": (0,),
    # The current paper path uses two provider input paths here.
    "skillcorner.load": (0, 1),
}
PATH_RECEIVER_CALLS = {"open", "read_text", "read_bytes"}
PATH_KEYWORDS = {
    "pandas.read_csv": {"filepath_or_buffer", "path_or_buf"},
    "pandas.read_parquet": {"path", "path_or_buf", "filepath_or_buffer"},
    "pandas.read_json": {"path_or_buf", "filepath_or_buffer"},
    "pandas.read_pickle": {"filepath_or_buffer", "path"},
    "pandas.read_feather": {"path", "path_or_buf"},
    "polars.read_csv": {"source", "path", "file"},
    "polars.read_parquet": {"source", "path", "file"},
    "polars.read_json": {"source", "path", "file"},
    "numpy.load": {"file", "path", "fname"},
    "numpy.loadtxt": {"fname", "path"},
    "numpy.genfromtxt": {"fname", "path"},
    "skillcorner.load": {"metadata_path", "tracking_path"},
}
ALLOWED_EXCEPTION_FIELDS = {
    "path", "change_status", "source_path", "exception_type", "purpose",
    "rationale", "approval_reference", "sha256", "overrides",
}
ALLOWED_EXCEPTION_TYPES = {"synthetic_fixture", "publication_artifact"}
ALLOWED_OVERRIDES = {
    "reconstructive_name", "large_file", "opaque_container",
    "notebook_embedded_output", "provider_like_filename",
}
OPAQUE_SUFFIXES = {".zip", ".tar", ".gz", ".bz2", ".xz", ".pickle", ".pkl", ".joblib"}
SMALL_BINARY_SUFFIXES = {".bin", ".dat"}


@dataclass(frozen=True)
class ReadSite:
    line: int
    reader: str
    expression: str
    reason: str


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    detail: str
    blocking: bool = True
    sites: tuple[ReadSite, ...] = ()


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None = None
    size: int | None = None
    symlink_target: str | None = None
    sha256: str | None = None
    git_target: str | None = None


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


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _qualified_name(node.value, aliases)
        return f"{base}.{node.attr}" if base else None
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
        if not left:
            return right.lstrip("/")
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


def _static_prefix(node: ast.AST, constants: dict[str, str]) -> str | None:
    """Return only a proven literal prefix for a partially dynamic path."""
    exact = _static_path(node, constants)
    if exact is not None:
        return exact
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
        return _static_prefix(node.left, constants)
    if isinstance(node, ast.JoinedStr):
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
            else:
                break
        return "".join(pieces) or None
    if isinstance(node, ast.Call) and _call_name(node.func) == "Path" and node.args:
        return _static_prefix(node.args[0], constants)
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


def _mode_is_read(node: ast.Call, positional_index: int) -> bool:
    mode: ast.AST | None = node.args[positional_index] if len(node.args) > positional_index else None
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    if mode is None:
        return True
    return not (isinstance(mode, ast.Constant) and isinstance(mode.value, str) and mode.value[:1] in {"w", "a", "x"})


def _read_path_arguments(node: ast.Call, aliases: dict[str, str]) -> tuple[str, list[ast.AST]] | None:
    """Return known path-bearing arguments for intentionally bounded reader forms."""
    name = _call_name(node.func)
    if isinstance(node.func, ast.Attribute) and name in PATH_RECEIVER_CALLS:
        if name == "open" and not _mode_is_read(node, 0):
            return None
        return f"Path.{name}", [node.func.value]
    qualified = _qualified_name(node.func, aliases)
    if qualified is not None and qualified.endswith(".skillcorner.load"):
        qualified = "skillcorner.load"
    if qualified not in READER_ARGUMENTS:
        return None
    if qualified == "open" and not _mode_is_read(node, 1):
        return None
    arguments = [node.args[index] for index in READER_ARGUMENTS[qualified] if index < len(node.args)]
    keywords = PATH_KEYWORDS.get(qualified, set())
    arguments.extend(keyword.value for keyword in node.keywords if keyword.arg in keywords)
    return qualified, arguments


def _calls_without_nested(node: ast.AST) -> Iterable[ast.Call]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(child, ast.Call):
            yield child
        yield from _calls_without_nested(child)


def _scope_calls(
    body: list[ast.stmt], module_constants: dict[str, str], aliases: dict[str, str],
    source_path: str, policy: dict[str, Any], scope: str = "module",
) -> tuple[list[Finding], dict[tuple[str, str], list[ReadSite]]]:
    """Visit direct scope statements in order, carrying only safe local aliases."""
    findings: list[Finding] = []
    warnings: dict[tuple[str, str], list[ReadSite]] = {}
    constants = dict(module_constants)

    def inspect_call(call: ast.Call) -> None:
        found = _read_path_arguments(call, aliases)
        if found is None:
            return
        reader, arguments = found
        for argument in arguments:
            exact = _static_path(argument, constants)
            if exact is not None:
                if _path_is_protected(exact, policy):
                    findings.append(Finding("protected_read_path", source_path, exact.replace("\\", "/").lstrip("./")))
                continue
            prefix = _static_prefix(argument, constants)
            if prefix is not None and _path_is_protected(prefix.rstrip("/") + "/", policy):
                findings.append(Finding("protected_read_path", source_path, prefix.replace("\\", "/").lstrip("./") + " [dynamic suffix]"))
                continue
            warnings.setdefault((source_path, scope), []).append(
                ReadSite(call.lineno, reader, ast.unparse(argument), "path is not statically resolved")
            )

    for statement in body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested_findings, nested_warnings = _scope_calls(
                statement.body, module_constants, aliases, source_path, policy, statement.name
            )
            findings.extend(nested_findings)
            for key, sites in nested_warnings.items():
                warnings.setdefault(key, []).extend(sites)
            continue
        if isinstance(statement, ast.ClassDef):
            for member in statement.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nested_findings, nested_warnings = _scope_calls(
                        member.body, module_constants, aliases, source_path, policy, f"{statement.name}.{member.name}"
                    )
                    findings.extend(nested_findings)
                    for key, sites in nested_warnings.items():
                        warnings.setdefault(key, []).extend(sites)
            continue
        for call in _calls_without_nested(statement):
            inspect_call(call)
        target: ast.Name | None = None
        value: ast.AST | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            target, value = statement.targets[0], statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name) and statement.value is not None:
            target, value = statement.target, statement.value
        if target is not None and value is not None:
            resolved = _static_path(value, constants)
            if resolved is None:
                constants.pop(target.id, None)
            else:
                constants[target.id] = resolved
    return findings, warnings


def audit_current_paper(root: Path = ROOT, policy: dict[str, Any] | None = None) -> list[Finding]:
    """Check configured paper entry points and reachable local Python imports."""
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
        source_path = str(source.relative_to(root))
        source_findings, warning_sites = _scope_calls(
            tree.body, _constants(tree), _import_aliases(tree), source_path, policy
        )
        findings.extend(source_findings)
        for (path, scope), sites in warning_sites.items():
            ordered = tuple(sorted(set(sites), key=lambda site: (site.line, site.reader, site.expression)))
            findings.append(Finding(
                "unresolved_read_path", path, f"{scope}: {len(ordered)} path expression(s) not statically resolved",
                blocking=False, sites=ordered,
            ))
    return sorted(
        set(findings),
        key=lambda item: (item.kind, item.path, item.detail, tuple((site.line, site.reader, site.expression) for site in item.sites)),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _exception_rules(policy: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    configured = policy["artifact_policy"].get("exception_policy", {})
    required = set(configured.get("required_fields", ALLOWED_EXCEPTION_FIELDS - {"source_path"}))
    types = set(configured.get("allowed_types", ALLOWED_EXCEPTION_TYPES))
    overrides = set(configured.get("allowed_overrides", ALLOWED_OVERRIDES))
    return required, types, overrides


def _exception_errors(policy: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    required, allowed_types, allowed_overrides = _exception_rules(policy)
    for index, item in enumerate(policy["artifact_policy"].get("exceptions", [])):
        path = str(item.get("path", f"exceptions[{index}]"))
        unknown = set(item) - ALLOWED_EXCEPTION_FIELDS
        missing = required - set(item)
        status = item.get("change_status")
        kind = item.get("exception_type")
        overrides = item.get("overrides")
        invalid = (
            unknown or missing or status not in {"A", "M", "R", "C"}
            or kind not in allowed_types or not isinstance(overrides, list)
            or not set(overrides).issubset(allowed_overrides)
            or not all(isinstance(item.get(key), str) and item[key] for key in required - {"overrides"})
            or (status in {"R", "C"} and not isinstance(item.get("source_path"), str))
            or (status in {"A", "M"} and "source_path" in item)
            or (kind == "synthetic_fixture" and not set(overrides or []).issubset({"provider_like_filename", "reconstructive_name"}))
            or (kind == "publication_artifact" and not set(overrides or []).issubset({
                "reconstructive_name", "large_file", "opaque_container", "notebook_embedded_output"
            }))
        )
        if invalid:
            findings.append(Finding("invalid_exception", path, "exception schema is incomplete or has unsupported authority"))
    return findings


def _matching_exception(change: Change, path: str, override: str, policy: dict[str, Any]) -> bool:
    for item in policy["artifact_policy"].get("exceptions", []):
        if (
            item.get("path") == path and item.get("change_status") == change.status
            and item.get("sha256") == change.sha256 and override in item.get("overrides", [])
            and (change.status not in {"R", "C"} or item.get("source_path") == change.old_path)
        ):
            kind = item.get("exception_type")
            if kind == "synthetic_fixture":
                return path.startswith("tests/fixtures/") and override in {"provider_like_filename", "reconstructive_name"}
            return kind == "publication_artifact" and override in {
                "reconstructive_name", "large_file", "opaque_container", "notebook_embedded_output"
            }
    return False


def _path_findings(change: Change, path: str, policy: dict[str, Any]) -> list[Finding]:
    rules = policy["artifact_policy"]
    normalized = path.replace("\\", "/")
    lower_name = Path(normalized).name.lower()
    findings: list[Finding] = []
    if normalized.startswith("data/") and normalized not in rules["allowed_data_paths"]:
        findings.append(Finding("data_path", normalized, "changed paths under data/ are not public artifacts"))
    if any(token.lower() in lower_name for token in rules["raw_filename_substrings"]):
        if not _matching_exception(change, normalized, "provider_like_filename", policy):
            findings.append(Finding("raw_provider_filename", normalized, "matches configured raw provider filename marker"))
    if any(token.lower() in lower_name for token in rules["reconstructive_name_substrings"]):
        if not _matching_exception(change, normalized, "reconstructive_name", policy):
            findings.append(Finding("reconstructive_row_artifact", normalized, "matches configured row-artifact marker"))
    suffix = Path(normalized).suffix.lower()
    if suffix in OPAQUE_SUFFIXES and not _matching_exception(change, normalized, "opaque_container", policy):
        findings.append(Finding("opaque_container", normalized, "opaque artifact requires an exact reviewed exception"))
    if suffix == ".ipynb" and not _matching_exception(change, normalized, "notebook_embedded_output", policy):
        findings.append(Finding("notebook_embedded_output", normalized, "notebook output requires an exact reviewed exception"))
    if suffix in SMALL_BINARY_SUFFIXES:
        findings.append(Finding("unknown_binary_artifact", normalized, "small binary artifact was not content-classified", blocking=False))
    return findings


def _lexical_link_path(path: str, target: str) -> tuple[str | None, str | None]:
    if os.path.isabs(target):
        return None, "external"
    parts: list[str] = list(PurePosixPath(path).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None, "external"
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts), None


def _git_mode_and_bytes(root: Path, revision: str, path: str) -> tuple[str | None, bytes | None]:
    record = subprocess.check_output(["git", "ls-tree", revision, "--", path], cwd=root, text=True).strip()
    if not record:
        return None, None
    mode = record.split(maxsplit=1)[0]
    return mode, subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root)


def _symlink_findings(change: Change, policy: dict[str, Any], root: Path) -> list[Finding]:
    if change.symlink_target is None:
        return []
    current_path, target = change.path, change.symlink_target
    for _ in range(MAX_SYMLINK_HOPS):
        resolved, error = _lexical_link_path(current_path, target)
        if error is not None or resolved is None:
            return [Finding("external_symlink", change.path, target)]
        if change.git_target is not None:
            mode, payload = _git_mode_and_bytes(root, change.git_target, resolved)
            if mode is None or payload is None:
                return [Finding("broken_symlink", change.path, resolved)]
            if mode == "040000":
                return [Finding("directory_symlink", change.path, resolved)]
            if mode == "120000":
                current_path, target = resolved, payload.decode("utf-8").rstrip("\n")
                continue
            return _path_findings(change, resolved, policy)
        candidate = root / resolved
        try:
            final = candidate.resolve(strict=True)
            final.relative_to(root.resolve())
        except (FileNotFoundError, ValueError):
            return [Finding("external_symlink", change.path, target)]
        if final.is_dir():
            return [Finding("directory_symlink", change.path, resolved)]
        return _path_findings(change, final.relative_to(root.resolve()).as_posix(), policy)
    return [Finding("symlink_chain_limit", change.path, f"exceeds {MAX_SYMLINK_HOPS} hops")]


def audit_changes(changes: Iterable[Change], policy: dict[str, Any], root: Path = ROOT) -> list[Finding]:
    """Check A/M/R/C paths only; unchanged historical artifacts are ignored."""
    findings = _exception_errors(policy)
    rules = policy["artifact_policy"]
    for change in changes:
        for candidate in [change.path, *([change.old_path] if change.old_path is not None else [])]:
            findings.extend(_path_findings(change, candidate, policy))
        path = change.path.replace("\\", "/")
        if change.size is not None and change.size > int(rules["max_changed_file_bytes"]):
            if not _matching_exception(change, path, "large_file", policy):
                findings.append(Finding("large_changed_file", path, f"{change.size} bytes exceeds configured limit"))
        findings.extend(_symlink_findings(change, policy, root))
    return sorted(
        set(findings),
        key=lambda item: (item.kind, item.path, item.detail, tuple((site.line, site.reader, site.expression) for site in item.sites)),
    )


def _git_changes(root: Path, base: str, target: str) -> list[Change]:
    raw = subprocess.check_output(
        ["git", "diff", "--name-status", "-z", "--find-renames", "--find-copies-harder", base, target], cwd=root
    )
    fields = raw.decode("utf-8").split("\0")
    changes: list[Change] = []
    i = 0
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
        mode, payload = _git_mode_and_bytes(root, target, path)
        if mode is None or payload is None:
            continue
        changes.append(Change(
            status=status[0], path=path, old_path=old_path, size=len(payload),
            symlink_target=payload.decode("utf-8").rstrip("\n") if mode == "120000" else None,
            sha256=_sha256_bytes(payload), git_target=target,
        ))
    return changes


def _worktree_changes(root: Path) -> list[Change]:
    raw = subprocess.check_output(
        ["git", "status", "--untracked-files=all", "--porcelain=v1", "-z"], cwd=root
    ).decode("utf-8")
    fields = raw.split("\0")
    changes: list[Change] = []
    i = 0
    while i < len(fields) - 1:
        record = fields[i]; i += 1
        if not record:
            continue
        code, path = record[:2], record[3:]
        old_path = fields[i] if code[0] in {"R", "C"} or code[1] in {"R", "C"} else None
        if old_path is not None:
            i += 1
        status = "A" if code == "??" else next((char for char in code if char not in {" ", "?"}), "M")
        if status == "D":
            continue
        candidate = root / path
        if candidate.is_symlink():
            payload = os.readlink(candidate).encode("utf-8")
            target = os.readlink(candidate)
        elif candidate.exists() and candidate.is_file():
            payload = candidate.read_bytes()
            target = None
        else:
            payload, target = b"", None
        changes.append(Change(
            status=status, path=path, old_path=old_path, size=len(payload), symlink_target=target,
            sha256=_sha256_bytes(payload),
        ))
    return changes


def _print(findings: list[Finding]) -> None:
    print(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True))


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
