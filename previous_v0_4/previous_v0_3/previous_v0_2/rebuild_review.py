#!/usr/bin/env python3
"""Rebuild curated exports from immutable v0.1 plus the evidenced review inputs.

Requires the RDKit version pinned by baseline_v0_1/requirements.txt. Rebuilding
does not obtain papers or automate scientific judgment: transcriptions and
decisions are review inputs, with document URLs, hashes and page locators.
"""
from pathlib import Path
import csv, hashlib, json
from collections import Counter
from decimal import Decimal
from rdkit import Chem, rdBase

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'baseline_v0_1'

def read(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))

def save(p,rows,fields=None):
    p.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def js(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def dec(x):return format(x,'f')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    config=json.loads((ROOT/'config.json').read_text())
    assert sha(BASE/'MANIFEST.json')==config['baseline_manifest_sha256']
    for p,x in json.loads((BASE/'MANIFEST.json').read_text())['files'].items():
        assert sha(BASE/p)==x['sha256'],f'Baseline changed: {p}'
    assert rdBase.rdkitVersion==json.loads((BASE/'config.json').read_text())['rdkit_version']
    candidates=read(BASE/'frozen/enthalpy_candidates.csv')
    sources={r['reference_code']:r for r in read(ROOT/'review/source_register.csv')}
    trans={r['record_id']:r for r in read(ROOT/'review/primary_table_transcriptions.csv')}
    primary_dois={json.loads(r['candidate_dois_json'])[0] for r in sources.values() if r['review_status']=='full_primary_review'}
    pressure=read(BASE/'frozen/pressure_observations.csv')
    envelopes={}
    for r in pressure:
        mid=r['molecule_id'];t=Decimal(r['T_K'])
        lo,hi=envelopes.get(mid,(t,t));envelopes[mid]=(min(lo,t),max(hi,t))
    revised=[];wave=[];identities=[];changes=[];lineages=[]
    for original in candidates:
        r=original.copy();rid=r['record_id'];codes=json.loads(r['reference_codes_json'])
        priorities=[x for x in codes if x in sources]
        r.update(review_wave='priority_14' if priorities else 'not_in_this_wave',
          review_date=config['review_date'] if priorities else '',
          original_H_kJ_mol=r['H_kJ_mol'],original_T_K=r['T_K'],
          original_reported_deviation=r['reported_deviation'],original_decision=r['decision'])
        if priorities:
            source=sources[priorities[0]]
            r.update(review_reference_code=priorities[0],primary_source_url=source['primary_url'],
              source_review_status=source['review_status'],decision='hold_'+source['review_status'],
              decision_reasons=source['table_methods_locator'])
        if rid in trans:
            t=trans[rid];source=sources[t['reference_code']]
            molecule=Chem.MolFromSmiles(t['structure_smiles_from_primary_name'])
            actual=Chem.MolToInchi(molecule)
            assert actual==r['inchi'],f'Primary identity does not match frozen InChI: {rid}'
            identities.append(dict(record_id=rid,primary_name=t['primary_compound_name'],
              reviewed_name_to_smiles=t['structure_smiles_from_primary_name'],
              primary_name_structure_inchi=actual,frozen_inchi=r['inchi'],exact_match=True,
              rdkit_version=rdBase.rdkitVersion))
            scale=Decimal(t['unit_multiplier_to_kJ'])
            h=Decimal(t['primary_H'])*scale;u=Decimal(t['primary_deviation'])*scale
            doi=json.loads(source['candidate_dois_json'])[0]
            lineage='cal_'+hashlib.sha256((doi+'|'+r['inchi']+'|current_measurement').encode()).hexdigest()[:20]
            allowed=t['decision']=='approve_primary_calorimetry' and r['split']=='train'
            kind=t['uncertainty_kind']
            r.update(t)
            r.update(source_doi=doi,primary_document_sha256=source['pdf_sha256'],
              H_kJ_mol=dec(h),H_J_mol=dec(h*1000),T_K=t['primary_temperature_K'],
              reported_deviation=dec(u),uncertainty_kind=kind,
              uncertainty_confidence_percent='',uncertainty_coverage_factor='',
              random_standard_error_kJ_mol=dec(u/2) if kind=='twice_standard_error_of_mean_random_only' else '',
              standard_error_multiplier='2' if kind=='twice_standard_error_of_mean_random_only' else '',
              source_locator=f"DOI {doi}; p.{t['primary_page']}; Table {t['primary_table']}; {t['primary_compound_name']}",
              full_primary_methods_verified=True,primary_numeric_table_verified=True,
              primary_identity_verified=True,independent_of_pressure_verified=True,
              method='electrical_compensation_vaporization_calorimetry',
              temperature_status='direct_measurement_temperature_restored_from_primary_source',
              measurement_or_reference_temperature='measurement',
              temperature_correction_applied=False,ideal_gas_state_conversion_applied=False,
              ancillary_apparatus_pressure_used=True,pressure_curve_used_to_derive_label=False,
              benchmark_pressure_used_for_label=False,minimum_replicates_in_reported_mean=5,
              training_allowed=allowed,measurement_lineage_id=lineage,
              reviewed_by='OpenAI Codex; no independent human sign-off',
              decision_reasons=('primary_table_methods_identity_state_uncertainty_and_lineage_verified' if allowed else 'source_explicit_unresolved_measurement_conflict'),
              inside_pressure_temperature_envelope=envelopes[r['molecule_id']][0]<=Decimal(r['T_K'])<=envelopes[r['molecule_id']][1])
            changes.append(dict(record_id=rid,name=r['name'],source_doi=doi,
              compendium_T_K=original['T_K'],primary_T_K=r['T_K'],
              compendium_H_kJ_mol=original['H_kJ_mol'],primary_H_kJ_mol=r['H_kJ_mol'],
              difference_H_kJ_mol=dec(h-Decimal(original['H_kJ_mol'])),
              compendium_deviation=original['reported_deviation'],primary_deviation_kJ_mol=dec(u),
              change_basis='original measured temperature, original numerical precision and exact unit conversion; no temperature adjustment of enthalpy',
              decision=r['decision']))
            lineages.append(dict(record_id=rid,molecule_id=r['molecule_id'],measurement_lineage_id=lineage,
              primary_doi=doi,source_role='current_work_direct_calorimetry',split=r['split'],component_id=r['component_id']))
        elif rid=='rdr250199#csvline864':
            r.update(decision='hold_secondary_temperature_corrected_value',
              decision_reasons='Iwanciow 1950 measurement at 50–80°C, corrected by later work and quoted in Howard/Wadsö Table 2; original correction chain not verified',
              primary_source_url='https://actachemscand.ki.ku.dk/pdf/acta_vol_24_p0145-0149.pdf',
              source_locator='Howard and Wadsö 1970 p.147 Table 2, calorimetric column, footnote h',
              independent_of_pressure_verified=False,training_allowed=False,
              temperature_status='reference_temperature_after_unverified_correction',
              measurement_or_reference_temperature='reference',
              measurement_lineage_id='secondary_1950IWA_corrected_later_quoted_1970HOW',
              quality_flags='Not a second Howard/Wadsö experiment; not merged with csvline860.')
            lineages.append(dict(record_id=rid,molecule_id=r['molecule_id'],measurement_lineage_id=r['measurement_lineage_id'],
              primary_doi='',source_role='older_calorimetry_temperature_corrected_and_quoted',split=r['split'],component_id=r['component_id']))
        revised.append(r)
        if priorities:wave.append(r)
    assert set(trans)=={r['record_id'] for r in revised if r.get('primary_numeric_table_verified') is True}
    labels=[r for r in revised if r.get('training_allowed') is True]
    frozen=ROOT/'frozen';frozen.mkdir(exist_ok=True)
    save(frozen/'enthalpy_candidates_reviewed.csv',revised)
    save(frozen/'enthalpy_primary_labels.csv',labels)
    save(ROOT/'review/priority_14_row_decisions.csv',wave)
    save(ROOT/'review/numeric_changes.csv',changes)
    save(ROOT/'review/measurement_lineages.csv',lineages)
    save(ROOT/'evidence/identity_verification.csv',identities)
    # Every pressure source of a molecule participates; only source identifiers
    # and temperature coverage are used here, never a pressure fit or residual.
    p_dois={r['source_doi'] for r in pressure}
    source_check=[]
    for code,s in sources.items():
        if s['review_status']!='full_primary_review':continue
        doi=json.loads(s['candidate_dois_json'])[0]
        rr=[r for r in labels if r['reference_code']==code]
        source_check.append(dict(reference_code=code,measurement_doi=doi,
          overlaps_any_frozen_pressure_doi=doi in p_dois,
          splits_json=json.dumps(sorted({r['split'] for r in rr})),
          component_ids_json=json.dumps(sorted({r['component_id'] for r in rr})),
          approved_rows=len(rr),methods_establish_energy_mass_measurement=True,
          review_limit='No DOI overlap is a supporting check; methods and correction lineage establish operational independence. Laboratory/systematic independence is not asserted.'))
    save(ROOT/'evidence/source_overlap_check.csv',source_check)
    bymol={}
    for r in labels:bymol.setdefault(r['molecule_id'],[]).append(r)
    molecules=[]
    for mid,rr in sorted(bymol.items()):
        molecules.append(dict(molecule_id=mid,inchi=rr[0]['inchi'],name=rr[0]['name'],split=rr[0]['split'],
          component_id=rr[0]['component_id'],approved_label_count=len(rr),
          record_ids_json=json.dumps([r['record_id'] for r in rr])))
    save(frozen/'training_enthalpy_molecules.csv',molecules)
    pending=[]
    approved_ids=set(bymol)
    for code,s in sources.items():
        rr=[r for r in wave if code in json.loads(r['reference_codes_json'])]
        pending.append(dict(priority=s['priority'],reference_code=code,candidate_rows=len(rr),
          candidate_molecules=len({r['molecule_id'] for r in rr}),
          approved_rows=sum(r.get('training_allowed') is True for r in rr),
          held_rows=sum(r.get('training_allowed') is not True for r in rr),
          unapproved_molecules_reachable=len({r['molecule_id'] for r in rr}-approved_ids),
          review_status=s['review_status'],candidate_dois_json=s['candidate_dois_json'],primary_url=s['primary_url']))
    save(ROOT/'review/priority_source_results.csv',pending)
    base_summary=json.loads((BASE/'frozen/summary.json').read_text())
    summary=dict(version='0.2.0',review_date=config['review_date'],
      status='HOLD_ENTHALPY_PROVENANCE',baseline_unchanged=True,
      priority_codes_reviewed_for_access_and_identity=len(sources),priority_candidate_rows=len(wave),
      priority_candidate_molecules=len({r['molecule_id'] for r in wave}),
      full_measurement_papers_verified=4,referenced_apparatus_papers_verified=2,
      direct_measurement_table_rows_verified=len(trans),approved_labels=len(labels),
      approved_training_molecules=len(bymol),approved_validation_labels=0,approved_test_labels=0,
      remaining_quarantined_candidates=len(revised)-len(labels),
      primary_coverage_required_training_molecules=100,additional_training_molecules_needed=100-len(bymol),
      approved_distinct_temperatures_K=sorted({r['T_K'] for r in labels}),
      approved_atomic_components=len({r['component_id'] for r in labels}),
      approved_laboratories=1,
      approved_rows_inside_pressure_temperature_envelope=sum(r['inside_pressure_temperature_envelope'] for r in labels),
      decision_counts=dict(sorted(Counter(r['decision'] for r in revised).items())),
      split_counts={r['split']:r['molecules'] for r in base_summary['split_counts']},
      cold_episode_counts={r['split']:r['cold_episodes'] for r in base_summary['split_counts']},
      primary_test_target_rows=512,model_fits_performed=False,
      note='37 labels represent 36 molecular identities, not 37 independent laboratories or source components. Verified provenance does not establish universal accuracy or ideal-vapor validity.')
    js(frozen/'summary.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
