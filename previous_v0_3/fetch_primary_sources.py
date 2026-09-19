#!/usr/bin/env python3
"""Download ten publicly available original papers for local reinspection.

Downloads go OUTSIDE the frozen release. No publisher PDF is redistributed in
the data bundle. A changed hash requires review, not automatic acceptance.
"""
from pathlib import Path
import argparse, hashlib, json, urllib.request
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
out=args.out.resolve()
if out==ROOT or ROOT in out.parents:raise SystemExit('Choose an evidence-download folder outside the immutable release.')
out.mkdir(parents=True,exist_ok=True)
for r in json.loads((ROOT/'evidence/primary_document_register.json').read_text()):
    dest=out/r['filename']
    try:
        data=dest.read_bytes() if dest.exists() else urllib.request.urlopen(r['url'],timeout=45).read()
        if hashlib.sha256(data).hexdigest()!=r['sha256']:
            print('HASH_MISMATCH',r['filename']);continue
        if not dest.exists():dest.write_bytes(data)
        print('VERIFIED',r['filename'])
    except Exception as e:print('UNAVAILABLE',r['filename'],type(e).__name__)
