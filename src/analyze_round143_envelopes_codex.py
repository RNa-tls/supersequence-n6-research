"""Necessary marked-capacity envelopes; unknown/equality never closes a row."""
import functools,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    budget=json.loads((ROOT/'outputs/rr_round143_threshold_budgets_codex.json').read_text())
    data=json.loads((ROOT/'outputs/rr_round143_marked_capacities_codex.json').read_text())
    table={(r['b'],r['D']):r['producer']['max_passes'] for r in data['rows'] if r['complete']}
    @functools.lru_cache(None)
    def conv(m,b,D):
        if m==1:return table.get((b,D))
        vals=[]
        for bj in range(b+1):
            for dj in range(D+1):
                a=table.get((bj,dj));c=conv(m-1,b-bj,D-dj)
                if a is None or c is None:return None
                vals.append(a+c)
        return max(vals)
    rows=[]
    for r in budget['rows']:
        x=dict(r);u=conv(r['m_max'],r['b_sum'],r['D_sum']);x['upper']=u
        x['status']='UNKNOWN_CAPACITY' if u is None else ('STRICT' if u<r['P_required'] else ('EQUALITY' if u==r['P_required'] else 'OPEN_CAPACITY'))
        # Tight sigma seams force >= one missing companion per seam;
        # any missing port can serve at most an incoming and outgoing seam.
        if r['Z']==r['H']==r['Bstar']==0 and r['D2']>2*r['D_sum']:
            x['status']='COMPANION_DEFICIT_OBSTRUCTION'
        rows.append(x)
    out=dict(schema='round143-marked-envelope-v1',rows=rows,
      counts={str(L):dict(Counter(r['status'] for r in rows if r['L']==L)) for L in (869,870,871)},
      scope='ARITHMETIC NECESSARY ROWS; NO LITERAL REALIZABILITY ASSUMED',
      threshold_closed={str(L):all(r['status'] in ('STRICT','COMPANION_DEFICIT_OBSTRUCTION') for r in rows if r['L']==L) for L in (869,870,871)})
    (ROOT/'outputs/rr_round143_marked_envelopes_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['counts']));print('869 residual:')
    for r in rows:
        if r['L']==869 and r['status'] not in ('STRICT','COMPANION_DEFICIT_OBSTRUCTION'):print(json.dumps(r))
if __name__=='__main__':main()
