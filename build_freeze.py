#!/usr/bin/env python3
"""Freeze a conservative pressure/enthalpy curation snapshot; never train a model.

Run with Python 3.12, numpy 2.3.5, pandas 2.2.3 and rdkit 2025.09.6.
Input files are preserved byte-for-byte. Full InChI equality remains the join key.
Structural fingerprints and connectivity keys are grouping tools, NOT join keys.
"""
import argparse
import ast
import collections
import csv
import hashlib
import json
import math
import pathlib
import re
import statistics
import sys

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import rdFingerprintGenerator, rdMolDescriptors

RDLogger.DisableLog('rdApp.*')
ROOT = pathlib.Path(__file__).resolve().parent

def digest(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def uid(prefix, value):
    return prefix + hashlib.sha256(value.encode()).hexdigest()[:16]

def js(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def dump(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True)+'\n')

def read(name):
    return pd.read_csv(ROOT/'inputs'/name, keep_default_na=False, low_memory=False, float_precision='round_trip')

def save(p, rows, columns=None):
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(p, index=False, lineterminator='\n', float_format='%.12g')
    else:
        pd.DataFrame(rows, columns=columns).to_csv(p, index=False, lineterminator='\n', float_format='%.12g')

def number(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return math.nan

def finite(v):
    return math.isfinite(number(v))

def codes(v):
    try:
        x = ast.literal_eval(v)
        return sorted(set(str(z).strip() for z in x)) if isinstance(x, list) else []
    except (ValueError, SyntaxError, TypeError):
        return []

def levels(ts, tolerance=0.1):
    out = []
    for t in sorted(set(float(t) for t in ts)):
        if not out or t-out[-1][0] > tolerance+1e-9:
            out.append([t])
        else:
            out[-1].append(t)
    return out

def coverage(ts):
    ls = levels(ts)
    med = [statistics.median(x) for x in ls]
    lo, hi = min(med), max(med)
    warm = [j for j,t in enumerate(med) if t >= lo+.7*(hi-lo)-1e-9]
    cold = [j for j,t in enumerate(med) if t <= lo+.3*(hi-lo)+1e-9]
    return dict(T_min_K=lo,T_max_K=hi,T_span_K=hi-lo,temperature_levels=len(ls),
                warm_levels=len(warm),cold_levels=len(cold),
                episode_eligible=len(ls)>=6 and hi-lo>=30-1e-9 and len(warm)>=3 and len(cold)>=2)

class UnionFind:
    def __init__(self, ids):
        self.p = {x:x for x in ids}
    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a
    def union(self,a,b):
        aa,bb = self.find(a),self.find(b)
        self.p[max(aa,bb)] = min(aa,bb)

def molecular_review(P):
    rows, mols = [], {}
    acid = Chem.MolFromSmarts('[CX3](=O)[OX2H1]')
    for i,g in P.groupby('inchi',sort=True):
        m = Chem.MolFromInchi(i,sanitize=True,removeHs=True)
        issues = []
        row = dict(molecule_id=uid('mol_',i),inchi=i,source_name=g['name'].iloc[0],
                   source_inchikeys_json=js(sorted(set(g.inchikey))),rdkit_version=rdBase.rdkitVersion)
        if m is None:
            issues.append('structure_parse_failed')
        else:
            ik = Chem.MolToInchiKey(m)
            rt = Chem.MolToInchi(m)
            potential = list(Chem.FindPotentialStereo(m))
            unspecified = sum(str(x.specified)=='Unspecified' for x in potential)
            rad = sum(a.GetNumRadicalElectrons() for a in m.GetAtoms())
            fragments = len(Chem.GetMolFrags(m))
            formal_charge = Chem.GetFormalCharge(m)
            atom_charge = any(a.GetFormalCharge()!=0 for a in m.GetAtoms())
            acid_match = m.HasSubstructMatch(acid)
            if rt != i: issues.append('inchi_roundtrip_mismatch')
            if set(g.inchikey) != {ik}: issues.append('inchikey_mismatch')
            if formal_charge: issues.append('nonneutral_graph')
            if fragments != 1: issues.append('disconnected_graph')
            if rad: issues.append('radical_graph')
            if unspecified: issues.append('unspecified_stereochemistry')
            if acid_match: issues.append('carboxylic_acid_association_review')
            # Charge-separated resonance representations of neutral nitro compounds
            # are retained; net charge, not individual atom charge, defines this gate.
            row.update(canonical_isomeric_smiles=Chem.MolToSmiles(m),rdkit_inchi=rt,
                       inchikey=ik,connectivity_key=ik.split('-')[0],
                       formula=rdMolDescriptors.CalcMolFormula(m),fragments=fragments,
                       net_formal_charge=formal_charge,contains_charged_atoms=atom_charge,
                       radical_electrons=rad,potential_stereo_count=len(potential),
                       unspecified_stereo_count=unspecified,carboxylic_acid=acid_match)
            mols[i] = m
        row.update(exclusion_reasons=';'.join(issues),structure_eligible=not issues,
                   physical_sample_identity_verified=False)
        rows.append(row)
    return pd.DataFrame(rows),mols

def review_labels(H,N,P,M,source_meta):
    xml = json.loads((ROOT/'inputs/archive_xml_verification.json').read_text())
    if xml['mismatch_count'] or xml['missing_count']:
        raise AssertionError('Archive verification failed.')
    xml_verified = set(xml['verified_record_ids'])
    good = set(M[M.structure_eligible].inchi)
    pressure_ids = set(P.inchi)
    graph_reason = dict(zip(M.inchi,M.exclusion_reasons))
    envelopes = {i:(float(g.T_K.min()),float(g.T_K.max())) for i,g in P.groupby('inchi')}
    raw = list(csv.DictReader(open(ROOT/'inputs/ChickosAcreeCompendiumVaporization.csv',newline='')))
    decisions, checks = [], []
    for r in H.to_dict('records'):
        orig = raw[int(r['csv_line_1based'])-2]
        pairs = [('Enthalpy','H_reported_kJ_mol'),('Tm (K)','T_reported_K'),('Hvap_298','H_corrected_298_kJ_mol')]
        ok = orig['InChI']==r['inchi'] and orig['Method']==r['method'] and orig['Reference']==r['source_reference_codes']
        for a,b in pairs:
            av,bv = number(orig[a]),number(r[b])
            ok &= (math.isnan(av) and math.isnan(bv)) or av==bv
        checks.append(ok)
        if not ok: raise AssertionError('Compendium row no longer matches original: '+r['record_id'])
        i = r['inchi'];T=number(r['T_reported_K']);Hv=number(r['H_reported_kJ_mol'])
        reason=[]
        if i not in pressure_ids: reason.append('outside_pressure_join')
        if i in pressure_ids and i not in good: reason.append(graph_reason[i])
        if not math.isfinite(Hv) or Hv<=0: reason.append('nonpositive_or_missing_enthalpy')
        if not math.isfinite(T) or not 250<=T<=500: reason.append('temperature_outside_domain_or_missing')
        if r['method']!='C': reason.append('not_exact_calorimetry_C')
        if r['notes']: reason.append('source_note_requires_review')
        if not codes(r['source_reference_codes']): reason.append('unresolved_reference_code')
        eligible=not reason
        if eligible:
            status='quarantine_compendium_provenance'
            reason=['measurement_temperature_state_correction_and_independence_unverified']
        else: status='excluded_from_primary_scope'
        lo,hi=envelopes.get(i,(math.nan,math.nan))
        decisions.append(dict(record_id=r['record_id'],origin='compendium',molecule_id=uid('mol_',i),
            inchi=i,name=r['name'],H_kJ_mol=Hv,T_K=T,H_J_mol=Hv*1000,
            method=r['method'],source_doi='',reference_codes_json=js(codes(r['source_reference_codes'])),
            source_locator=f"RDR file 250199, CSV line {r['csv_line_1based']}",
            reported_deviation=r['deviation_reported'],uncertainty_kind='unspecified_compendium_deviation',
            uncertainty_confidence_percent='',uncertainty_coverage_factor='',
            experimental_temperature_range=r['reported_experimental_T_range'],
            temperature_status=r['measurement_vs_reference_T_status'],
            thermodynamic_state='not_resolved_from_compendium_row',
            raw_row_verified=ok,archive_XML_verified=False,full_primary_methods_verified=False,
            calorimetry_candidate=eligible,has_pressure_join=i in pressure_ids,
            inside_pressure_temperature_envelope=lo<=T<=hi,
            decision=status,decision_reasons=';'.join(reason),
            independent_of_pressure_verified=False,training_allowed=False,
            corrected_298_field_excluded=True,duplicate_family='',linked_record_ids_json='[]'))

    joinedN = N[N.inchi.isin(pressure_ids)].copy()
    for r in joinedN.to_dict('records'):
        i=r['inchi'];T=number(r['T_K']);Hv=number(r['H_kJ_mol']);pv=json.loads(r['original_property_value_metadata_json'])
        sm=source_meta[r['series_id']]['metadata']
        prop=next(x for x in sm.get('Property',[]) if x['nPropNumber']==int(r['property_number']))
        u=pv.get('CombinedUncertainty',{})
        if isinstance(u,list):u=u[0] if u else {}
        ud=prop.get('CombinedUncertainty',{})
        if isinstance(ud,list):ud=ud[0] if ud else {}
        reason=[]
        if i not in good:reason.append(graph_reason[i])
        if not r['stable_liquid_gas']:reason.append('not_liquid_gas_transition')
        if not r['calorimetry_label']:reason.append('not_calorimetry_method_metadata')
        if not 250<=T<=500 or not math.isfinite(Hv) or Hv<=0:reason.append('invalid_or_out_of_domain_value')
        eligible=not reason
        if eligible:
            status='quarantine_archive_calorimetry'
            reason=['full_methods_state_corrections_and_independence_unverified']
        else:status='excluded_from_primary_scope'
        if r['source_doi']=='10.1016/j.jct.2019.02.001' and r['name']=='decane':
            status='quarantine_same_source_conflict';reason.append('two_values_same_T_source_sample_require_table_lineage_review')
        if r['source_doi']=='10.1021/je025634v':
            reason.append('abstract_reports_cross_method_refinement')
        if r['source_doi']=='10.1016/j.jct.2015.07.028':
            reason.append('abstract_discusses_gas_phase_association')
        lo,hi=envelopes[i]
        decisions.append(dict(record_id=r['record_id'],origin='thermoml',molecule_id=uid('mol_',i),
            inchi=i,name=r['name'],H_kJ_mol=Hv,T_K=T,H_J_mol=Hv*1000,
            method=r['method'],source_doi=r['source_doi'],reference_codes_json='[]',
            source_locator=f"{r['archive_member']}; data {r['data_number']}; property {r['property_number']}; row {r['numvalues_index_1based']}",
            reported_deviation=u.get('nCombExpandUncertValue',''),uncertainty_kind='combined_expanded' if u else 'not_reported',
            uncertainty_confidence_percent=ud.get('nCombUncertLevOfConfid',''),
            uncertainty_coverage_factor=ud.get('nCombUncertCoverageFactor',''),
            experimental_temperature_range='',temperature_status='reported_T_from_numeric_variable_or_constraint',
            thermodynamic_state='liquid_gas_metadata_standard_vs_saturation_requires_primary_methods',
            raw_row_verified=r['record_id'] in xml_verified,archive_XML_verified=r['record_id'] in xml_verified,
            full_primary_methods_verified=False,calorimetry_candidate=eligible,has_pressure_join=True,
            inside_pressure_temperature_envelope=lo<=T<=hi,
            decision=status,decision_reasons=';'.join(reason),independent_of_pressure_verified=False,
            training_allowed=False,corrected_298_field_excluded=True,duplicate_family='',linked_record_ids_json='[]'))
    D=pd.DataFrame(decisions)
    return D,dict(compendium_original_rows_checked=len(checks),compendium_original_mismatches=sum(not x for x in checks))

def link_copies(D):
    # Source mappings corroborated in the prior audit. Similar author codes alone
    # are deliberately insufficient for asserting a duplicate.
    confirmed={'2009ZAI/PAU':'10.1021/je900093h','2003ZAI/VER':'10.1021/je025634v','2013STE/FUL':'10.1016/j.jct.2013.01.009'}
    links=[]
    for idx,r in D[(D.origin=='compendium') & D.calorimetry_candidate].iterrows():
        ds={confirmed[c] for c in json.loads(r.reference_codes_json) if c in confirmed}
        matches=D[(D.origin=='thermoml')&D.calorimetry_candidate&(D.inchi==r.inchi)&D.source_doi.isin(ds)]
        for j,s in matches.iterrows():
            kind='possible_same_measurement_different_temperature'
            if abs(r.H_kJ_mol-s.H_kJ_mol)<=1e-8 and abs(r.T_K-s.T_K)<=0.51:
                kind='same_source_value_with_rounded_temperature'
            family=uid('lineage_',r.inchi+'|'+s.source_doi)
            links.append(dict(compendium_record_id=r.record_id,thermoml_record_id=s.record_id,
                molecule_id=r.molecule_id,source_doi=s.source_doi,lineage_id=family,
                relation=kind,compendium_T_K=r.T_K,thermoml_T_K=s.T_K,
                compendium_H_kJ_mol=r.H_kJ_mol,thermoml_H_kJ_mol=s.H_kJ_mol,
                numeric_values_merged=False,reason='preserve source-specific T and uncertainty; do not count twice'))
            for a,b in [(idx,s.record_id),(j,r.record_id)]:
                vals=set(json.loads(D.at[a,'linked_record_ids_json']));vals.add(b)
                D.at[a,'linked_record_ids_json']=js(sorted(vals));D.at[a,'duplicate_family']=family
    return links

def split_groups(P,D,M,mols,citations,config):
    ids=sorted(M[M.structure_eligible].inchi)
    uf=UnionFind(ids);edges=[]
    def add(a,b,kind,key,similarity=''):
        if a==b:return
        uf.union(a,b);edges.append(dict(molecule_a=uid('mol_',a),molecule_b=uid('mol_',b),kind=kind,key=key,similarity=similarity))
    def groups(rows,kind):
        for key,vals in sorted(rows.items()):
            vs=sorted(set(vals))
            for v in vs[1:]:add(vs[0],v,kind,key)
    groups({k:list(g.inchi) for k,g in M[M.structure_eligible].groupby('connectivity_key')},'same_connectivity')
    gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=False)
    fps=[gen.GetFingerprint(mols[i]) for i in ids]
    for a,i in enumerate(ids):
        sims=DataStructs.BulkTanimotoSimilarity(fps[a],fps[:a])
        for b,v in enumerate(sims):
            if v>=config['tanimoto_threshold']-1e-12:
                add(i,ids[b],'morgan_similarity_ge_threshold','ECFP4_2048_no_chirality',v)
    ps=P[P.inchi.isin(ids)]
    groups({k:list(g.inchi) for k,g in ps.groupby('source_doi')},'same_pressure_DOI')
    candidate=D[D.calorimetry_candidate & D.inchi.isin(ids)]
    refs=collections.defaultdict(set)
    for r in candidate.to_dict('records'):
        for c in json.loads(r['reference_codes_json']):refs[c].add(r['inchi'])
        if r['source_doi']:refs['doi:'+r['source_doi']].add(r['inchi'])
    groups(refs,'shared_enthalpy_reference')
    # Conservative source embargo: ambiguous year/author suggestions unite ALL
    # candidate DOIs for grouping only. They never validate a label or its source.
    aliases=collections.defaultdict(set)
    for d,c in citations.items():
        t=c.get('TRCRefID',{})
        key=f"{t.get('yrYrPub','')}{t.get('sAuthor1','').upper()}/{t.get('sAuthor2','').upper()}"
        aliases[key].add(d)
    doi_mol=collections.defaultdict(set)
    for r in ps.to_dict('records'):doi_mol[r['source_doi']].add(r['inchi'])
    for r in candidate.to_dict('records'):
        if r['source_doi']:doi_mol[r['source_doi']].add(r['inchi'])
    alias_rows=[]
    for code,vs in sorted(refs.items()):
        if code.startswith('doi:'):
            ds=[code[4:]]
        else:
            ds=sorted(aliases.get(code,set()))
        connected=set(vs)
        for d in ds:connected.update(doi_mol[d])
        groups({code:connected},'possible_enthalpy_pressure_source_alias')
        if ds:alias_rows.append(dict(reference_code=code,candidate_dois_json=js(ds),status='conservative_grouping_only_not_source_certification'))
    components=collections.defaultdict(list)
    for i in ids:components[uf.find(i)].append(i)
    cids={i:uid('grp_','\n'.join(sorted(vs))) for vs in components.values() for i in vs}
    # A single deterministic 70/15/15 allocation; NO seed search and NO outcomes.
    ordered=sorted(components.values(),key=lambda vs:(-len(vs),uid('',str(config['seed'])+'|'+'\n'.join(sorted(vs)))))
    ratios=config['split_fractions'];tie_order=config['split_tie_order'];counts={s:0 for s in tie_order};total=len(ids)
    assignments={}
    for vs in ordered:
        # Minimize sum of squared fraction errors. Stable tie order is explicit.
        choice=min(tie_order,key=lambda s:sum(((counts[t]+(len(vs) if t==s else 0))/total-ratios[t])**2 for t in tie_order))
        for i in vs:assignments[i]=choice
        counts[choice]+=len(vs)
    S=M[M.structure_eligible].copy()
    S['component_id']=S.inchi.map(cids);S['split']=S.inchi.map(assignments)
    return S,edges,alias_rows

def pressure_tables(P,S):
    ps=P[P.inchi.isin(set(S.inchi))].copy()
    ps['molecule_id']=ps.inchi.map(dict(zip(S.inchi,S.molecule_id)))
    ps['component_id']=ps.inchi.map(dict(zip(S.inchi,S.component_id)))
    ps['split']=ps.inchi.map(dict(zip(S.inchi,S.split)))
    ps['T_K']=ps.T_K.astype(float);ps['p_Pa']=ps.p_Pa.astype(float)
    # Identical source/molecule/T/p copies do not get extra statistical weight.
    ps['duplicate_group']=ps.apply(lambda r:uid('pdup_',js([r.source_doi,r.inchi,float(r.T_K),float(r.p_Pa)])),axis=1)
    ps=ps.sort_values('record_id',kind='stable')
    ps['duplicate_representative_id']=ps.groupby('duplicate_group').record_id.transform('first')
    ps['is_duplicate_copy']=ps.record_id!=ps.duplicate_representative_id
    ps['log10_p_over_1Pa']=np.log10(ps.p_Pa)
    ps['ln_p_over_1Pa']=np.log(ps.p_Pa)
    ps['temperature_level_id']=''
    series=[]
    for sid,g in ps.groupby('series_id',sort=True):
        ls=levels(g.T_K)
        for n,ts in enumerate(ls):
            ps.loc[g.index[g.T_K.isin(ts)],'temperature_level_id']=sid+f'#T{n:04d}'
        med=g.groupby('T_K').log10_p_over_1Pa.median().sort_index()
        series.append(dict(series_id=sid,molecule_id=g.molecule_id.iloc[0],inchi=g.inchi.iloc[0],source_doi=g.source_doi.iloc[0],
                           **coverage(g.T_K),monotonicity_flag=bool((med.diff().dropna() < -1e-8).any()),
                           monotonicity_used_to_select_series=False))
    series=pd.DataFrame(series)
    selected=series.sort_values(['episode_eligible','T_span_K','temperature_levels','series_id'],ascending=[False,False,False,True]).drop_duplicates('inchi')
    selected_ids=set(selected[selected.episode_eligible].series_id)
    ps['base_role']=np.where(ps.split=='train','train_pressure','withheld_other')
    ps.loc[ps.is_duplicate_copy,'base_role']='duplicate_copy_never_used'
    episodes=[];sens=[];episode_records=[]
    # All pressure ceilings share molecular assignments. Rebuild temperature
    # episodes within the SAME source series; no series cherry-picking at a cap.
    for cap in [20000,10000,5000]:
        for sid in sorted(selected_ids):
            g=ps[(ps.series_id==sid)&(~ps.is_duplicate_copy)&(ps.p_Pa<=cap)]
            if not len(g):continue
            cov=coverage(g.T_K)
            if not cov['episode_eligible']:continue
            ls=levels(g.T_K);med=[statistics.median(ts) for ts in ls]
            lo,hi=med[0],med[-1];span=hi-lo
            warm=[j for j,t in enumerate(med) if t>=lo+.7*span-1e-9]
            cold=[j for j,t in enumerate(med) if t<=lo+.3*span+1e-9]
            ai=[warm[0],warm[(len(warm)-1)//2],warm[-1]]
            anchors=[]
            for j in ai:
                candidates=g[g.T_K.isin(ls[j])].copy()
                candidates['distance_to_level_median']=abs(candidates.T_K-med[j])
                anchors.append(candidates.sort_values(['distance_to_level_median','record_id']).record_id.iloc[0])
            cold_t={t for j in cold for t in ls[j]}
            targets=sorted(g[g.T_K.isin(cold_t)].record_id)
            e=dict(episode_id=uid('ep_',sid+'|'+str(cap)),molecule_id=g.molecule_id.iloc[0],
                component_id=g.component_id.iloc[0],split=g.split.iloc[0],source_doi=g.source_doi.iloc[0],
                series_id=sid,pressure_ceiling_Pa=cap,**cov,
                anchor_record_ids_json=js(anchors),cold_target_record_ids_json=js(targets),
                anchor_count=3,cold_record_count=len(targets),cold_temperature_level_count=len(cold))
            episodes.append(e)
            level_map={t:j for j,ts in enumerate(ls) for t in ts}
            for role,record_ids in [('anchor',anchors),('cold_target',targets)]:
                for rid in record_ids:
                    row=g[g.record_id==rid].iloc[0]
                    j=level_map[row.T_K]
                    episode_records.append(dict(episode_id=e['episode_id'],pressure_ceiling_Pa=cap,
                        molecule_id=e['molecule_id'],component_id=e['component_id'],split=e['split'],
                        record_id=rid,episode_role=role,
                        episode_temperature_level_id=e['episode_id']+f'#T{j:04d}',
                        temperature_level_representative_K=med[j]))
            if cap==20000 and g.split.iloc[0]!='train':
                ps.loc[ps.record_id.isin(anchors),'base_role']='adaptation_anchor'
                ps.loc[ps.record_id.isin(targets),'base_role']='cold_target'
        cap_e=[e for e in episodes if e['pressure_ceiling_Pa']==cap]
        sens.append(dict(pressure_ceiling_Pa=cap,episode_counts=dict(collections.Counter(e['split'] for e in cap_e)),
                         source_series_selection='same_preselected_series_as_20kPa',split_assignments='unchanged'))
    keep=['record_id','molecule_id','inchi','name','component_id','split','series_id','source_doi','T_K','p_Pa',
          'log10_p_over_1Pa','ln_p_over_1Pa','temperature_level_id','base_role','duplicate_group',
          'duplicate_representative_id','is_duplicate_copy','method','property_phase',
          'state_origin','original_property_value_metadata_json','state_metadata_json']
    return ps[keep].sort_values('record_id'),pd.DataFrame(episodes),series,sens,pd.DataFrame(episode_records)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=pathlib.Path,default=ROOT/'frozen')
    a=parser.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'config.json').read_text())
    # These fields document this release's protocol. A changed protocol requires
    # an explicit new implementation/version, not an unnoticed configuration edit.
    fixed={'temperature_domain_K':[250,500],'pressure_domain_Pa':[1,20000],
           'pressure_sensitivity_caps_Pa':[20000,10000,5000],
           'temperature_level_tolerance_K':0.1,'minimum_episode_temperature_span_K':30,
           'minimum_episode_temperature_levels':6,'warm_fraction_of_temperature_span':0.3,
           'cold_fraction_of_temperature_span':0.3,'minimum_cold_temperature_levels':2,
           'adaptation_anchors_per_episode':3,
           'fingerprint':{'family':'Morgan','radius':2,'bits':2048,'include_chirality':False}}
    for key,value in fixed.items():
        if config[key]!=value:raise SystemExit('New protocol implementation required for '+key)
    if rdBase.rdkitVersion!=config['rdkit_version']:raise SystemExit('RDKit version mismatch; do not silently change the grouping.')
    expected=json.loads((ROOT/'input_hashes.json').read_text())
    for name,sha in expected.items():
        if digest(ROOT/'inputs'/name)!=sha:raise SystemExit('Input checksum mismatch: '+name)
    P=read('pressure_records.csv');P=P[P.primary_candidate].copy();P['T_K']=P.T_K.astype(float)
    H=read('enthalpy_records.csv');N=read('thermoml_enthalpy_records.csv')
    citations=json.loads((ROOT/'inputs/citations.json').read_text())
    meta={x['series_id']:x for x in (json.loads(l) for l in open(ROOT/'inputs/thermoml_provenance.jsonl'))}
    M,mols=molecular_review(P)
    D,raw_checks=review_labels(H,N,P,M,meta)
    copies=link_copies(D)
    S,edges,aliases=split_groups(P,D,M,mols,citations,config)
    ps,E,series,sens,Q=pressure_tables(P,S)
    smap=dict(zip(S.molecule_id,S.split));cmap=dict(zip(S.molecule_id,S.component_id))
    D['split']=D.molecule_id.map(smap).fillna('outside_frozen_scope')
    D['component_id']=D.molecule_id.map(cmap).fillna('')
    S['has_calorimetry_candidate']=S.molecule_id.isin(D[D.calorimetry_candidate].molecule_id)
    S['has_cold_episode']=S.molecule_id.isin(E[E.pressure_ceiling_Pa==20000].molecule_id)
    S['pressure_rows_deduplicated']=S.molecule_id.map(ps[~ps.is_duplicate_copy].groupby('molecule_id').size())
    S['enthalpy_certified_count']=0
    save(out/'molecular_review.csv',M)
    save(out/'split_assignments.csv',S.sort_values('molecule_id'))
    save(out/'enthalpy_decisions.csv',D.sort_values('record_id'))
    save(out/'enthalpy_candidates.csv',D[D.calorimetry_candidate].sort_values('record_id'))
    save(out/'enthalpy_primary_labels.csv',D[D.training_allowed].sort_values('record_id'))
    save(out/'enthalpy_lineage_links.csv',copies)
    save(out/'pressure_observations.csv',ps)
    save(out/'source_series_review.csv',series.sort_values('series_id'))
    save(out/'episodes.csv',E.sort_values(['pressure_ceiling_Pa','episode_id']))
    save(out/'episode_records.csv',Q.sort_values(['episode_id','episode_role','record_id']))
    save(out/'group_edges.csv',edges)
    save(out/'source_aliases_for_grouping.csv',aliases)
    dump(out/'pressure_ceiling_sensitivity.json',sens)
    # Explicit input exports prevent a future model script from accidentally
    # fitting on a withheld target, an alternate series or a duplicate copy.
    save(out/'train_pressure.csv',ps[ps.base_role=='train_pressure'])
    for split in ['validation','test']:
        save(out/f'{split}_anchors.csv',ps[(ps.split==split)&(ps.base_role=='adaptation_anchor')])
        save(out/f'{split}_cold_targets.csv',ps[(ps.split==split)&(ps.base_role=='cold_target')])
    refs=collections.defaultdict(list)
    for r in D[(D.origin=='compendium')&D.calorimetry_candidate].to_dict('records'):
        for c in json.loads(r['reference_codes_json']):refs[c].append(r)
    for r in D[(D.origin=='thermoml')&D.calorimetry_candidate].to_dict('records'):
        refs['doi:'+r['source_doi']].append(r)
    queue=[]
    for c,rs in refs.items():
        queue.append(dict(reference_code=c,records=len(rs),molecules=len({r['molecule_id'] for r in rs}),
            train_molecules=len({r['molecule_id'] for r in rs if r['split']=='train'}),
            record_ids_json=js(sorted(r['record_id'] for r in rs)),
            review_status='required_before_promotion',
            required_evidence='primary table and methods; measurement vs reference T; phase and state; uncertainty convention; pressure-independent lineage and corrections'))
    save(out/'source_review_queue.csv',pd.DataFrame(queue).sort_values(['train_molecules','molecules','reference_code'],ascending=[False,False,True]))
    summary={
      'version':config['version'],'date':config['freeze_date'],'scientific_readiness':'HOLD_ENTHALPY_PROVENANCE',
      'software':dict(python=sys.version.split()[0],pandas=pd.__version__,numpy=np.__version__,rdkit=rdBase.rdkitVersion),
      'raw_compendium_checks':raw_checks,'input_hashes_verified':len(expected),
      'pressure_candidate_molecules':len(M),'structure_eligible_molecules':len(S),
      'structure_exclusion_reasons':dict(collections.Counter(x for x in M.exclusion_reasons for x in x.split(';') if x)),
      'pressure_rows_before_dedup':len(ps),'pressure_rows_after_dedup':int((~ps.is_duplicate_copy).sum()),
      'duplicate_pressure_copies_removed_from_use':int(ps.is_duplicate_copy.sum()),
      'compendium_C_candidates_in_frozen_scope':int(((D.origin=='compendium')&D.calorimetry_candidate).sum()),
      'compendium_C_candidate_molecules_in_frozen_scope':int(D[(D.origin=='compendium')&D.calorimetry_candidate].molecule_id.nunique()),
      'thermoml_calorimetry_candidates_in_frozen_scope':int(((D.origin=='thermoml')&D.calorimetry_candidate).sum()),
      'certified_independent_enthalpy_labels':int(D.training_allowed.sum()),
      'certified_independent_enthalpy_molecules':int(D[D.training_allowed].molecule_id.nunique()),
      'required_independent_enthalpy_molecules_before_main_training':config['minimum_independent_enthalpy_molecules'],
      'required_independent_training_enthalpy_molecules':config['minimum_independent_training_enthalpy_molecules'],
      'certified_independent_training_enthalpy_molecules':int(D[D.training_allowed & (D.split=='train')].molecule_id.nunique()),
      'known_cross_dataset_lineage_links':len(copies),'source_review_groups':len(queue),
      'atomic_components':int(S.component_id.nunique()),
      'largest_component_molecules':int(S.groupby('component_id').size().max()),
      'candidate_enthalpy_decisions':D[D.calorimetry_candidate].decision.value_counts().to_dict(),
      'split_counts':[],
      'split_selection_used_model_scores':False,'CC_diagnostic_used_for_exclusion':False,
      'full_primary_methods_obtained':False,
      'test_design':'retrospective pre-model holdout; no models trained',
      'primary_metric':config['evaluation']['primary_metric'],
    }
    base=E[E.pressure_ceiling_Pa==20000]
    for split in ['train','validation','test']:
        ss=S[S.split==split];pp=ps[ps.split==split];ee=base[base.split==split]
        summary['split_counts'].append(dict(split=split,molecules=len(ss),components=int(ss.component_id.nunique()),
            pressure_rows_deduplicated=int((~pp.is_duplicate_copy).sum()),cold_episodes=len(ee),
            exposed_pressure_training_rows=int((pp.base_role=='train_pressure').sum()),
            adaptation_anchor_rows=int((pp.base_role=='adaptation_anchor').sum()),
            cold_target_rows=int((pp.base_role=='cold_target').sum()),
            calorimetry_candidate_molecules=int(ss.has_calorimetry_candidate.sum())))
    dump(out/'summary.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
