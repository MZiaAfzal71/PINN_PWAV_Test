#!/usr/bin/env python3
from pathlib import Path
import csv, json, html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent;R=ROOT/'results';OUT=ROOT/'PINN_Pressure_Enthalpy_Join_Audit.pdf'
s=json.loads((R/'statistics.json').read_text());d=json.loads((R/'diagnostic_summary.json').read_text());v=json.loads((R/'xml_verification.json').read_text());sens=json.loads((R/'pressure_ceiling_sensitivity.json').read_text())
font=Path(matplotlib.get_data_path())/'fonts/ttf'
for n,f in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf'),('DVI','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(n,str(font/f)))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DVI',boldItalic='DVB')
navy=colors.HexColor('#122C43');teal=colors.HexColor('#087E83');ink=colors.HexColor('#243746');gray=colors.HexColor('#536573');line=colors.HexColor('#D7E1E7')
styles=StyleSheet1()
for name,size,lead,color,weight in [('body',9.8,14,ink,'DV'),('small',8.5,12,gray,'DV'),('title',22,27,navy,'DVB'),('subtitle',11,15,teal,'DVB'),('cell',8.5,11.6,ink,'DV'),('header',8.5,11.6,colors.white,'DVB'),('ref',8.1,11.5,ink,'DV')]:
    styles.add(ParagraphStyle(name=name,fontName=weight,fontSize=size,leading=lead,textColor=color,spaceAfter=7 if name not in ('cell','header') else 0))
story=[]
def p(text,style='body'):story.append(Paragraph(text,styles[style]))
def h(text):p(text,'subtitle')
def page(n,title):
    if story:story.append(PageBreak())
    p(f'PRESSURE–ENTHALPY AUDIT  /  {n:02d}','small');p(title,'title')
