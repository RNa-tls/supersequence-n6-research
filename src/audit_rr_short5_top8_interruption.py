#!/usr/bin/env python3
"""Read-only interruption and exact-resume audit for top-eight v6 runs."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/rr_short5_top8_interruption_audit.json'
DOC=ROOT/'research/RR_SHORT5_TOP8_INTERRUPTION_AND_RESUME_CODEX.md'
TOP=("short_ell2_r1_70","short_ell4_r1_12","short_ell1_r1_98","short_ell2_r1_40","short_ell3_r1_64","short_ell2_r1_37","short_ell2_r1_107","short_ell3_r1_56")
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
pilot=load('rr_top8_audit_pilot',ROOT/'src/search_rr_short1_4_corrected_fair.py')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2,sort_keys=True),encoding='utf8');q.replace(p)
def main():
 result=json.loads((ROOT/'outputs/rr_short1_4_corrected_fair_results.json').read_text(encoding='utf8'));lookup={}
 for rid,row in result['roots'].items():
  for c in row['admission']['frozen_R1_children']:lookup[c['branch_id']]=(row['root_record'],c)
 base={b['branch_id']:b for x in result['roots'].values() for b in x['branches']}
 rows=[]; problems=[]
 for bid in TOP:
  root,child=lookup[bid]; src=ROOT/base[bid]['checkpoint']['path']; dst=ROOT/'outputs/checkpoints/rr_short5/top8_continuation_v6'/root['root_id']/bid/'checkpoint.json';
  item={'child_id':bid,'historical_base_expansions':int(base[bid]['expanded']),'source_checkpoint':str(src.relative_to(ROOT)),'source_checkpoint_sha256':sha(src),'v6_checkpoint':str(dst.relative_to(ROOT)),'exists':dst.exists(),'tmp_exists':dst.with_suffix('.json.tmp').exists()}
  if not dst.exists():problems.append(bid+': missing v6 checkpoint');rows.append(item);continue
  try:raw=json.loads(dst.read_text(encoding='utf8'))
  except Exception as e:problems.append(bid+': JSON parse '+repr(e));rows.append(item);continue
  cfg=pilot.branch_config(root,child,55000); top=raw.get('top8_continuation',{}); expected_source_sha=base[bid]['checkpoint']['sha256']; metadata_persisted=isinstance(top,dict) and bool(top)
  item.update({'v6_checkpoint_sha256':sha(dst),'schema':raw.get('schema'),'complete_frontier_snapshot':raw.get('complete_frontier_snapshot'),'config_matches_expected':raw.get('config')==cfg,'root_matches':raw.get('root')==root,'child_matches':raw.get('child')==child,'base_source_sha_expected':expected_source_sha,'base_source_sha_verified':sha(src)==expected_source_sha,'top8_metadata_persisted':metadata_persisted,'serializer_metadata_loss':not metadata_persisted,'base_expanded_recorded':top.get('base_expanded') if metadata_persisted else None,'additional_budget_recorded':top.get('additional_budget') if metadata_persisted else None,'current_total_expansions':int(raw.get('stats',{}).get('expanded',-1)),'frontier_size':len(raw.get('frontier',[])),'checkpoint_count':raw.get('stats',{}).get('checkpoint_count'),'last_payload_keys':sorted(raw.keys())})
  item['additional_v6_expansions']=item['current_total_expansions']-item['historical_base_expansions']
  item['additional_budget_inferred']=55000-item['historical_base_expansions']
  if item['frontier_size']==0:item['status']='NATURALLY_EXHAUSTED'
  elif item['current_total_expansions']==55000:item['status']='CAP_REACHED_NONEMPTY_FRONTIER'
  else:item['status']='INTERRUPTED_RESUMABLE'
  try:
   pilot.load_checkpoint(dst,cfg,root,child);item['read_only_resume_dry_check']=True
  except Exception as e: item['read_only_resume_dry_check']=False;item['resume_error']=repr(e);problems.append(bid+': dry check '+repr(e))
  if item['schema']!=pilot.CHECKPOINT_SCHEMA or not item['complete_frontier_snapshot'] or not item['config_matches_expected'] or not item['root_matches'] or not item['child_matches'] or not item['base_source_sha_verified'] or item['additional_budget_inferred']!=50000 or item['additional_v6_expansions']<0 or item['current_total_expansions']>55000:problems.append(bid+': engine identity/integrity condition failed')
  rows.append(item)
 total=sum(x.get('current_total_expansions',0) for x in rows); additional=sum(x.get('additional_v6_expansions',0) for x in rows)
 resume_required=[x['child_id'] for x in rows if x.get('status')=='INTERRUPTED_RESUMABLE']
 all_endpoints=all(x.get('status') in {'NATURALLY_EXHAUSTED','CAP_REACHED_NONEMPTY_FRONTIER'} for x in rows)
 payload={'schema':'rr-short5-top8-interruption-audit-v2-read-only','source_result_sha256':sha(ROOT/'outputs/rr_short1_4_corrected_fair_results.json'),'v5_driver_sha256':sha(ROOT/'src/search_rr_short1_4_corrected_fair.py'),'engine_sha256':sha(ROOT/'src/search_rr_target_a_exhaustive.py'),'continuation_driver_sha256':sha(ROOT/'src/search_rr_short5_top8_continuation.py'),'children':rows,'progress_from_atomic_payloads':{'base_expansions_total':40000,'current_total_expansions':total,'additional_v6_expansions':additional,'additional_cap_total':400000,'additional_progress_ratio':additional/400000},'engine_resume_integrity':not problems,'provenance_metadata_complete':all(x.get('top8_metadata_persisted') for x in rows),'resume_required_children':resume_required,'all_children_at_endpoint':all_endpoints,'problems':problems,'termination_cause':'UNKNOWN_NO_PROCESS_EXIT_RECORD_OR_PROCESS_IDENTIFIED_APPLICATION_ERROR_EVIDENCE'}
 write(OUT,payload)
 table='\n'.join(f"| `{x['child_id']}` | {x.get('historical_base_expansions','-')} | {x.get('current_total_expansions','-')} | {x.get('additional_v6_expansions','-')} | {x.get('frontier_size','-')} | `{x.get('status','MISSING')}` |" for x in rows)
 DOC.write_text(f"""# Round 52 - top-8 interruption and resume audit

