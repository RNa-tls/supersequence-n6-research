"""Replay the TWO complete marked96 prefixes against independent static cover.
The prior literal-clean checker also proves these particular marked extrema
contain no dirty joint. It is not applied to arbitrary marked paths.
"""
import hashlib
import json
from pathlib import Path
from verify_round141_completion_cover_codex import complete_chain, controls

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'outputs/rr_round143_t4_b0_exact_prefix_codex.json'
    data=json.loads(source.read_text())
    row=next(r for r in data['rows'] if (r['A'],r['b'],r['D'],r['P'])==(0,0,14,96))
    assert row['complete'] and row['status']=='EXACT_P_PREFIXES_COMPLETE'
    sets=[];hashes={source.relative_to(ROOT).as_posix():hashlib.sha256(source.read_bytes()).hexdigest()}
    for name in ('producer','independent'):
        path=ROOT/row[name]['exported_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row[name]['export_sha256']
        hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        paths=[]
        for line in path.read_text().splitlines():
            r=json.loads(line)
            paths.append(tuple(r['entries'] if isinstance(r,dict) else r))
        sets.append(set(paths))
    assert sets[0]==sets[1] and len(sets[0])==2
    checks=controls()
    outcomes=[complete_chain(list(p)) for p in sorted(sets[0])]
    assert all(r['status']=='UNSAT' and r['complete_finite_decision'] and not r['capped'] for r in outcomes)
    out=dict(schema='round143-marked96-completion-v1',input_sha256=hashes,controls=checks,
             exact_marked_prefixes=2,independently_replayed_as_light_clean=True,
             c=6,instances=outcomes,all_static_completions_impossible=True,
             scope='Only Z=H=0,k=4,G=c=6,A=Bstar=0. Exact enumeration includes all marked96 paths, not just old clean paths.')
    destination=ROOT/'outputs/rr_round143_marked96_completion_codex.json'
    destination.write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(prefixes=2,unsat=2,nodes=sum(r['nodes'] for r in outcomes))))


if __name__=='__main__':
    main()
