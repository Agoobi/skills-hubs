import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
ids: set[str] = set()

for skill in MANIFEST["skills"]:
    skill_id = skill["id"]
    if skill_id in ids:
        raise SystemExit(f"duplicate skill id: {skill_id}")
    ids.add(skill_id)
    path = Path(skill["path"])
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"unsafe skill path: {path}")
    content = (ROOT / path / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([^\n]+)$", content)
    if match is None or match.group(1).strip() != skill_id:
        raise SystemExit(f"frontmatter name does not match id: {skill_id}")

print(f"validated {len(ids)} skills")