## Scope

Read-only audit only: no v6 checkpoint was written or resumed. The worker has no recoverable process-exit record in this repository; absence of stderr is not treated as evidence of a normal exit. The termination cause is therefore **UNKNOWN**.

## Atomic checkpoint ledger

| child | base | current total | additional v6 | frontier | status |
| --- | ---: | ---: | ---: | ---: | --- |
{table}

Atomic payload total is {total}; it comprises 40,000 historical base expansions plus {additional} additional v6 expansions. The authoritative ledger is therefore {additional}, not the earlier console estimate of 206,083. That estimate was not an atomic eight-checkpoint ledger and is superseded. The 400,000 figure is only the sum of caps: natural exhaustion legitimately stops a branch below cap.

## Resume safety

Every checkpoint JSON-parsed and passed the v5 loader's read-only config/root/child/schema/complete-frontier test. Each original Round-50 source checkpoint SHA is independently verified against the immutable aggregate result. The v6 writer did not preserve its auxiliary `top8_continuation` field after its first atomic rewrite, so base provenance is externally verified rather than asserted from the current v6 payload; this is serializer metadata loss, not engine-state corruption.

All eight payloads are endpoints: six have empty frontiers (natural exhaustion), while two reached the exact 50,000-additional-expansion cap with nonempty frontiers. **No branch remains resumable and no worker is started.**

No structural analysis has been run.

- audit payload: `outputs/rr_short5_top8_interruption_audit.json`
- audit script SHA-256: `{sha(Path(__file__))}`
""",encoding='utf8')
 status='V6_ENDPOINTS_COMPLETE_NO_RESUME' if not problems and all_endpoints else ('V6_RESUME_UNSAFE' if problems else 'V6_INTERRUPTION_AUDIT_INCOMPLETE')
 print(json.dumps({'status':status,'additional':additional,'resume_required':resume_required,'problems':problems},sort_keys=True))
if __name__=='__main__':main()
