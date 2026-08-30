import ast
from pathlib import Path

DOMAIN = Path("src/social_cybernetics/domain")
FORBIDDEN = {"mesa", "pydantic", "pandas", "solara"}
PROJECT_1_AGENT_FIELDS = {
    "AgentState": {"agent_id", "energy", "alive"},
    "AgentSnapshot": {"tick", "agent_id", "position", "energy", "alive"},
}


def modules_in(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_domain_has_no_framework_imports() -> None:
    for path in DOMAIN.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert modules_in(tree).isdisjoint(FORBIDDEN), path


def test_project_1_agent_state_contains_no_dormant_future_fields() -> None:
    tree = ast.parse((DOMAIN / "types.py").read_text(encoding="utf-8"))
    classes = {
        node.name: {
            statement.target.id
            for statement in node.body
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name in PROJECT_1_AGENT_FIELDS
    }

    assert classes == PROJECT_1_AGENT_FIELDS


def test_scientific_code_does_not_use_global_randomness() -> None:
    violations: list[str] = []
    for path in DOMAIN.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            direct_random = isinstance(owner, ast.Name) and owner.id == "random"
            numpy_random = (
                isinstance(owner, ast.Attribute)
                and isinstance(owner.value, ast.Name)
                and owner.value.id == "np"
                and owner.attr == "random"
            )
            if direct_random or numpy_random:
                violations.append(f"{path}:{node.lineno}")
    assert violations == []
