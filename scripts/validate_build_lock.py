#!/usr/bin/env python3
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key or not value:
            raise ValueError(f"Invalid version lock line: {raw_line!r}")
        values[key] = value
    return values


versions = read_env(ROOT / "build" / "versions.env")
manifest = json.loads((ROOT / "build" / "image-manifest.json").read_text(encoding="utf-8"))
apps = json.loads((ROOT / "build" / "apps.json").read_text(encoding="utf-8"))

assert manifest["major_version"] == 16
assert manifest["builder"]["commit"] == versions["FRAPPE_DOCKER_COMMIT"]
assert manifest["runtime"]["python"] == versions["PYTHON_VERSION"]
assert manifest["runtime"]["node"] == versions["NODE_VERSION"]
assert manifest["runtime"]["mariadb"] == versions["MARIADB_VERSION"]

for app in ("frappe", "erpnext", "hrms", "payments"):
    prefix = app.upper()
    assert manifest["apps"][app]["ref"] == versions[f"{prefix}_REF"]
    assert manifest["apps"][app]["commit"] == versions[f"{prefix}_COMMIT"]
    assert re.fullmatch(r"[0-9a-f]{40}", versions[f"{prefix}_COMMIT"])

app_by_name = {entry["url"].rstrip("/").rsplit("/", 1)[-1]: entry for entry in apps}
assert set(app_by_name) == {"erpnext", "hrms", "payments"}
for app in ("erpnext", "hrms", "payments"):
    assert app_by_name[app]["branch"] == versions[f"{app.upper()}_REF"]

print("build lock: ok")
