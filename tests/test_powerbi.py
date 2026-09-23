import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"


def test_report_files_match_official_schemas():
    folder = ROOT / "tests/schemas"
    index = json.loads((folder / "index.json").read_text())
    registry = Registry().with_resources(
        (url, Resource.from_contents(json.loads((folder / path).read_text()))) for url, path in index.items()
    )
    paths = list(PBI.rglob("*.json")) + list(PBI.rglob("*.pbir"))
    for path in paths:
        obj = json.loads(path.read_text())
        if "$schema" in obj:
            schema = registry.contents(obj["$schema"])
            validator = jsonschema.validators.validator_for(schema)(schema, registry=registry)
            errors = list(validator.iter_errors(obj))
            assert not errors, f"{path}: {[e.message for e in errors]}"


def test_model_and_visual_references():
    model = json.loads((PBI / "SaaSIntelligence.SemanticModel/model.bim").read_text())["model"]
    tables = {t["name"]: t for t in model["tables"]}
    for rel in model["relationships"]:
        for side in ["from", "to"]:
            assert rel[side + "Column"] in [c["name"] for c in tables[rel[side + "Table"]]["columns"]]
        assert rel["crossFilteringBehavior"] == "oneDirection"

    def check(obj):
        if isinstance(obj, dict):
            for kind, collection in [("Measure", "measures"), ("Column", "columns")]:
                if kind in obj and isinstance(obj[kind], dict) and "Property" in obj[kind]:
                    expr = obj[kind]
                    entity = expr["Expression"]["SourceRef"]["Entity"]
                    assert expr["Property"] in [c["name"] for c in tables[entity][collection]]
            for v in obj.values():
                check(v)
        elif isinstance(obj, list):
            for v in obj:
                check(v)

    for p in (PBI / "SaaSIntelligence.Report").rglob("*.json"):
        check(json.loads(p.read_text()))
    role = model["roles"][0]
    permissions = {p["name"]: p["filterExpression"] for p in role["tablePermissions"]}
    assert "USERPRINCIPALNAME()" in permissions["Account"]
    assert permissions["Marketing"] == "FALSE()"
    assert not any(t.startswith("mart_") for t in tables)  # No disconnected aggregate RLS bypass.


def test_dax_copy_and_half_open_refresh_filter():
    model = json.loads((PBI / "SaaSIntelligence.SemanticModel/model.bim").read_text())["model"]
    text = (PBI / "measures.dax").read_text()
    for t in model["tables"]:
        for m in t.get("measures", []):
            assert m["expression"] in text
    events = next(t for t in model["tables"] if t["name"] == "Events")
    expr = events["partitions"][0]["source"]["expression"]
    assert "[occurred_at] >= RangeStart and [occurred_at] < RangeEnd" in expr
