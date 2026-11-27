"""Enforce clean architecture layer import boundaries."""

import ast
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"

FORBIDDEN_APP_LIBS = frozenset(
    {
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "anthropic",
        "google",
        "httpx",
        "aiosqlite",
        "uvicorn",
    }
)


def _iter_python_files(layer: str) -> list[Path]:
    layer_dir = APP_ROOT / layer
    if not layer_dir.exists():
        return []
    return sorted(layer_dir.rglob("*.py"))


def _extract_imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                modules.append(f".{node.module or ''}")
            elif node.module:
                modules.append(node.module)
    return modules


def test_domain_imports_only_stdlib() -> None:
    """Domain layer must only import Python stdlib or itself."""
    violations: list[str] = []
    for path in _iter_python_files("domain"):
        for mod in _extract_imports(path):
            if mod.startswith(".") or mod == "app.domain" or mod.startswith("app.domain."):
                continue
            top_level = mod.split(".")[0]
            if top_level not in sys.stdlib_module_names:
                violations.append(f"{path.relative_to(APP_ROOT)}: imports '{mod}'")
    assert not violations, "Domain layer import violations:\n" + "\n".join(violations)


def test_application_does_not_import_outer_layers_or_frameworks() -> None:
    """Application layer must not import infrastructure, interfaces, or web/DB SDKs."""
    forbidden_app_prefixes = (
        "app.infrastructure",
        "app.interfaces",
        "app.config",
        "app.composition",
        "app.main",
    )
    violations: list[str] = []
    for path in _iter_python_files("application"):
        for mod in _extract_imports(path):
            if mod.startswith(forbidden_app_prefixes):
                violations.append(f"{path.relative_to(APP_ROOT)}: imports '{mod}'")
            top_level = mod.split(".")[0]
            if top_level in FORBIDDEN_APP_LIBS:
                violations.append(f"{path.relative_to(APP_ROOT)}: imports '{mod}'")
    assert not violations, "Application layer import violations:\n" + "\n".join(violations)


def test_infrastructure_does_not_import_interfaces() -> None:
    """Infrastructure layer must not depend on interfaces, composition, or main."""
    forbidden_prefixes = ("app.interfaces", "app.composition", "app.main")
    violations: list[str] = []
    for path in _iter_python_files("infrastructure"):
        for mod in _extract_imports(path):
            if mod.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(APP_ROOT)}: imports '{mod}'")
    assert not violations, "Infrastructure layer import violations:\n" + "\n".join(violations)


def test_interfaces_does_not_import_infrastructure() -> None:
    """Interfaces layer must not import infrastructure internals (use composition.py)."""
    violations: list[str] = []
    for path in _iter_python_files("interfaces"):
        for mod in _extract_imports(path):
            if mod.startswith("app.infrastructure"):
                violations.append(f"{path.relative_to(APP_ROOT)}: imports '{mod}'")
    assert not violations, "Interfaces layer import violations:\n" + "\n".join(violations)
