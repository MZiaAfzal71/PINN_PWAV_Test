#!/usr/bin/env python3
"""Recheck the extracted JSON-derived rows against the uploaded ThermoML XML.

This verifies archive transcription, not experimental independence or correctness.
The 189 MB archive is not redistributed in this package. Supply the original tgz.
Only Python's standard library is needed for this check.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(8*1024*1024), b''): h.update(c)
    return h.hexdigest()

def close(a, b):
    try: return math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-10)
    except (TypeError, ValueError): return a == b

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=ROOT/'inputs/archive_xml_verification.json')
    args = ap.parse_args()
    config = json.loads((ROOT/'config.json').read_text())
    actual_hash = sha256(args.archive)
    if actual_hash != config['source_archive']['sha256']:
        raise SystemExit('Archive checksum differs from the frozen source.')
    with (ROOT/'inputs/pressure_records.csv').open() as f:
        pressure = [r for r in csv.DictReader(f) if r['primary_candidate']=='True']
    with (ROOT/'inputs/thermoml_enthalpy_records.csv').open() as f:
        enthalpy = list(csv.DictReader(f))
    rows = {r['record_id']:r for r in pressure+enthalpy}
    selected = {r['source_doi'] for r in rows.values()}
    errors, seen, checked = [], set(), []
    studies = set()
    with tarfile.open(args.archive, 'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.xml') or member.name[:-4] not in selected:
                continue
            root = ET.parse(tar.extractfile(member)).getroot()
            for el in root.iter(): el.tag=el.tag.split('}')[-1]
            doi = root.findtext('Citation/sDOI')
            compounds = {c.findtext('RegNum/nOrgNum'):c.findtext('sStandardInChI') for c in root.findall('Compound')}
            studies.add(doi)
            for block in root.findall('PureOrMixtureData'):
                if len(block.findall('Component')) != 1: continue
                inchi = compounds[block.findtext('Component/RegNum/nOrgNum')]
                dn = block.findtext('nPureOrMixtureDataNumber')
                props = {p.findtext('nPropNumber'):p for p in block.findall('Property')}
                var = {v.findtext('nVarNumber'):v for v in block.findall('Variable')}
                for ni, nv in enumerate(block.findall('NumValues'), 1):
                    for pv in nv.findall('PropertyValue'):
                        pn = pv.findtext('nPropNumber')
                        rid = f'{doi}#d{dn}#p{pn}#r{ni}'
                        if rid not in rows: continue
                        seen.add(rid); r = rows[rid]; prop = props[pn]
                        failures = []
                        def check(ok, key):
                            if not ok: failures.append(key)
                        check(inchi==r['inchi'], 'full_inchi')
                        check(prop.findtext('.//ePropName')==r['property_name'], 'property_name')
                        check(prop.findtext('PropPhaseID/ePropPhase')==r['property_phase'], 'property_phase')
                        check(sorted(x.findtext('ePhase') for x in block.findall('PhaseID'))==sorted(json.loads(r['block_phases_json'])), 'block_phases')
                        method = prop.findtext('.//eMethodName') or prop.findtext('.//sMethodName') or ''
                        check(method==r['method'], 'method')
                        value = pv.findtext('nPropValue')
                        check(close(value, r['original_property_value']), 'original_value')
                        target = r.get('p_Pa')
                        check(close(float(value)*1000, target) if target is not None else close(value,r['H_kJ_mol']), 'target_units')
                        states = []
                        for vv in nv.findall('VariableValue'):
                            if var[vv.findtext('nVarNumber')].find('.//eTemperature') is not None:
                                states.append(('variable',vv.findtext('nVarValue')))
                        for co in block.findall('Constraint'):
                            if co.find('.//eTemperature') is not None:
                                states.append(('constraint',co.findtext('nConstraintValue')))
                        check(len(states)==1, 'unique_temperature_state')
                        if len(states)==1:
                            check(close(states[0][1],r['T_K']), 'temperature')
                            check(states[0][0]==r['state_origin'], 'temperature_origin')
                        # Compare every stored scalar leaf in the property-value
                        # metadata, including reported uncertainty and precision.
                        metadata = json.loads(r['original_property_value_metadata_json'])
                        def walk(node, path=''):
                            if isinstance(node,dict):
                                for k,v in node.items(): walk(v, path+'/'+k if path else k)
                            elif isinstance(node,list):
                                # Only an absent list entry needs a separate failure;
                                # scalar leaf checks below cover the common schema.
                                for v in node: walk(v,path)
                            else:
                                vals=[x.text for x in pv.findall(path)]
                                check(any(close(node,v) for v in vals), 'metadata:'+path)
                        walk(metadata)
                        if failures: errors.append({'record_id':rid,'mismatches':failures})
                        else: checked.append(rid)
    missing = sorted(set(rows)-seen)
    report = dict(archive_sha256=actual_hash,comparison='independent XML parsing versus prior JSON-derived CSV',
        checks=['full InChI','property and phase','method','T variable/constraint','value and kPa-to-Pa units','property-value metadata including available uncertainties'],
        pressure_rows_requested=len(pressure),enthalpy_rows_requested=len(enthalpy),xml_studies=len(studies),
        rows_passed=len(checked),mismatch_count=len(errors),missing_count=len(missing),
        mismatches=errors,missing_record_ids=missing,verified_record_ids=sorted(checked),
        certifies_primary_methods_or_independence=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['verified_record_ids','mismatches','missing_record_ids']},indent=2))
    if errors or missing:
        print(json.dumps(errors[:10],indent=2))
        raise SystemExit(1)

if __name__=='__main__': main()
