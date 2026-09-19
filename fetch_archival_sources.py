#!/usr/bin/env python3
"""Optionally download archival PDFs outside this immutable release."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
out = args.out.resolve()
if out == ROOT or ROOT in out.parents:
    raise SystemExit("Choose a download folder outside the release.")
out.mkdir(parents=True, exist_ok=True)

documents = json.loads((ROOT / "evidence" / "archival_document_register.json").read_text(encoding="utf-8"))
for document in documents:
    destination = out / (document["source_key"].lower() + ".pdf")
    try:
        data = destination.read_bytes() if destination.exists() else urllib.request.urlopen(document["download_url"], timeout=90).read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != document["sha256"]:
            print("HASH_MISMATCH", document["source_key"], digest)
            continue
        if not destination.exists():
            destination.write_bytes(data)
        print("VERIFIED", document["source_key"], destination)
    except Exception as error:
        print("UNAVAILABLE", document["source_key"], type(error).__name__)
