#!/usr/bin/env python3
"""Reproduce the ThermoML/enthalpy feasibility audit. Python 3.10+, standard library only.

This exports CANDIDATES, not a scientifically validated training set. Read README.md.
No network access or archive extraction is used. XML and JSON are not double-counted.
"""
import argparse, ast, collections, csv, hashlib, json, math, pathlib, re, statistics, tarfile

P_NAME = 'Vapor or sublimation pressure, kPa'
H_NAME = 'Molar enthalpy of vaporization or sublimation, kJ/mol'
B_NAME = 'Boiling temperature at pressure P, K'
EXPECTED_SHA256 = '231161b5e443dc1ae0e5da8429d86a88474cb722016e5b790817bb31c58d7ec2'
EXPECTED_H_SHA256 = 'bf3d928535baa662849d0ced75acda117134c1cdc421facad2bd0f11b30a99ff'
ALLOWED_ELEMENTS = {'C','H','B','N','O','F','Si','P','S','Cl','Br','I'}
MEASUREMENT_METHOD = re.compile(r'transpir|closed cell|^CCELL|ebulli|^EBULLIO|^TWINEBU|manomet|^MANOM|diaphragm|gas saturation|inclined piston|^INCPIST|knudsen effusion|torsion effusion|isoten|^DCELL|^static|bubble-point|recirculating still', re.I)

def arr(x): return x if isinstance(x,list) else ([] if x is None else [x])
def compact(x):
    if isinstance(x,dict): return {k:compact(v) for k,v in x.items() if k!='tml_elements'}
    if isinstance(x,list): return [compact(v) for v in x]
    return x
def js(x): return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def number(x):
    try: return float(x)
    except (ValueError,TypeError): return math.nan
def write_csv(path, rows):
    if not rows: return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def chemistry_flags(inchi):
    if not inchi.startswith('InChI=1S/'): return ['nonstandard_or_missing_inchi']
    f=inchi.split('/')[1]; elems=set(re.findall(r'[A-Z][a-z]?',f)); bad=[]
    if '.' in f: bad.append('disconnected_formula')
    if '/q' in inchi or '/p' in inchi: bad.append('charge_or_protonation_layer')
    if '/i' in inchi: bad.append('isotope_layer')
    if 'C' not in elems: bad.append('no_carbon')
    if not elems <= ALLOWED_ELEMENTS: bad.append('element_outside_scope')
    return bad
def state_value(block,values,kind):
    key,label=('eTemperature','Temperature, K') if kind=='T' else ('ePressure','Pressure, kPa')
    defs={v['nVarNumber']:v for v in arr(block.get('Variable'))}
    found=[]
    for v in arr(values.get('VariableValue')):
        d=defs.get(v['nVarNumber'],{}).get('VariableID',{}).get('VariableType',{})
        if d.get(key)==label: found.append((v['nVarValue'], 'variable', compact(v)))
    for c in arr(block.get('Constraint')):
        if c.get('ConstraintID',{}).get('ConstraintType',{}).get(key)==label:
            found.append((c['nConstraintValue'],'constraint',compact(c)))
    if len(found)!=1: return None, 'missing_or_ambiguous', found
    return found[0]
