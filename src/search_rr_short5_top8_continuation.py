#!/usr/bin/env python3
"""Exact, branch-local 50k-additional continuation for the verified top eight.

The v5 source checkpoint is read once, hash-checked, and copied into the v6
namespace.  The copied state is then resumed with the existing literal-R2 v5
engine; the source checkpoint is never modified.
"""
from __future__ import annotations
import json, sys, shutil, hashlib, argparse, importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
TOP=("short_ell2_r1_70","short_ell4_r1_12","short_ell1_r1_98","short_ell2_r1_40","short_ell3_r1_64","short_ell2_r1_37","short_ell2_r1_107","short_ell3_r1_56")
OUT=ROOT/'outputs/rr_short5_top8_continuation.json'
CPROOT=ROOT/'outputs/checkpoints/rr_short5/top8_continuation_v6'

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
pilot=load('rr_top8_pilot',ROOT/'src/search_rr_short1_4_corrected_fair.py')

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix('.json.tmp');q.write_text(json.dumps(x,indent=2,sort_keys=True),encoding='utf8');q.replace(p)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--additional',type=int,default=50000);ap.add_argument('--checkpoint-every',type=int,default=1000);ap.add_argument('--resume',action='store_true');a=ap.parse_args()
 r=json.loads((ROOT/'outputs/rr_short1_4_corrected_fair_results.json').read_text(encoding='utf8'))
 lookup={}
 for rid,row in r['roots'].items():
  for c in row['admission']['frozen_R1_children']: lookup[c['branch_id']]=(row['root_record'],c)
 if set(TOP)-set(lookup):raise AssertionError('top8 manifest mismatch')
 old=pilot.CHECKPOINT_ROOT;pilot.CHECKPOINT_ROOT=CPROOT
 rows=[]
 for bid in TOP:
  root,child=lookup[bid]; src=ROOT/next(b for x in r['roots'].values() for b in x['branches'] if b['branch_id']==bid)['checkpoint']['path']; dst=CPROOT/root['root_id']/bid/'checkpoint.json'; base=json.loads(src.read_text(encoding='utf8'))
  basecfg=pilot.branch_config(root,child,5000)
  if base.get('schema')!=pilot.CHECKPOINT_SCHEMA or base.get('config')!=basecfg or sha(src)!=next(b for x in r['roots'].values() for b in x['branches'] if b['branch_id']==bid)['checkpoint']['sha256']:raise AssertionError('base identity failure '+bid)
  cfg=pilot.branch_config(root,child,5000+a.additional)
  if not dst.exists():
   base['config']=cfg;base['top8_continuation']={'schema':'rr-short5-top8-v6','source_checkpoint':str(src.relative_to(ROOT)),'source_sha256':sha(src),'base_expanded':base['stats']['expanded'],'additional_budget':a.additional};write(dst,base)
  else:
   existing=json.loads(dst.read_text(encoding='utf8'))
   if existing.get('config')!=cfg or existing.get('top8_continuation',{}).get('source_sha256')!=sha(src):raise AssertionError('v6 resume identity failure '+bid)
  result=pilot.run_branch(root,child,5000+a.additional,checkpoint_every=a.checkpoint_every,resume=True)
  rows.append({'child_id':bid,'base_expanded':5000,'additional_expanded':result['expanded']-5000,'continuation_result':result,'source_checkpoint_sha256':sha(src),'v6_checkpoint_sha256':result['checkpoint']['sha256']})
 pilot.CHECKPOINT_ROOT=old
 write(OUT,{'schema':'rr-short5-top8-continuation-v6','scope':'exact additional-cap study; nonempty frontiers are INCOMPLETE','additional_budget':a.additional,'recognizer_semantics':pilot.R2_SEMANTICS,'children':rows})
 print(json.dumps({'status':'DONE','children':len(rows),'additional':sum(x['additional_expanded'] for x in rows)},sort_keys=True))
if __name__=='__main__':main()
