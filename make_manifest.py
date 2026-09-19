#!/usr/bin/env python3
"""Create the v0.5 release manifest after verification receipts exist."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


files = {}
for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "MANIFEST.json"):
    relative = path.relative_to(ROOT).as_posix()
    files[relative] = {"bytes": path.stat().st_size, "sha256": sha256(path)}

content_fingerprint = hashlib.sha256(
    "\n".join(f"{path}\t{meta['sha256']}" for path, meta in files.items()).encode("utf-8")
).hexdigest()
manifest = {
    "version": "0.5.0",
    "review_date": "2026-09-18",
    "release_id": "enthalpy-source-review-v0.5.0-" + content_fingerprint[:16],
    "scientific_readiness": "HOLD_ENTHALPY_PROVENANCE",
    "content_fingerprint_sha256": content_fingerprint,
    "files": files,
}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in manifest.items() if key != "files"} | {"files": len(files)}, indent=2, sort_keys=True))