def curve(ts):
    ts=sorted(set(ts)); exact_n=len(ts); clusters=[]
    for t in ts:
        if not clusters or t-clusters[-1][0]>0.1+1e-9:clusters.append([t])
        else:clusters[-1].append(t)
    ts=[statistics.median(g) for g in clusters]; n=len(ts)
    if not n: return {'distinct_T':0,'temperature_levels_0p1K':0,'T_min_K':'','T_max_K':'','T_span_K':0,'warm_T_count':0,'cold_T_count':0,'long_curve':False,'three_anchor_curve':False}
    lo,hi=ts[0],ts[-1];span=hi-lo
    nw=sum(t>=lo+0.7*span-1e-9 for t in ts);nc=sum(t<=lo+0.3*span+1e-9 for t in ts)
    long=n>=6 and span>=30-1e-9
    return {'distinct_T':exact_n,'temperature_levels_0p1K':n,'T_min_K':lo,'T_max_K':hi,'T_span_K':span,'warm_T_count':nw,'cold_T_count':nc,'long_curve':long,'three_anchor_curve':long and nw>=3 and nc>=2}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--archive',type=pathlib.Path,required=True);a.add_argument('--enthalpy',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True)
    args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    sha=digest(args.archive);hsha=digest(args.enthalpy)
    if sha!=EXPECTED_SHA256: raise SystemExit('Archive SHA-256 differs from the audited NIST release.')
    if hsha!=EXPECTED_H_SHA256: raise SystemExit('Enthalpy CSV SHA-256 differs from the audited RDR data file 250199.')
    pressure=[];nist_h=[];boiling=[];sources={};blocks_meta=[];compounds={};counts=collections.Counter();errors=[]
    with tarfile.open(args.archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.json'):continue
            counts['json_studies']+=1; data=json.load(tar.extractfile(member));citation=compact(data.get('Citation',{}));doi=citation.get('sDOI',member.name[:-5])
            cs={c['RegNum']['nOrgNum']:compact(c) for c in arr(data.get('Compound'))}
            for bi,b in enumerate(arr(data.get('PureOrMixtureData'))):
                if len(arr(b.get('Component')))!=1: continue
                c=cs[arr(b['Component'])[0]['RegNum']['nOrgNum']];inchi=c.get('sStandardInChI',''); compounds[inchi]=c
                phases=[x.get('ePhase','') for x in arr(b.get('PhaseID'))]
                for prop in arr(b.get('Property')):
                    groups=prop.get('Property-MethodID',{}).get('PropertyGroup',{})
                    details=[v for v in groups.values() if isinstance(v,dict)]
                    if len(details)!=1:continue
                    d=details[0];name=d.get('ePropName',d.get('sPropName',''))
                    if name not in (P_NAME,H_NAME,B_NAME): continue
                    counts[name+'_blocks']+=1;phase=prop.get('PropPhaseID',{}).get('ePropPhase','')
                    sid=f"{doi}#d{b.get('nPureOrMixtureDataNumber',bi+1)}#p{prop['nPropNumber']}"
                    method=d.get('eMethodName',d.get('sMethodName',''));sources[doi]=citation
                    blocks_meta.append({'series_id':sid,'archive_member':member.name,'compound':c,'citation':citation,'metadata':compact({k:v for k,v in b.items() if k!='NumValues'}),'target_property_number':prop['nPropNumber']})
                    for ni,values in enumerate(arr(b.get('NumValues'))):
                        for pv in arr(values.get('PropertyValue')):
                            if pv['nPropNumber']!=prop['nPropNumber']: continue
                            raw=pv['nPropValue'];T,Torigin,Tmeta=state_value(b,values,'P' if name==B_NAME else 'T')
                            r={'record_id':f'{sid}#r{ni+1}','series_id':sid,'archive_member':member.name,'data_number':b.get('nPureOrMixtureDataNumber'),'property_number':prop['nPropNumber'],'numvalues_index_1based':ni+1,
                               'inchi':inchi,'inchikey':c.get('sStandardInChIKey',''),'name':arr(c.get('sCommonName',['']))[0],'formula':c.get('sFormulaMolec',''),
                               'source_doi':doi,'source_year':citation.get('yrPubYr',''),'property_name':name,'property_phase':phase,'block_phases_json':js(phases),'method':method,
                               'original_property_value':raw,'original_property_value_metadata_json':js(compact(pv)),'state_origin':Torigin,'state_metadata_json':js(Tmeta),'T_K':raw if name==B_NAME else T,
                               'stable_liquid_gas':phase=='Liquid' and set(phases)=={'Liquid','Gas'},'basic_chemistry_flags':';'.join(chemistry_flags(inchi))}
                            if T is None: errors.append({'record_id':r['record_id'],'error':'missing_or_ambiguous_state'})
                            if name==H_NAME:
                                r['H_kJ_mol']=raw;r['calorimetry_label']=bool(re.search('calor',method,re.I));nist_h.append(r)
                            else:
                                r['p_Pa']=None if name==B_NAME and T is None else (T*1000 if name==B_NAME else raw*1000)
                                r['measurement_method_screen']=bool(MEASUREMENT_METHOD.search(method))
                                r['in_numeric_domain']=250<=number(r['T_K'])<=500 and 1<=number(r['p_Pa'])<=20000
                                r['primary_candidate']=name==P_NAME and r['stable_liquid_gas'] and r['in_numeric_domain'] and not r['basic_chemistry_flags'] and r['measurement_method_screen']
                                (pressure if name==P_NAME else boiling).append(r)
    # A conservative full-InChI equality join. Never truncate stereochemical layers.
    with args.enthalpy.open(newline='',encoding='utf-8') as f: raw_h=list(csv.DictReader(f))
    H=[]
    for line,row in enumerate(raw_h,2):
        r={'record_id':f'rdr250199#csvline{line}','csv_line_1based':line,'source_row_index':row.get('',row.get('Unnamed: 0','')),'inchi':row['InChI'],'name':row['name'],
           'H_reported_kJ_mol':number(row['Enthalpy']),'T_reported_K':number(row['Tm (K)']),'H_corrected_298_kJ_mol':number(row['Hvap_298']),'method':row['Method'],'source_reference_codes':row['Reference'],'notes':row['Notes'],
           'reported_experimental_T_range':row['Temp. range (K)'],'deviation_reported':row['Deviation'],'original_row_json':js(row)}
        r['C_candidate']=r['method']=='C' and 250<=r['T_reported_K']<=500 and math.isfinite(r['H_reported_kJ_mol']) and r['H_reported_kJ_mol']>0 and not r['notes']
        r['source_verification_status']='not_primary_paper_verified'
        r['measurement_vs_reference_T_status']='unresolved'
        if r['reported_experimental_T_range']:
            try:
                ran=ast.literal_eval(r['reported_experimental_T_range'])
                if len(ran)==2 and all(math.isfinite(number(x)) for x in ran):
                    r['measurement_vs_reference_T_status']='reported_T_inside_listed_range' if ran[0]<=r['T_reported_K']<=ran[1] else 'reported_T_outside_listed_range_review_correction'
            except (SyntaxError,ValueError,TypeError):r['measurement_vs_reference_T_status']='unparseable_range'
        H.append(r)
    hp=collections.defaultdict(list); pp=collections.defaultdict(list); sp=collections.defaultdict(list); nh=collections.defaultdict(list)
    for h in H:hp[h['inchi']].append(h)
    for h in nist_h:nh[h['inchi']].append(h)
    primary=[r for r in pressure if r['primary_candidate']]
    for p in primary:pp[p['inchi']].append(p);sp[p['series_id']].append(p)
    # Count repeated tuples without silently deleting possible independent replicates.
    pdup=collections.Counter((p['source_doi'],p['inchi'],p['T_K'],p['p_Pa']) for p in pressure)
    hdup=collections.Counter((h['inchi'],h['T_reported_K'],h['H_reported_kJ_mol'],h['method'],h['source_reference_codes']) for h in H)
    for p in pressure:p['same_doi_identity_T_p_count']=pdup[(p['source_doi'],p['inchi'],p['T_K'],p['p_Pa'])]
    for h in H:
        h['same_identity_T_H_method_reference_count']=hdup[(h['inchi'],h['T_reported_K'],h['H_reported_kJ_mol'],h['method'],h['source_reference_codes'])]
        h['has_primary_pressure_match']=h['inchi'] in pp
    series=[]
    for sid,rs in sorted(sp.items()):
        series.append({'series_id':sid,'inchi':rs[0]['inchi'],'name':rs[0]['name'],'source_doi':rs[0]['source_doi'],'method':rs[0]['method'],'pressure_rows':len(rs),**curve(r['T_K'] for r in rs)})
    molecule=[]
    for i,rs in sorted(pp.items()):
        hs=hp[i];cc=[h for h in hs if h['C_candidate']];cu=curve(r['T_K'] for r in rs);nm=rs[0]['name']
        acid=bool(re.search(r'\bacid\b',nm,re.I) and not re.search(r'\bester\b',nm,re.I))
        ins=[h for h in cc if cu['T_min_K']<=h['T_reported_K']<=cu['T_max_K']]
        owned=[s for s in series if s['inchi']==i]
        molecule.append({'inchi':i,'inchikey':rs[0]['inchikey'],'name':nm,'primary_pressure_rows':len(rs),'source_doi_count':len({r['source_doi'] for r in rs}),**cu,
          'eligible_single_source_series_count':sum(s['three_anchor_curve'] for s in owned),'enthalpy_rows_any_method':len(hs),'C_candidate_rows':len(cc),'C_candidate_rows_in_pressure_envelope':len(ins),
          'nist_calorimetry_label_rows':sum(h['stable_liquid_gas'] and h['calorimetry_label'] for h in nh[i]),'acid_name_review_flag':acid,'full_structure_and_phase_review_complete':False,
          'pressure_source_dois_json':js(sorted({r['source_doi'] for r in rs})),'C_enthalpy_record_ids_json':js([h['record_id'] for h in cc])})
    # Source code similarity is only a lookup aid, NOT proof of source identity.
    code_doi=collections.defaultdict(list)
    for doi,c in sources.items():
        t=c.get('TRCRefID',{});code=f"{t.get('yrYrPub','')}{t.get('sAuthor1','').upper()}/{t.get('sAuthor2','').upper()}"
        code_doi[code].append(doi)
    grouped=collections.defaultdict(list)
    for h in H:
        if h['C_candidate'] and h['has_primary_pressure_match']:grouped[h['source_reference_codes']].append(h)
    ref_audit=[]
    for ref,rs in sorted(grouped.items()):
        ds=set()
        try:
            for code in ast.literal_eval(ref):ds.update(code_doi.get(code,[]))
        except (ValueError,SyntaxError):pass
        ref_audit.append({'source_reference_codes':ref,'C_rows':len(rs),'molecular_identifiers':len({r['inchi'] for r in rs}),'candidate_dois_from_year_author_code_json':js(sorted(ds)),
          'status':'primary_methods_and_data_lineage_review_required','enthalpy_record_ids_json':js([r['record_id'] for r in rs])})
    liquid=[r for r in pressure if r['stable_liquid_gas']]
    numeric=[r for r in liquid if r['in_numeric_domain']]
    def tally(rows):return {'records':len(rows),'molecular_identifiers':len({r['inchi'] for r in rows})}
    stats={'archive_bytes':args.archive.stat().st_size,'archive_sha256':sha,'enthalpy_sha256':hsha,'counts':dict(counts),'extraction_errors':len(errors),'temperature_level_grouping_K':0.1,
      'all_pure_pressure_properties':tally(pressure),'stable_liquid_gas_pressure':tally(liquid),'numeric_domain_pressure':tally(numeric),'primary_method_and_chemistry_screen':tally(primary),
      'primary_distinct_doi_identity_T_p_tuples':len({(r['source_doi'],r['inchi'],r['T_K'],r['p_Pa']) for r in primary}),
      'primary_molecules_with_any_enthalpy':sum(m['enthalpy_rows_any_method']>0 for m in molecule),'primary_molecules_with_C_candidate':sum(m['C_candidate_rows']>0 for m in molecule),
      'primary_C_candidate_records':sum(m['C_candidate_rows'] for m in molecule),'primary_molecules_with_C_inside_pressure_envelope':sum(m['C_candidate_rows_in_pressure_envelope']>0 for m in molecule),
      'long_curve_molecules':sum(m['long_curve'] for m in molecule),'three_anchor_curve_molecules':sum(m['three_anchor_curve'] for m in molecule),
      'three_anchor_curve_molecules_with_C':sum(m['three_anchor_curve'] and m['C_candidate_rows']>0 for m in molecule),
      'single_series_three_anchor_molecules':sum(m['eligible_single_source_series_count']>0 for m in molecule),
      'single_series_three_anchor_molecules_with_C':sum(m['eligible_single_source_series_count']>0 and m['C_candidate_rows']>0 for m in molecule),
      'non_acid_name_primary_molecules':sum(not m['acid_name_review_flag'] for m in molecule),
      'non_acid_name_C_molecules':sum(not m['acid_name_review_flag'] and m['C_candidate_rows']>0 for m in molecule),
      'non_acid_name_three_anchor_C_molecules':sum(not m['acid_name_review_flag'] and m['three_anchor_curve'] and m['C_candidate_rows']>0 for m in molecule),
      'nist_liquid_calorimetry_label_matched_molecules':sum(m['nist_calorimetry_label_rows']>0 for m in molecule),
      'C_source_reference_groups':len(ref_audit),'enthalpy_raw_records':len(H),'enthalpy_raw_identifiers':len({h['inchi'] for h in H}),
      'review_status':'Feasibility candidates only. No molecular identifier or C label is certified as a fully validated independent training observation.'}
    for name,rows in [('pressure_records.csv',pressure),('boiling_records_supplement.csv',boiling),('enthalpy_records.csv',H),('thermoml_enthalpy_records.csv',nist_h),('molecule_audit.csv',molecule),('series_audit.csv',series),('enthalpy_source_audit.csv',ref_audit),('extraction_errors.csv',errors)]:write_csv(args.out/name,rows)
    (args.out/'statistics.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    with (args.out/'thermoml_provenance.jsonl').open('w',encoding='utf-8') as f:
        for b in blocks_meta:f.write(js(b)+'\n')
    (args.out/'citations.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
