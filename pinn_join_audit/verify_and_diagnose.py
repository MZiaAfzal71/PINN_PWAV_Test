#!/usr/bin/env python3
"""Independent XML spot checks and descriptive diagnostics; no model training.

Dependencies: numpy. Diagnostics never remove observations or certify independence.
"""
import argparse, csv, json, math, pathlib, statistics, tarfile, xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np

def read(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def save(p, rows):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['status']);w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=pathlib.Path,required=True);ap.add_argument('--results',type=pathlib.Path,required=True);a=ap.parse_args();out=a.results
    P=read(out/'pressure_records.csv');H=read(out/'enthalpy_records.csv');N=read(out/'thermoml_enthalpy_records.csv');B=read(out/'boiling_records_supplement.csv');M=read(out/'molecule_audit.csv')
    chosen={'10.1021/je025634v','10.1016/j.jct.2013.01.009','10.1021/je900093h','10.1007/s10765-006-0018-5','10.1016/j.fluid.2004.11.010'}
    rows={r['record_id']:r for r in P+H+N+B if r.get('source_doi') in chosen};checked=[];errors=[];seen=set();names={'Vapor or sublimation pressure, kPa','Molar enthalpy of vaporization or sublimation, kJ/mol','Boiling temperature at pressure P, K'}
    with tarfile.open(a.archive,'r|gz') as tar:
        for m in tar:
            if not m.isfile() or not m.name.endswith('.xml') or m.name[:-4] not in chosen:continue
            root=ET.parse(tar.extractfile(m)).getroot()
            for e in root.iter():e.tag=e.tag.split('}')[-1]
            cmp={c.findtext('RegNum/nOrgNum'):c.findtext('sStandardInChI') for c in root.findall('Compound')}
            doi=root.findtext('Citation/sDOI')
            for b in root.findall('PureOrMixtureData'):
                if len(b.findall('Component'))!=1:continue
                inchi=cmp[b.findtext('Component/RegNum/nOrgNum')];dn=b.findtext('nPureOrMixtureDataNumber')
                props={p.findtext('nPropNumber'):p for p in b.findall('Property')}
                var={v.findtext('nVarNumber'):v for v in b.findall('Variable')}
                for ni,nv in enumerate(b.findall('NumValues'),1):
                    for pv in nv.findall('PropertyValue'):
                        pn=pv.findtext('nPropNumber');pr=props[pn];name=pr.findtext('.//ePropName')
                        if name not in names:continue
                        rid=f'{doi}#d{dn}#p{pn}#r{ni}';seen.add(rid);r=rows.get(rid)
                        if r is None:errors.append([rid,'XML record missing from CSV']);continue
                        val=float(pv.findtext('nPropValue'));key='ePressure' if name.startswith('Boiling') else 'eTemperature';states=[]
                        for vv in nv.findall('VariableValue'):
                            if var[vv.findtext('nVarNumber')].find('.//'+key) is not None:states.append(float(vv.findtext('nVarValue')))
                        for c in b.findall('Constraint'):
                            if c.find('.//'+key) is not None:states.append(float(c.findtext('nConstraintValue')))
                        checks=[inchi==r['inchi'],name==r['property_name'],math.isclose(val,float(r['original_property_value']),rel_tol=1e-12,abs_tol=1e-12),pr.findtext('PropPhaseID/ePropPhase')==r['property_phase']]
                        if len(states)==1:
                            checks.append(math.isclose(float(r['T_K']),val if name.startswith('Boiling') else states[0],rel_tol=1e-12))
                            if 'pressure' in name or name.startswith('Boiling'):checks.append(math.isclose(float(r['p_Pa']),(states[0] if name.startswith('Boiling') else val)*1000,rel_tol=1e-12))
                        if not all(checks):errors.append([rid,'identity/property/phase/value/state mismatch'])
                        checked.append(rid)
    errors.extend([[r,'CSV record missing from XML'] for r in rows.keys()-seen])
    result={'xml_studies':len({r.split('#')[0] for r in checked}),'xml_records_compared':len(checked),'mismatches':errors,'coverage':'vapor pressure, temperature as variable and constraint, boiling at specified pressure, liquid/crystal phases, calorimetric enthalpy; 5 selected studies'}
    (out/'xml_verification.json').write_text(json.dumps(result,indent=2))
    if errors:raise SystemExit('XML verification failed: '+str(errors[:3]))
    # Local log(p) versus 1/T slope, only within a single pressure series.
    groups=defaultdict(list)
    for p in P:
        if p['primary_candidate']=='True':groups[p['inchi'],p['series_id']].append(p)
    diags=[]
    for h in H:
        if h['C_candidate']!='True' or h['has_primary_pressure_match']!='True':continue
        T=float(h['T_reported_K']); options=[]
        for (i,sid),rs in groups.items():
            if i!=h['inchi']:continue
            byT=defaultdict(list)
            for p in rs:
                t=float(p['T_K'])
                if abs(t-T)<=20:byT[t].append(math.log(float(p['p_Pa'])))
            ts=sorted(byT)
            if len(ts)<6 or ts[-1]-ts[0]<10 or not ts[0]<=T<=ts[-1]:continue
            x=1/np.array(ts);y=np.array([np.mean(byT[t]) for t in ts]);X=np.column_stack([np.ones(len(x)),x-x.mean()]);coef=np.linalg.lstsq(X,y,rcond=None)[0]
            pred=X@coef;Hv=-8.314462618*coef[1]/1000;res=float(np.sqrt(np.mean((y-pred)**2))/math.log(10));observed=float(h['H_reported_kJ_mol'])
            item={'enthalpy_record_id':h['record_id'],'inchi':i,'name':h['name'],'source_reference_codes':h['source_reference_codes'],'pressure_series_id':sid,'pressure_source_doi':rs[0]['source_doi'],'pressure_method':rs[0]['method'],
                  'H_T_reported_K':T,'H_reported_kJ_mol':observed,'local_CC_H_kJ_mol':Hv,'difference_percent':100*(Hv-observed)/observed,'local_pressure_distinct_T':len(ts),'fit_T_min_K':ts[0],'fit_T_max_K':ts[-1],'fit_log10p_RMSE':res,
                  'interpretation':'descriptive_approximate_CC_diagnostic_not_independence_or_accuracy_validation'}
            options.append(item)
        # Select most local temperatures, then narrowest fit span, then stable series id.
        if options:diags.append(sorted(options,key=lambda z:(-z['local_pressure_distinct_T'],z['fit_T_max_K']-z['fit_T_min_K'],z['pressure_series_id']))[0])
    save(out/'local_clapeyron_diagnostics.csv',diags)
    absdiff=[abs(d['difference_percent']) for d in diags]
    summary={'comparisons':len(diags),'identifiers':len({d['inchi'] for d in diags}),'median_absolute_difference_percent':float(np.median(absdiff)) if absdiff else None,'p90_absolute_difference_percent':float(np.percentile(absdiff,90)) if absdiff else None,'not_an_independence_test':True,'no_observations_excluded_by_this_diagnostic':True}
    (out/'diagnostic_summary.json').write_text(json.dumps(summary,indent=2))
    # Predefined pressure-ceiling sensitivity; retain the other extraction screens.
    c_ids={h['inchi'] for h in H if h['C_candidate']=='True'}
    sensitivities=[]
    for cap in [5000,10000,20000]:
        ps=[p for p in P if p['primary_candidate']=='True' and float(p['p_Pa'])<=cap]; gg=defaultdict(set)
        for p in ps:gg[p['inchi']].add(float(p['T_K']))
        eligible=set()
        for i,ts in gg.items():
            clusters=[]
            for t in sorted(ts):
                if not clusters or t-clusters[-1][0]>0.1+1e-9:clusters.append([t])
                else:clusters[-1].append(t)
            ts=[statistics.median(g) for g in clusters]
            low,high=min(ts),max(ts);span=high-low
            if len(ts)>=6 and span>=30-1e-9 and sum(t>=low+.7*span-1e-9 for t in ts)>=3 and sum(t<=low+.3*span+1e-9 for t in ts)>=2:eligible.add(i)
        sensitivities.append({'p_ceiling_Pa':cap,'pressure_rows':len(ps),'identifiers':len(gg),'C_match_identifiers':len(set(gg)&c_ids),'three_anchor_identifiers':len(eligible),'three_anchor_C_identifiers':len(eligible&c_ids)})
    (out/'pressure_ceiling_sensitivity.json').write_text(json.dumps(sensitivities,indent=2))
    print(json.dumps({'xml_verification':result,'diagnostics':summary},indent=2))

if __name__=='__main__':main()