def table(headers,rows,widths):
    data=[[Paragraph(str(c),styles['header']) for c in headers]]+[[Paragraph(str(c),styles['cell']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,line),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F8FA')])]))
    story.extend([t,Spacer(1,9)])
def note(text):
    t=Table([[Paragraph(text,styles['body'])]],colWidths=[487]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#EDF5F6')),('BOX',(0,0),(-1,-1),.5,line),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.extend([t,Spacer(1,10)])

page(1,'The join is promising, with a clear curation gate')
p('Prepared for Muhammad Zia Afzal · 14 September 2026','small')
note('<b>Recommendation:</b> retain temperature-dependent liquid vapor pressure coupled to calorimetric vaporization enthalpy as the research problem. The data overlap is adequate to pursue. Independent measurement provenance is the remaining feasibility gate before training.')
p('The supplied NIST archive is intact: its 189,433,115 bytes and SHA-256 match the documented release. All 11,923 JSON studies were scanned. The equivalent XML copies were excluded from counting. [1]')
table(['Progressive pressure screen','Rows','Identifiers'],[
('Pure-component vapor or sublimation pressure','66,226','1,943'),('Liquid property phase with Liquid/Gas equilibrium','44,515','1,455'),('Also 250–500 K and 1–20,000 Pa','20,145','1,111'),('Also basic chemical and measurement-method screens','16,214','860')],[321,80,86])
p('“Identifiers” means complete Standard InChI strings. These counts precede molecular graph, stereochemical, phase-stability and full source-lineage validation. Repeated observations are retained and flagged: the 16,214 rows contain 15,953 unique (DOI, InChI, T, p) tuples.')
table(['Within the 860-identifier candidate pressure pool','Count'],[
('Matched to any compendium enthalpy method','742'),('Matched to candidate calorimetry (Method exactly C)','214'),('Candidate C rows, across 190 reference groups','793'),('At least one C temperature inside the pressure envelope',s['primary_molecules_with_C_inside_pressure_envelope']),('Molecules supporting the three-warm-anchor/cold-test design',s['three_anchor_curve_molecules']),('Those also possessing candidate C enthalpy',s['three_anchor_curve_molecules_with_C'])],[407,80])
p('<b>Decision boundary:</b> the proposed ≥500 pressure-molecule and ≥150 long-curve planning targets are supported numerically. The ≥100 <i>source-verified independent</i> calorimetric-molecule target is still unproven. The 214 matches are an upper bound on that curated set, not a completed benchmark. These planning targets are not a statistical power calculation.','small')

page(2,'What makes a valid pressure–enthalpy join')
table(['Check','Implemented rule and remaining limitation'],[
('Chemical identity','Join on the full unchanged Standard InChI. Preserve stereochemical layers. Basic element, disconnected-component, charge/protonation and isotope screens are applied. No graph-toolkit validation or correction of source identities has been performed.'),
('Phase','Require one component, property phase Liquid, and exactly Liquid/Gas block phases. Exclude crystals and metastable liquids. Original papers must still confirm a stable liquid at each retained temperature.'),
('Units and state','p[kPa] × 1,000 gives Pa; T remains K. H remains kJ/mol in exported tables and becomes J/mol inside the physics loss. Temperature comes from the appropriate variable or constraint, using its numeric identifier.'),
('Pressure method','Retain recognizable static/manometric, ebulliometric, transpiration/gas-saturation, effusion and related equilibrium-pressure methods. Flag correlations, generic calculations, thermal-analysis and unrecognized methods outside the main pool.'),
('Enthalpy method','C identifies calorimetry. A and pressure-derived methods do not establish an independent calorimetric label. A C label alone does not establish actual measurement temperature, source lineage or freedom from corrections. [3]'),
('Data lineage','Keep pressure and enthalpy observations in separate tables, linked by molecular identity and original record IDs. Do not multiply them into a pressure×enthalpy Cartesian table or count cross-database copies twice.')],[100,387])
h('The temperature fields need particular care')
p('Use <b>Enthalpy</b> and <b>Tm (K)</b> as the compendium-reported value and temperature. Tm is not a melting point here. A value reported at 298 K may already be corrected in the original study. <b>Hvap_298</b> is a derived field, not a second independent observation. The heat-capacity model fields T_low, T_high and T_mid are not experimental pressure coverage. [2]')
p('Among the 793 C candidates, 772 lack a usable listed experimental temperature range, 17 have reported temperature inside that range, and four outside it. The missing range does not invalidate the measurement; it means the primary paper is needed to establish measurement versus reference temperature.')
p('The 36 acid-name flags leave 824 pressure identifiers and 209 C-matched identifiers without that flag. This limited name screen is a review aid, not a complete test for carboxylic acids, vapor association, decomposition or nonideal behavior.','small')

page(3,'Three real examples of why a naïve merge fails')
p('These examples were traced through the supplied ThermoML numerical records and original-study abstracts. The full experimental methods sections were not obtained. Accordingly, they support source and method review, not blanket certification of independent observations.')
table(['Compound / source','Compendium entry','ThermoML entry'],[
('Ethyl decanoate<br/>2009ZAI/PAU · [4]','69.9 kJ/mol<br/>305 K<br/>Method C','69.9 kJ/mol<br/>304.79 K<br/>Static calorimetry'),
('Cyclohexyl butanoate<br/>2003ZAI/VER · [5]','60.1 kJ/mol<br/>298 K<br/>Method C','58.72 kJ/mol<br/>315.57 K<br/>Static calorimetry'),
('(-)-Verbenone<br/>2013STE/FUL · [6]','58.9 kJ/mol<br/>298 K<br/>Method C','58.9 kJ/mol<br/>298.15 K<br/>Static calorimetry')],[203,142,142])
h('Ethyl decanoate: rounding can conceal repeated evidence')
p('The same source and enthalpy occur at rounded temperatures. Treat these as a duplicate candidate, not two independent labels. ThermoML also provides eight pressure points from the 2009 Knudsen experiment. Other eligible pressure sources exist, but a different DOI still needs a check for reused measurements.')
h('Cyclohexyl butanoate: the reported temperatures differ')
p('The two enthalpies are not interchangeable same-temperature targets. Recover whether the 298 K value was corrected from the measured-temperature result. The source contains separate Knudsen and transpiration pressure series, as well as calorimetry. Its abstract also describes refinement using the three methods, so cross-method dependence must be checked. Same-paper measurements can be distinct, but independence cannot be inferred from method labels alone.')
h('(-)-Verbenone: reference-temperature rounding matters')
p('The identical enthalpy appears at 298 and 298.15 K in the two compilations. The source distinguishes static pressure measurements from Calvet microcalorimetry, making it a useful candidate for detailed review. Keep the exact stereoisomer and one measurement lineage. Do not automatically equate every 298 K and 298.15 K entry across the dataset.')
note('Practical rule: join identities first. Then audit each enthalpy observation’s source, measurement temperature, phase and corrections. Evaluate p(M,Tp) and H(M,TH) at their own validated temperatures; an identical-temperature database join is not required for multitask supervision.')

page(4,'Coverage and a descriptive physics check')
p(f"Grouping temperatures within 0.1 K prevents near-replicates from becoming separate anchors. There are <b>{s['long_curve_molecules']}</b> molecules with at least six temperature levels over ≥30 K. <b>{s['three_anchor_curve_molecules']}</b> also have three levels in the warmest 30% and two in the coldest 30% of the span. Of these, <b>{s['three_anchor_curve_molecules_with_C']}</b> have a C candidate.")
p(f"Requiring the protocol to fit within one source series leaves <b>{s['single_series_three_anchor_molecules']}</b> molecules, <b>{s['single_series_three_anchor_molecules_with_C']}</b> with C candidates (101 after the limited acid-name exclusion). This is the stronger starting point for isolating temperature extrapolation from source differences.")
table(['Pressure ceiling','Pressure IDs','C-matched IDs','Warm/cold IDs with C'],[(f"{x['p_ceiling_Pa']/1000:g} kPa",x['identifiers'],x['C_match_identifiers'],x['three_anchor_C_identifiers']) for x in sens],[112,110,120,145])
di=list(csv.DictReader((R/'local_clapeyron_diagnostics.csv').open()));x=np.array([float(z['H_reported_kJ_mol']) for z in di]);y=np.array([float(z['local_CC_H_kJ_mol']) for z in di])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(figsize=(7.0,2.9));lo=min(x.min(),y.min())-3;hi=max(x.max(),y.max())+3
ax.plot([lo,hi],[lo,hi],color='#82909a',lw=1,ls='--');ax.scatter(x,y,s=20,alpha=.65,color='#087E83',edgecolors='none');ax.set(xlabel='Compendium-reported C-method H (kJ/mol)',ylabel='Local pressure-slope H (kJ/mol)',xlim=(lo,hi),ylim=(lo,hi));ax.grid(alpha=.12);fig.tight_layout();figpath=ROOT/'local_clapeyron_diagnostic.png';fig.savefig(figpath,dpi=170);plt.close(fig)
story.append(Image(str(figpath),width=487,height=202));story.append(Spacer(1,6))
p(f"<b>Descriptive result:</b> {d['comparisons']} local comparisons for {d['identifiers']} identifiers give median absolute difference {d['median_absolute_difference_percent']:.2f}% and 90th percentile {d['p90_absolute_difference_percent']:.2f}%. These are pressure-slope comparisons, not PINN predictions, validation scores or proof of independent measurements.")
p('Within one series, fit ln(p) versus 1/T using at least six distinct temperatures spanning ≥10 K, within ±20 K and bracketing the reported H temperature. Approximate H = −R × slope. This unweighted local fit assumes nearly constant H and suitable vapor behavior. No observations were excluded for failing this diagnostic.','small')

page(5,'The research problem to fix now')
note('<b>Research question:</b> Can independent calorimetric vaporization enthalpies improve cold-end liquid vapor-pressure extrapolation, and does a thermodynamic differential constraint add value beyond the same enthalpy labels in ordinary multitask learning?')
table(['Decision','Specification'],[
('Primary target','log<sub>10</sub>[p<sub>sat</sub>(M,T)/(1 Pa)] for vetted pure organic liquids, initially 250–500 K and 1–20,000 Pa.'),
('Auxiliary target','ΔH<sub>vap</sub>(M,T) at its validated measurement/reference state and temperature. Prefer direct calorimetry; explicitly account for any corrections.'),
('Primary comparison','Pressure-only model; multitask p/H model without physics; PINN with exactly the same labels; and an Antoine-parameter model also allowed H supervision.'),
('Representation question','Compare conventional descriptors, PWAV core, full PWAV, ChemBERTa and fusion. This tests whether PWAV contributes beyond the descriptors included in your original representation.'),
('Evaluation','Hold out molecular clusters with all property labels. Adapt using three warm-end pressure anchors only; evaluate cold-end pressure. Tune adaptation on validation molecules. Hide held-out H in this main experiment.'),
('Evidence of contribution','Paired molecule-level error estimates, grouped resampling, single-source-series results, pressure-ceiling sensitivity and an explicit no-physics ablation. An extra-H-at-test-time experiment is a separate information-budget comparison.')],[105,382])
h('Physical relationship and its scope')
p('Let u = ln[p/(1 Pa)]. Use r = [R T² ∂u/∂T − H]/H<sub>scale</sub>, with H in J/mol and R in J/(mol K). This is an approximation to exact Clapeyron, dp/dT = H/[T(v<sub>g</sub>−v<sub>l</sub>)]. Dilute approximately ideal vapor and negligible liquid volume are required. A low pressure ceiling alone does not verify these assumptions.')
p('Resolve source lineage, actual liquid stability and standard-state versus saturation enthalpy before freezing the labels. Keep related source copies and molecular clusters in the same fold. With roughly 100 candidate paired single-series molecules before full review, avoid overclaiming precision from a small fixed test subset.')
p('<b>Novelty:</b> vapor-pressure PINNs and Clapeyron-based molecular models already exist. [7,8] The contribution should be the transparent independent-calorimetry benchmark and a controlled answer to when physical coupling helps. No predictive improvement or publication outcome is established by this audit.','small')

page(6,'Reproducible files and verification')
p(f"An independent XML parser checked <b>{v['xml_records_compared']} observations in {v['xml_studies']} studies</b>, including temperature variables and constraints, boiling at specified pressure, phase labels, chemical identifiers and unit conversions. It found <b>zero mismatches</b>. Nineteen temperature-missing crystal records were logged and excluded from the primary liquid pool.")
table(['Companion ZIP content','Purpose'],[
('audit_thermoml.py','Streams the original archive and recreates all extraction, identity, method and coverage tables. Standard-library Python; no scraping.'),
('verify_and_diagnose.py','Independent XML spot checks, local pressure-slope diagnostics and pressure-ceiling sensitivity. Requires NumPy.'),
('results/molecule_audit.csv','The molecule-level pressure–enthalpy join, with coverage, source counts and linked enthalpy record IDs.'),
('Pressure / enthalpy record tables','Original values, state metadata, units, methods, exclusions, source identifiers and duplicate flags. Includes separate ThermoML enthalpy and boiling supplements.'),
('Source audit and provenance files','190 C-reference review groups, three worked examples, original property/variable/constraint metadata and citations.'),
('README.md and inputs/','Exact reproduction commands, field meanings, limitations and attributed source CSV. The uploaded 189 MB archive is used separately.')],[213,274])
p('Archive SHA-256:','small');p(s['archive_sha256'][:32]+'<br/>'+s['archive_sha256'][32:],'small')
h('Sources')
refs=[
('[1] NIST ThermoML Archive, supplied 2020-09-30 release.','https://data.nist.gov/od/id/mds2-2422'),
('[2] Leenhouts et al. Replication Data for Thermodynamics-informed Graph Neural Networks for Phase Transition Enthalpies. KU Leuven RDR, V2; vaporization file 250199.','https://doi.org/10.48804/CBHEAB'),
('[3] NIST Chemistry WebBook: experimental method codes.','https://webbook.nist.gov/chemistry/enthalpy.html'),
('[4] Zaitsau et al. Thermodynamics of Ethyl Decanoate (2009).','https://doi.org/10.1021/je900093h'),
('[5] Zaitsau et al. Comprehensive Study of Vapor Pressures and Enthalpies of Vaporization of Cyclohexyl Esters (2003).','https://doi.org/10.1021/je025634v'),
('[6] Stejfa et al. Thermodynamic study of selected monoterpenes (2013).','https://doi.org/10.1016/j.jct.2013.01.009'),
('[7] Pavšek et al. Clapeyron Neural Networks for Single-Species Vapor-Liquid Equilibria (2026 preprint).','https://arxiv.org/abs/2602.18313'),
('[8] Hoffmann et al. GRAPPA: predicting vapor pressures with graph neural networks (2025).','https://arxiv.org/abs/2501.08729')]
for label,url in refs:p(html.escape(label)+' <link href="'+url+'" color="#087E83">Source</link>','ref')
p('This report updates the data-feasibility stage of the earlier research brief. It contains no trained PINN, fitted predictive benchmark or finalized train/test split.','small')

def footer(c,doc):
    c.setStrokeColor(line);c.line(54,42,541,42);c.setFont('DV',8);c.setFillColor(gray);c.drawString(54,29,'PINN research feasibility · 14 September 2026');c.drawRightString(541,29,str(doc.page))
SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),rightMargin=54,leftMargin=54,topMargin=42,bottomMargin=55,title='Pressure–Enthalpy Join Audit',author='Research audit for Muhammad Zia Afzal').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
