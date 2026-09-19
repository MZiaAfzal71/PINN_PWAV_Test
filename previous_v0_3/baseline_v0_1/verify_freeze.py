#!/usr/bin/env python3
"""Independent integrity, identity, leakage and evaluation-access checks.

Exit 0 means the curation freeze is internally consistent. It does NOT authorize
enthalpy model training: check_readiness.py is a separate scientific gate.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog('rdApp.*')
ROOT=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--frozen',type=Path,default=ROOT/'frozen')
    ap.add_argument('--out',type=Path,default=ROOT/'evidence/integrity_verification.json')
    a=ap.parse_args();f=a.frozen
    config=json.loads((ROOT/'config.json').read_text())
    def read(name):return pd.read_csv(f/(name+'.csv'),keep_default_na=False,float_precision='round_trip',low_memory=False)
    checks=[]
    def check(condition,message):
        if not bool(condition):raise AssertionError(message)
        checks.append(message)
    check(rdBase.rdkitVersion==config['rdkit_version'],'Pinned RDKit version')
    for name,expected in json.loads((ROOT/'input_hashes.json').read_text()).items():
        check(sha(ROOT/'inputs'/name)==expected,'Input SHA256: '+name)
    P=read('pressure_observations');S=read('split_assignments');D=read('enthalpy_decisions');E=read('episodes')
    H=read('enthalpy_candidates');L=read('enthalpy_primary_labels');G=read('group_edges');Q=read('episode_records')
    SM=S.set_index('molecule_id');PM=P.set_index('record_id')
    check(S.inchi.is_unique and S.molecule_id.is_unique,'One assignment per full InChI and molecule ID')
    check(P.record_id.is_unique and D.record_id.is_unique,'Unique observation record IDs')
    check(set(S.split)=={'train','validation','test'},'All three splits present')
    check(S.groupby('component_id').split.nunique().max()==1,'Atomic components never cross splits')
    check(S.groupby('connectivity_key').split.nunique().max()==1,'Shared connectivity never crosses splits')
    check(P.groupby('molecule_id').split.nunique().max()==1,'Molecule pressure records never cross splits')
    check(P.groupby('source_doi').split.nunique().max()==1,'All included pressure DOI groups never cross splits')
    check(all(P.split==P.molecule_id.map(SM.split)),'Pressure assignments match molecular assignments')
    check(all(P.component_id==P.molecule_id.map(SM.component_id)),'Pressure components match molecular assignments')
    check(all(G.molecule_a.map(SM.split)==G.molecule_b.map(SM.split)),'Every stored source/structure edge remains inside one split')
    refs={}
    for row in H.to_dict('records'):
        keys=json.loads(row['reference_codes_json'])
        if row['source_doi']:keys.append('doi:'+row['source_doi'])
        for key in keys:refs.setdefault(key,set()).add(row['split'])
    check(all(len(x)==1 for x in refs.values()),'Candidate enthalpy references never cross splits')
    doi_split={d:set(g.split) for d,g in P.groupby('source_doi')}
    for r in H.to_dict('records'):
        if r['source_doi']:doi_split.setdefault(r['source_doi'],set()).add(r['split'])
    check(all(len(v)==1 for v in doi_split.values()),'Known common pressure/enthalpy DOI sources never cross splits')
    for r in read('source_aliases_for_grouping').to_dict('records'):
        splits=set(refs.get(r['reference_code'],set()))
        for doi in json.loads(r['candidate_dois_json']):splits.update(doi_split.get(doi,set()))
        check(len(splits)<=1,'Conservative source embargo: '+r['reference_code'])
    gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=False)
    fps={r.molecule_id:gen.GetFingerprint(Chem.MolFromInchi(r.inchi)) for r in S.itertuples()}
    maxima={};nearest={}
    for left,right in [('train','validation'),('train','test'),('validation','test')]:
        lhs=list(S[S.split==left].molecule_id);rhs=list(S[S.split==right].molecule_id)
        best=(-1,None,None)
        for i in lhs:
            values=DataStructs.BulkTanimotoSimilarity(fps[i],[fps[j] for j in rhs])
            k=int(np.argmax(values))
            if values[k]>best[0]:best=(values[k],i,rhs[k])
        key=left+'__'+right;maxima[key]=best[0];nearest[key]=best[1:]
        check(best[0]<config['tanimoto_threshold']-1e-12,'Cross-split fingerprint similarity below 0.7: '+key)
    check(P.T_K.between(250,500).all() and P.p_Pa.between(1,20000).all(),'Pressure numerical domain')
    check(np.isfinite(P[['T_K','p_Pa','log10_p_over_1Pa','ln_p_over_1Pa']].to_numpy()).all(),'Finite pressure inputs and targets')
    check(np.allclose(P.log10_p_over_1Pa,np.log10(P.p_Pa),rtol=1e-10,atol=1e-10),'Dimensionless log10 pressure target')
    check(np.allclose(P.ln_p_over_1Pa,np.log(P.p_Pa),rtol=1e-10,atol=1e-10),'Natural-log pressure for CC derivative')
    kept=P[~P.is_duplicate_copy]
    check(not kept.duplicated(['source_doi','inchi','T_K','p_Pa']).any(),'One copy of each exact source/identity/T/p tuple')
    check(all(P[P.is_duplicate_copy].base_role=='duplicate_copy_never_used'),'Duplicate copies excluded from every model input')
    for r in P[P.is_duplicate_copy].itertuples():
        s=PM.loc[r.duplicate_representative_id]
        if not (r.source_doi==s.source_doi and r.inchi==s.inchi and r.T_K==s.T_K and r.p_Pa==s.p_Pa):
            raise AssertionError('Invalid duplicate link '+r.record_id)
    checks.append('Every removed duplicate matches its retained representative')
    train=read('train_pressure')
    check(set(train.record_id)==set(kept[kept.split=='train'].record_id),'Training pressure export contains exactly retained train rows')
    used=set(train.record_id)
    for split in ['validation','test']:
        for kind,role in [('anchors','adaptation_anchor'),('cold_targets','cold_target')]:
            x=read(split+'_'+kind)
            expect=P[(P.split==split)&(P.base_role==role)]
            check(set(x.record_id)==set(expect.record_id),'Role export exact: '+split+'_'+kind)
            check(not used.intersection(x.record_id),'Disjoint exposed exports: '+split+'_'+kind)
            used.update(x.record_id)
    check(not P[(P.split!='train')].record_id.isin(train.record_id).any(),'No held-out pressure record enters global training')
    check(E.episode_id.is_unique,'Unique episode IDs')
    check(not E.duplicated(['molecule_id','pressure_ceiling_Pa']).any(),'At most one source episode per molecule and pressure cap')
    check(E.groupby('molecule_id').series_id.nunique().max()==1,'Sensitivity caps retain the same source series')
    check(not Q.duplicated(['episode_id','record_id']).any(),'One role per observation within an episode')
    counts={}
    for r in E.to_dict('records'):
        anchors=json.loads(r['anchor_record_ids_json']);targets=json.loads(r['cold_target_record_ids_json'])
        aa=PM.loc[anchors];tt=PM.loc[targets]
        mapping=Q[Q.episode_id==r['episode_id']]
        ma=mapping[mapping.episode_role=='anchor'];mt=mapping[mapping.episode_role=='cold_target']
        if not(set(ma.record_id)==set(anchors) and set(mt.record_id)==set(targets) and
               ma.episode_temperature_level_id.nunique()==3 and
               mt.episode_temperature_level_id.nunique()==r['cold_temperature_level_count'] and
               not set(ma.episode_temperature_level_id)&set(mt.episode_temperature_level_id)):
            raise AssertionError('Episode-specific temperature levels '+r['episode_id'])
        if not(len(anchors)==3 and len(set(anchors))==3 and targets and not(set(anchors)&set(targets))):
            raise AssertionError('Anchor/target record isolation '+r['episode_id'])
        both=pd.concat([aa,tt]);span=r['T_max_K']-r['T_min_K']
        if not (set(both.molecule_id)=={r['molecule_id']} and set(both.series_id)=={r['series_id']} and
                set(both.split)=={r['split']} and (both.p_Pa<=r['pressure_ceiling_Pa']).all() and
                not both.is_duplicate_copy.any() and span>=30-1e-8 and
                aa.T_K.min()>tt.T_K.max() and aa.temperature_level_id.nunique()==3 and
                not set(aa.temperature_level_id)&set(tt.temperature_level_id)):
            raise AssertionError('Temperature/source/duplicate embargo '+r['episode_id'])
        # Level representatives may differ by <=0.05 K from a recorded endpoint.
        if not ((aa.T_K>=r['T_min_K']+.7*span-.1-1e-8).all() and
                (tt.T_K<=r['T_min_K']+.3*span+.1+1e-8).all()):
            raise AssertionError('Warm/cold bounds '+r['episode_id'])
        if r['pressure_ceiling_Pa']==20000 and r['split']!='train':
            if not ((aa.base_role=='adaptation_anchor').all() and (tt.base_role=='cold_target').all()):
                raise AssertionError('Evaluation export episode roles '+r['episode_id'])
        key=str(r['pressure_ceiling_Pa'])+'_'+r['split'];counts[key]=counts.get(key,0)+1
    checks.append('Every episode: three warm levels, colder targets, one molecule/source/split, cap compliance, no duplicates or shared levels')
    checks.append('Explicit episode record maps preserve each cap-specific temperature level and role')
    check(np.allclose(H.H_J_mol,H.H_kJ_mol*1000,rtol=1e-12),'Enthalpy kJ/mol to J/mol conversion')
    check(H.H_kJ_mol.gt(0).all() and H.T_K.between(250,500).all(),'Positive finite in-domain enthalpy candidates')
    check((H[H.origin=='compendium'].method=='C').all(),'Only exact C compendium methods enter candidate pool')
    check(H.raw_row_verified.all(),'Candidate transcription checks passed')
    check(H[H.origin=='thermoml'].archive_XML_verified.all(),'Archive enthalpy candidates checked against XML')
    check(not D.training_allowed.any() and len(L)==0,'No uncertified enthalpy exposed as training labels')
    check(not D.independent_of_pressure_verified.any(),'No unverified pressure independence claim')
    check(D.corrected_298_field_excluded.all(),'Derived Hvap_298 field never used as independent label')
    xml=json.loads((ROOT/'inputs/archive_xml_verification.json').read_text())
    check(xml['mismatch_count']==0 and xml['missing_count']==0,'Complete original-XML transcription checks')
    check(set(P.record_id).issubset(set(xml['verified_record_ids'])),'Every frozen pressure record covered by XML verification')
    # This is a validation of archived data, not an experimentally blinded trial.
    report=dict(technical_status='PASS',scientific_status='HOLD_ENTHALPY_PROVENANCE',
        checks_passed=len(checks),checks=checks,max_cross_split_tanimoto=maxima,
        nearest_cross_split_pairs=nearest,episode_counts=counts,
        archive_xml_rows_checked=xml['rows_passed'],
        certified_independent_enthalpy_labels=len(L),
        known_source_and_identity_leakage_detected=False,
        unknown_source_lineage_fully_resolved=False,
        pressure_only_split_usable=True,enthalpy_comparative_training_authorized=False)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['checks','nearest_cross_split_pairs']},indent=2))

if __name__=='__main__':main()
