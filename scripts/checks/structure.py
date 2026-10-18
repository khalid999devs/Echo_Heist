"""Check maintained file budgets, test placement and pure-core imports."""

from __future__ import annotations

import ast
import sys
import tomllib
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORED_SUFFIXES = {".py", ".pyi", ".spec", ".md", ".toml", ".json", ".yml", ".yaml", ".svg"}


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
        if not line_exempt and (path.suffix in AUTHORED_SUFFIXES or path.name == ".gitignore"):
            count = len(path.read_text(encoding="utf-8").splitlines())
            if count > rules["max-lines"]:
                problems.append(f"{relative}: {count} lines; limit {rules['max-lines']}")
        is_test = path.name.startswith("test_") or path.name.endswith("_test.py")
        if (
            path.suffix == ".py"
            and (is_test or path.name in {"tests.py", "conftest.py"})
            and relative.parts[0] != "tests"
        ):
            problems.append(f"{relative}: test files belong under root tests/")
        pure_area = relative.parts[:3] == ("src", "echo_heist", "core")
        if path.suffix == ".py" and pure_area:
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    if name == "pygame" or name.startswith(("pygame.", "echo_heist.ui")):
                        problems.append(
                            f"{relative}:{node.lineno}: core imports presentation {name}"
                        )
        ai_area = relative.parts[:3] == ("src", "echo_heist", "ai")
        if path.suffix == ".py" and ai_area:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                module = node.module if isinstance(node, ast.ImportFrom) else ""
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else []
                if (module and module.startswith("echo_heist.core.simulation")) or any(
                    name.startswith("echo_heist.core.simulation") for name in names
                ):
                    problems.append(f"{relative}:{node.lineno}: AI must use observation contracts")

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
