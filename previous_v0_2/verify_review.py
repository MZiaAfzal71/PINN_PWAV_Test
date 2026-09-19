#!/usr/bin/env python3
"""Verify release integrity and meaningful data invariants without fitting models."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'baseline_v0_1'
def read(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,description):
    if not ok:raise AssertionError(description)
    checks.append(description)
checks=[]

def verify():
    config=json.loads((ROOT/'config.json').read_text())
    manifest=json.loads((BASE/'MANIFEST.json').read_text())
    check(sha(BASE/'MANIFEST.json')==config['baseline_manifest_sha256'],'Parent manifest unchanged')
    for path,meta in manifest['files'].items():
        check(sha(BASE/path)==meta['sha256'],'Unchanged baseline: '+path)
    labels=read(ROOT/'frozen/enthalpy_primary_labels.csv')
    candidates=read(ROOT/'frozen/enthalpy_candidates_reviewed.csv')
    original={r['record_id']:r for r in read(BASE/'frozen/enthalpy_candidates.csv')}
    reviewed={r['record_id']:r for r in candidates}
    assignments={r['molecule_id']:r for r in read(BASE/'frozen/split_assignments.csv')}
    trans={r['record_id']:r for r in read(ROOT/'review/primary_table_transcriptions.csv')}
    identities={r['record_id']:r for r in read(ROOT/'evidence/identity_verification.csv')}
    check(len(candidates)==len(reviewed)==len(original)==751,'All 751 candidate IDs preserved exactly once')
    check(set(reviewed)==set(original),'No silent candidate additions/removals')
    check(len(trans)==38,'38 original current-work table transcriptions')
    check(len(labels)==37,'37 approved labels; source-conflicted ethylenediamine excluded')
    check(len({r['molecule_id'] for r in labels})==36,'36 approved molecular identities')
    check({r['record_id'] for r in labels}=={rid for rid,t in trans.items() if t['decision']=='approve_primary_calorimetry'},'Label export exactly matches review decisions')
    check(len({r['measurement_lineage_id'] for r in labels})==37,'Approved measurement lineages are unique')
    for r in candidates:
        old=original[r['record_id']]
        check(all(r[k]==old[k] for k in ('inchi','molecule_id','split','component_id')),'Identity and split unchanged: '+r['record_id'])
        check(all(r['original_'+k]==old[k] for k in ('H_kJ_mol','T_K','reported_deviation','decision')),'Original label values preserved: '+r['record_id'])
    for r in labels:
        rid=r['record_id'];t=trans[rid];a=assignments[r['molecule_id']]
        check(r['split']==a['split']=='train','Training partition: '+rid)
        check(r['component_id']==a['component_id'],'Frozen component: '+rid)
        check(all(r[k]=='True' for k in ('raw_row_verified','primary_identity_verified','primary_numeric_table_verified','full_primary_methods_verified','independent_of_pressure_verified','training_allowed','table_image_visually_checked')),'Evidence flags: '+rid)
        check(D(r['H_kJ_mol'])==D(t['primary_H'])*D(t['unit_multiplier_to_kJ']) and D(r['H_J_mol'])==1000*D(r['H_kJ_mol']),'Exact enthalpy unit conversion: '+rid)
        check(D(r['reported_deviation'])==D(t['primary_deviation'])*D(t['unit_multiplier_to_kJ']),'Exact deviation unit conversion: '+rid)
        check(D(r['T_K'])==D(t['primary_temperature_C'])+D('273.15')==D('298.15'),'Original measurement temperature: '+rid)
        check(r['temperature_correction_applied']==r['ideal_gas_state_conversion_applied']==r['pressure_curve_used_to_derive_label']==r['benchmark_pressure_used_for_label']=='False','No undocumented thermal/state/pressure-fit conversion: '+rid)
        check(r['thermodynamic_state']=='liquid_to_real_vapor_at_saturation','Saturation state preserved: '+rid)
        check(r['uncertainty_confidence_percent']==r['uncertainty_coverage_factor']=='','No invented confidence level or coverage factor: '+rid)
        if r['uncertainty_kind']=='twice_standard_error_of_mean_random_only':
            check(D(r['random_standard_error_kJ_mol'])*2==D(r['reported_deviation']),'Random SE convention: '+rid)
        else:check(r['random_standard_error_kJ_mol']=='','No invented standard error: '+rid)
        ii=identities[rid]
        check(ii['exact_match']=='True' and ii['primary_name_structure_inchi']==ii['frozen_inchi']==r['inchi'],'Primary-name structure receipt: '+rid)
    old_acn=reviewed['rdr250199#csvline864']
    check(old_acn['training_allowed']=='False' and old_acn['decision']=='hold_secondary_temperature_corrected_value','Older corrected acetonitrile remains quarantined')
    check(old_acn['measurement_lineage_id']!=reviewed['rdr250199#csvline860']['measurement_lineage_id'],'Distinct older and Howard acetonitrile lineage')
    check(reviewed['rdr250199#csvline1276']['training_allowed']=='False','Source-conflicted ethylenediamine excluded from training')
    check(reviewed['rdr250199#csvline2872']['measurement_lineage_id']!=reviewed['rdr250199#csvline2873']['measurement_lineage_id'],'New 1968 bromobutane distinguished from 1966 measurement')
    overlap=read(ROOT/'evidence/source_overlap_check.csv')
    check(all(r['overlaps_any_frozen_pressure_doi']=='False' and json.loads(r['splits_json'])==['train'] for r in overlap),'Newly resolved measurement DOIs do not bridge partitions or overlap pressure DOIs')
    wave=read(ROOT/'review/priority_14_row_decisions.csv')
    check(len(wave)==174 and len({r['molecule_id'] for r in wave})==100,'Priority wave covers 174 rows and 100 training molecules')
    check(len(read(ROOT/'review/source_register.csv'))==14,'All 14 priority references have explicit review status')
    summary=json.loads((ROOT/'frozen/summary.json').read_text())
    check(summary['approved_labels']==len(labels) and summary['approved_training_molecules']==36 and summary['additional_training_molecules_needed']==64,'Summary coverage reconciles')
    check(summary['remaining_quarantined_candidates']==714,'All 714 remaining candidates explicitly withheld')
    check(summary['approved_atomic_components']==len({r['component_id'] for r in labels})==1,'Single training component disclosed')
    check(summary['approved_distinct_temperatures_K']==['298.15'],'Single approved temperature disclosed')
    check(summary['status']=='HOLD_ENTHALPY_PROVENANCE' and config['minimum_independent_training_enthalpy_molecules']==100,'Original feasibility gate retained')
    check(Counter(r['split'] for r in assignments.values())=={'train':492,'validation':106,'test':105},'Original molecular split counts retained')
    check(len(read(BASE/'frozen/test_cold_targets.csv'))==512 and len(read(BASE/'frozen/test_anchors.csv'))==234,'Frozen evaluation records retained')
    result=dict(status='PASS',checks_passed=len(checks),approved_labels=len(labels),approved_training_molecules=36,
      additional_training_molecules_needed=64,scientific_readiness='HOLD_ENTHALPY_PROVENANCE',
      scope='Integrity, mapping and arithmetic checks. Scientific decisions are evidenced manual/AI-assisted inputs, not established by these software checks.')
    return result

if __name__=='__main__':
    result=verify()
    mf=ROOT/'MANIFEST.json'
    if mf.exists():
        data=json.loads(mf.read_text())
        for path,x in data['files'].items():
            if sha(ROOT/path)!=x['sha256']:raise SystemExit('Release hash mismatch: '+path)
        result['manifest_files_verified']=len(data['files'])
    print(json.dumps(result,indent=2))
