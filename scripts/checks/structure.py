"""Check maintained file budgets, test placement and pure-core imports."""

from __future__ import annotations

import ast
import sys
import tomllib
from collections import defaultdict
from collections.abc import Iterator
from importlib.util import resolve_name
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def maintained_files(ignored: set[str]) -> Iterator[Path]:
    for directory, subdirectories, filenames in ROOT.walk():
        subdirectories[:] = [
            name
            for name in subdirectories
            if name not in ignored and not name.endswith(".egg-info")
        ]
        for name in sorted(filenames):
            if name != ".DS_Store":
                yield directory / name


def imported_modules(path: Path, content: str) -> Iterator[tuple[int, str]]:
    package = ".".join(path.relative_to(ROOT / "src").parent.parts)
    for node in ast.walk(ast.parse(content, filename=str(path))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            module = resolve_name(base, package) if node.level else base
            yield node.lineno, module
            for alias in node.names:
                yield node.lineno, f"{module}.{alias.name}"


def check() -> list[str]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        rules = tomllib.load(stream)["tool"]["echo-heist"]["structure"]
    ignored = set(rules["ignored-directories"])
    exempt = tuple(Path(value) for value in rules["line-exempt-paths"])
    by_directory: dict[Path, list[Path]] = defaultdict(list)
    problems: list[str] = []

    for path in maintained_files(ignored):
        relative = path.relative_to(ROOT)
        by_directory[path.parent].append(path)
        line_exempt = any(relative == value or value in relative.parents for value in exempt)
        if not line_exempt:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue  # Binary assets count as files, but have no authored-text line count.
            count = len(content.splitlines())
            if count > rules["max-lines"]:
                problems.append(f"{relative}: {count} lines; limit {rules['max-lines']}")
        is_test = path.name.startswith("test_") or path.name.endswith("_test.py")
        if (
            path.suffix == ".py"
            and (is_test or path.name in {"tests.py", "conftest.py"})
            and relative.parts[0] != "tests"
        ):
            problems.append(f"{relative}: test files belong under root tests/")
        area = relative.parts[:3]
        pure_core = area == ("src", "echo_heist", "core")
        ai_controller = area == ("src", "echo_heist", "ai")
        if path.suffix == ".py" and (pure_core or ai_controller):
            for line, module in imported_modules(path, path.read_text(encoding="utf-8")):
                if pure_core and (
                    module == "pygame" or module.startswith(("pygame.", "echo_heist.ui"))
                ):
                    problems.append(f"{relative}:{line}: core imports presentation {module}")
                if ai_controller and module.startswith("echo_heist.core.simulation"):
                    problems.append(f"{relative}:{line}: AI must use observation contracts")

    for directory, paths in by_directory.items():
        if len(paths) > rules["max-files"]:
            problems.append(
                f"{directory.relative_to(ROOT)}: {len(paths)} direct files; "
                f"limit {rules['max-files']}"
            )
    return problems


if __name__ == "__main__":
    failures = check()
    for failure in failures:
        print(failure, file=sys.stderr)
    if not failures:
        print("Structure checks passed (1000 lines/file, 6 direct files/directory).")
    raise SystemExit(bool(failures))
