#!/usr/bin/env python3
"""Scientific release gate. Exit 2 is the expected HOLD for v0.1.0.

This release freezes quarantined candidates, not certified training enthalpies.
Do not change a decision field in-place to bypass provenance requirements.
A reviewed successor version must retain evidence and repeat integrity checks.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    config=json.loads((ROOT/'config.json').read_text())
    manifest=ROOT/'MANIFEST.json'
    if manifest.exists():
        data=json.loads(manifest.read_text())
        for name,expected in data['files'].items():
            if sha(ROOT/name)!=expected['sha256']:
                raise SystemExit('Integrity failure; a frozen file changed: '+name)
    with (ROOT/'frozen/enthalpy_primary_labels.csv').open() as f:labels=list(csv.DictReader(f))
    required=['raw_row_verified','full_primary_methods_verified','independent_of_pressure_verified','training_allowed']
    certified=[r for r in labels if all(r.get(k)=='True' for k in required)]
    molecules={r['molecule_id'] for r in certified}
    train={r['molecule_id'] for r in certified if r['split']=='train'}
    enough=(len(molecules)>=config['minimum_independent_enthalpy_molecules'] and
            len(train)>=config['minimum_independent_training_enthalpy_molecules'])
    status='READY' if enough and len(certified)==len(labels) else 'HOLD_ENTHALPY_PROVENANCE'
    result=dict(status=status,certified_independent_enthalpy_molecules=len(molecules),
        certified_independent_training_enthalpy_molecules=len(train),
        required_total=config['minimum_independent_enthalpy_molecules'],
        required_train=config['minimum_independent_training_enthalpy_molecules'],
        reason='Primary methods, measurement/reference temperature, phase/state, uncertainty convention and pressure-independent correction lineage must be documented per label.',
        next_action='Resolve the source review queue and create a reviewed successor release. Retain current split IDs; if newly discovered lineage bridges splits, embargo affected records or explicitly version the split change before training.')
    print(json.dumps(result,indent=2))
    return 0 if status=='READY' else 2

if __name__=='__main__':sys.exit(main())
