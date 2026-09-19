#!/usr/bin/env python3
"""Reproduce v0.3 exports from frozen identities and evidenced review inputs.
Requires pinned RDKit. This script does not automate scientific judgment.
"""
from pathlib import Path
from collections import Counter
from decimal import Decimal as D
import csv, hashlib, json
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors
ROOT=Path(__file__).resolve().parent
BASE=ROOT/'baseline_v0_1'
PREV=ROOT/'previous_v0_2'
def read(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def save(p,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r));p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def js(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def dec(x):return format(x,'f')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    config=json.loads((ROOT/'config.json').read_text())
    assert sha(BASE/'MANIFEST.json')==config['baseline_manifest_sha256']
    assert sha(PREV/'MANIFEST.json')==config['previous_review_manifest_sha256']
    for rel,meta in json.loads((BASE/'MANIFEST.json').read_text())['files'].items():
        assert sha(BASE/rel)==meta['sha256'],rel
    for rel,meta in json.loads((PREV/'MANIFEST.json').read_text())['files'].items():
        assert sha(ROOT/rel if rel.startswith('baseline_v0_1/') else PREV/rel)==meta['sha256'],rel
    assert rdBase.rdkitVersion==json.loads((BASE/'config.json').read_text())['rdkit_version']
    candidates=read(BASE/'frozen/enthalpy_candidates.csv')
    prior={r['record_id']:r for r in read(PREV/'frozen/enthalpy_candidates_reviewed.csv')}
    sources={r['reference_code']:r for r in read(ROOT/'review/source_register.csv')}
    trans={r['record_id']:r for r in read(ROOT/'review/primary_table_transcriptions.csv')}
    pressure=read(BASE/'frozen/pressure_observations.csv')
    envelopes={}
    for r in pressure:
        mid=r['molecule_id'];t=D(r['T_K']);lo,hi=envelopes.get(mid,(t,t))
        envelopes[mid]=(min(lo,t),max(hi,t))
    revised=[];identities=[];changes=[];lineages=[];nist_checks=[]
    for original in candidates:
        r=original.copy();rid=r['record_id'];codes=json.loads(r['reference_codes_json'])
        matches=[c for c in codes if c in sources]
        r.update(review_wave='not_reviewed' if not matches else 'source_access_review',review_date='',
          original_H_kJ_mol=r['H_kJ_mol'],original_T_K=r['T_K'],original_reported_deviation=r['reported_deviation'],
          original_decision=r['decision'],previous_v0_2_decision=prior[rid]['decision'])
        if matches:
            s=sources[matches[0]]
            r.update(review_reference_code=matches[0],review_date=s['review_date'],primary_source_url=s['primary_url'],
              source_review_status=s['review_status'],decision='hold_'+s['review_status'],decision_reasons=s['table_methods_locator'])
        if rid in trans:
            t=trans[rid];s=sources[t['reference_code']];r.update(t)
            mol=Chem.MolFromSmiles(t['structure_smiles_from_primary_name']);inchi=Chem.MolToInchi(mol)
            assert inchi==r['inchi'],rid
            identities.append(dict(record_id=rid,primary_name=t['primary_compound_name'],reviewed_name_to_smiles=t['structure_smiles_from_primary_name'],
              primary_name_structure_inchi=inchi,frozen_inchi=r['inchi'],exact_match=True,rdkit_version=rdBase.rdkitVersion))
            nist=t['primary_unit']=='US_international_J/g'
            mass=format(Descriptors.MolWt(mol),'.3f') if nist else ''
            scale=D(t['energy_conversion_factor_to_abs_J'])*D(mass)/1000 if nist else D(t['unit_multiplier_to_kJ'])
            h=D(t['primary_H'])*scale
            u=D(t['primary_deviation'])*scale if t['primary_deviation'] else None
            allowed=t['decision']=='approve_primary_calorimetry' and r['split']=='train'
            doi=json.loads(s['candidate_dois_json'])[0]
            lineage=prior[rid].get('measurement_lineage_id') or 'cal_'+hashlib.sha256((doi+'|'+inchi+'|current_measurement').encode()).hexdigest()[:20]
            r.update(source_doi=doi,primary_document_sha256=s['pdf_sha256'],H_kJ_mol=dec(h),H_J_mol=dec(h*1000),T_K=t['primary_temperature_K'],
              unit_multiplier_to_kJ=dec(scale),molar_mass_g_mol=mass,
              reported_deviation=dec(u) if u is not None else '',uncertainty_confidence_percent='',uncertainty_coverage_factor='',
              random_standard_error_kJ_mol=dec(u/2) if t['uncertainty_kind']=='twice_standard_error_of_mean_random_only' else '',
              standard_error_multiplier='2' if t['uncertainty_kind']=='twice_standard_error_of_mean_random_only' else '',
              author_estimated_total_error_kJ_mol=dec(h*D(t['estimated_relative_error_fraction'])) if nist else '',
              source_locator=f"DOI {doi}; p.{t['primary_page']}; Table {t['primary_table']}; {t['primary_compound_name']}",
              full_primary_methods_verified=True,primary_numeric_table_verified=True,primary_identity_verified=True,
              independent_of_pressure_verified=not nist,method='electrical_energy_and_evaporated_mass_calorimetry',
              temperature_status='nominal_historical_scale_temperature' if nist else 'direct_measurement_temperature_restored_from_primary_source',
              measurement_or_reference_temperature='measurement',temperature_correction_applied=False,ideal_gas_state_conversion_applied=False,
              ancillary_apparatus_pressure_used=True,pressure_curve_used_to_derive_label=nist,
              benchmark_pressure_used_for_label='unknown_upstream_ancillary_lineage' if nist else False,
              minimum_replicates_in_reported_mean=t['reported_replicates_minimum'],training_allowed=allowed,measurement_lineage_id=lineage,
              reviewed_by='OpenAI Codex; no independent human sign-off',
              decision_reasons=('primary_calorimetry_verified_with_disclosed_source_quality_limits' if allowed else
                'ancillary_pressure_slope_lineage_and_primary_pool_eligibility_unresolved' if nist else 'source_explicit_unresolved_measurement_conflict'),
              inside_pressure_temperature_envelope=envelopes[r['molecule_id']][0]<=D(r['T_K'])<=envelopes[r['molecule_id']][1])
            changes.append(dict(record_id=rid,name=r['name'],source_doi=doi,compendium_T_K=original['T_K'],primary_T_K=r['T_K'],
              compendium_H_kJ_mol=original['H_kJ_mol'],primary_H_kJ_mol=dec(h),difference_H_kJ_mol=dec(h-D(original['H_kJ_mol'])),
              compendium_deviation=original['reported_deviation'],primary_deviation_kJ_mol=r['reported_deviation'],
              change_basis='Primary specific energy, US electrical-unit conversion, explicit molar mass and nominal historical 25 C; remains held.' if nist else
                'Original published H, deviation and measurement temperature restored; no new temperature extrapolation.',decision=r['decision']))
            lineages.append(dict(record_id=rid,molecule_id=r['molecule_id'],measurement_lineage_id=lineage,primary_doi=doi,
              source_role=t['source_role'],split=r['split'],component_id=r['component_id'],training_allowed=allowed))
            if nist:
                g,b,L=map(D,(t['mean_gamma_intJ_g'],t['beta_intJ_g'],t['primary_H']))
                assert g-b==L,rid
                nist_checks.append(dict(record_id=rid,primary_name=t['primary_compound_name'],mean_gamma_intJ_g=dec(g),beta_intJ_g=dec(b),L_intJ_g=dec(L),
                  gamma_minus_beta_exact=True,beta_fraction_of_L=dec(b/L),molar_mass_g_mol=mass,energy_conversion_factor='1.000165',
                  normalized_H_kJ_mol=dec(h),beta_kJ_mol=dec(b*scale),training_allowed=False))
        elif rid=='rdr250199#csvline864':
            for k in ('decision','decision_reasons','primary_source_url','source_locator','independent_of_pressure_verified','training_allowed',
                      'temperature_status','measurement_or_reference_temperature','measurement_lineage_id','quality_flags'):
                r[k]=prior[rid].get(k,'')
            lineages.append(dict(record_id=rid,molecule_id=r['molecule_id'],measurement_lineage_id=r['measurement_lineage_id'],primary_doi='',
              source_role='older_calorimetry_temperature_corrected_and_quoted',split=r['split'],component_id=r['component_id'],training_allowed=False))
        revised.append(r)
    assert set(trans)=={r['record_id'] for r in revised if r.get('primary_numeric_table_verified') is True}
    labels=[r for r in revised if r.get('training_allowed') is True]
    held_nist=[r for r in revised if r.get('reference_code')=='1947OSB/GIN']
    reviewed_wave=[r for r in revised if any(c in sources for c in json.loads(r['reference_codes_json']))]
    first14={c for c,s in sources.items() if int(s['priority'])<=14}
    first14rows=[r for r in revised if any(c in first14 for c in json.loads(r['reference_codes_json']))]
    save(ROOT/'frozen/enthalpy_candidates_reviewed.csv',revised)
    save(ROOT/'frozen/enthalpy_primary_labels.csv',labels)
    save(ROOT/'frozen/enthalpy_nist_ancillary_hold.csv',held_nist)
    save(ROOT/'review/priority_14_row_decisions.csv',first14rows)
    save(ROOT/'review/all_reviewed_source_rows.csv',reviewed_wave)
    save(ROOT/'review/numeric_changes.csv',changes)
    save(ROOT/'review/measurement_lineages.csv',lineages)
    save(ROOT/'evidence/identity_verification.csv',identities)
    save(ROOT/'evidence/nist_conversion_checks.csv',nist_checks)
    pdois={r['source_doi'] for r in pressure};overlap=[]
    for code,s in sources.items():
        if s['review_status'] not in ('full_primary_review','primary_table_verified_ancillary_lineage_hold'):continue
        doi=json.loads(s['candidate_dois_json'])[0]
        rr=[r for r in revised if r.get('reference_code')==code]
        overlap.append(dict(reference_code=code,measurement_doi=doi,overlaps_any_frozen_pressure_doi=doi in pdois,
          splits_json=json.dumps(sorted({r['split'] for r in rr})),component_ids_json=json.dumps(sorted({r['component_id'] for r in rr})),
          approved_rows=sum(r.get('training_allowed') is True for r in rr),verified_table_rows=len(rr),methods_establish_energy_mass_measurement=True,
          ancillary_pressure_slope_present=code=='1947OSB/GIN',
          review_limit='No DOI overlap does not certify upstream independence; NIST ancillary tables remain untraced. No pressure fits or held-out pressure values used.'))
    save(ROOT/'evidence/source_overlap_check.csv',overlap)
    bymol={}
    for r in labels:bymol.setdefault(r['molecule_id'],[]).append(r)
    save(ROOT/'frozen/training_enthalpy_molecules.csv',[dict(molecule_id=m,inchi=rr[0]['inchi'],name=rr[0]['name'],split=rr[0]['split'],component_id=rr[0]['component_id'],
      approved_label_count=len(rr),record_ids_json=json.dumps([r['record_id'] for r in rr])) for m,rr in sorted(bymol.items())])
    results=[]
    for code,s in sources.items():
        rr=[r for r in reviewed_wave if code in json.loads(r['reference_codes_json'])]
        results.append(dict(priority=s['priority'],reference_code=code,candidate_rows=len(rr),candidate_molecules=len({r['molecule_id'] for r in rr}),
          approved_rows=sum(r.get('training_allowed') is True for r in rr),held_rows=sum(r.get('training_allowed') is not True for r in rr),
          unapproved_molecules_reachable=len({r['molecule_id'] for r in rr}-set(bymol)),review_status=s['review_status'],candidate_dois_json=s['candidate_dois_json'],primary_url=s['primary_url']))
    save(ROOT/'review/priority_source_results.csv',results)
    queue=[]
    for item in read(BASE/'review/prioritized_training_sources.csv'):
        c=item['reference_code'];rr=[r for r in revised if c in json.loads(r['reference_codes_json']) and r['split']=='train']
        remaining={r['molecule_id'] for r in rr}-set(bymol)
        if not remaining:continue
        s=sources.get(c,{})
        queue.append(dict(original_priority=item['priority'],reference_code=c,candidate_rows=len(rr),additional_unapproved_training_molecules=len(remaining),
          row_level_review_status=s.get('review_status','not_reviewed'),primary_url=s.get('primary_url',''),
          caveat='Reachable identities, not guaranteed acceptable labels; overlapping codes must not be summed.'))
    save(ROOT/'review/remaining_verification_queue.csv',queue)
    water=read(ROOT/'review/1971_methoxyethanol_correction_runs.csv');checks=[]
    for r in water:
        s=sum(D(r[k]) for k in ('apparent_H_kJ_mol','condensation_correction_kJ_mol','dissolution_correction_kJ_mol'))
        checks.append(dict(run=r['run'],sum_terms_kJ_mol=dec(s),printed_corrected_H_kJ_mol=r['corrected_H_kJ_mol'],
          difference_kJ_mol=dec(s-D(r['corrected_H_kJ_mol'])),terms_match=s==D(r['corrected_H_kJ_mol'])))
        assert checks[-1]['terms_match']
    save(ROOT/'evidence/water_correction_checks.csv',checks)
    mean=sum(D(r['corrected_H_kJ_mol']) for r in water)/len(water)
    js(ROOT/'evidence/water_correction_summary.json',dict(arithmetic_mean_of_printed_corrected_runs_kJ_mol=dec(mean),published_fit_H_kJ_mol='45.17',
      difference_from_published_fit_kJ_mol=dec(mean-D('45.17')),interpretation='Published result follows a joint fit for H and water solution enthalpy. Simple mean of rounded run values is not claimed to reproduce that fit exactly.',
      water_specific_enthalpy_used_as_printed_kJ_g='2.433',original_raw_unrounded_runs_available=False))
    oldlabels=read(PREV/'frozen/enthalpy_primary_labels.csv')
    summary=dict(version='0.3.0',review_date=config['review_date'],status='HOLD_ENTHALPY_PROVENANCE',baseline_unchanged=True,previous_release_unchanged=True,
      source_codes_with_review_status=len(sources),reviewed_source_candidate_rows=len(reviewed_wave),reviewed_source_candidate_molecules=len({r['molecule_id'] for r in reviewed_wave}),
      primary_measurement_papers_reviewed_for_candidate_rows=len(overlap),referenced_apparatus_papers_verified=2,lineage_comparison_papers=1,metrology_references=1,
      direct_measurement_table_rows_verified=len(trans),new_table_rows_verified=sum(t['review_wave']=='wave2' for t in trans.values()),
      approved_labels=len(labels),new_approved_labels=len(labels)-len(oldlabels),approved_training_molecules=len(bymol),
      new_approved_training_molecules=len(set(bymol)-{r['molecule_id'] for r in oldlabels}),approved_validation_labels=0,approved_test_labels=0,
      nist_rows_normalized_but_held=len(held_nist),remaining_quarantined_candidates=len(revised)-len(labels),
      primary_coverage_required_training_molecules=config['minimum_independent_training_enthalpy_molecules'],additional_training_molecules_needed=max(0,100-len(bymol)),
      approved_distinct_temperatures_K=sorted({r['T_K'] for r in labels}),approved_atomic_components=len({r['component_id'] for r in labels}),approved_laboratories=1,
      approved_rows_inside_pressure_temperature_envelope=sum(r['inside_pressure_temperature_envelope'] for r in labels),
      nist_beta_percent_of_H_min=min(float(r['beta_fraction_of_L'])*100 for r in nist_checks),nist_beta_percent_of_H_max=max(float(r['beta_fraction_of_L'])*100 for r in nist_checks),
      decision_counts=dict(sorted(Counter(r['decision'] for r in revised).items())),split_counts={'train':492,'validation':106,'test':105},
      primary_test_episodes=78,primary_test_anchor_rows=234,primary_test_target_rows=512,model_fits_performed=False,test_targets_used_for_label_decisions=False,
      note='Primary labels remain one-laboratory, one-component, one-temperature data. NIST rows pass main-table checks but remain held for ancillary lineage. Eligibility does not mean all systematic errors are quantified.')
    js(ROOT/'frozen/summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
