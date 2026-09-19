#!/usr/bin/env python3
"""Exit 2 means the retained scientific feasibility gate is not yet satisfied."""
from pathlib import Path
import csv, hashlib, json, sys
ROOT=Path(__file__).resolve().parent
def main():
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    for path,x in manifest['files'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=x['sha256']:
            raise SystemExit('Release integrity failure: '+path)
    with (ROOT/'frozen/enthalpy_primary_labels.csv').open() as f: rows=list(csv.DictReader(f))
    required=('raw_row_verified','primary_identity_verified','primary_numeric_table_verified','full_primary_methods_verified','independent_of_pressure_verified','training_allowed')
    approved=[r for r in rows if all(r.get(k)=='True' for k in required) and r['decision']=='approve_primary_calorimetry' and r['split']=='train']
    config=json.loads((ROOT/'config.json').read_text());n=len({r['molecule_id'] for r in approved})
    ready=(len(approved)==len(rows) and n>=config['minimum_independent_training_enthalpy_molecules'] and n>=config['minimum_independent_enthalpy_molecules'])
    result=dict(status='READY' if ready else 'HOLD_ENTHALPY_PROVENANCE',approved_labels=len(approved),
      approved_training_molecules=n,required_training_molecules=config['minimum_independent_training_enthalpy_molecules'],
      additional_training_molecules_needed=max(0,config['minimum_independent_training_enthalpy_molecules']-n),
      reason='The 100-training-molecule project feasibility gate is unchanged; source access and lineage remain incomplete.')
    print(json.dumps(result,indent=2));return 0 if ready else 2
if __name__=='__main__':sys.exit(main())
