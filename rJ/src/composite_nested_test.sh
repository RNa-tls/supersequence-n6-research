#!/bin/bash
# Nested-delegation test of composite_check.py on the n=6 phi-only chain set (optimum 873 = BASE 867 + 6).
# Builds top (FRONTIER=4) -> subtrees (NODE_LIMIT=3, open nodes delegated) -> sub-subtrees, checks the
# composite, then checks that each mutation is REJECTED.
# usage: composite_nested_test.sh PYTHON WORKDIR
PY=$1; D=$2; W=rI/certs/phi_only_n6_873.txt
mkdir -p $D; rm -f $D/top* $D/s_* $D/m_*
FRONTIER=4 $PY -I rJ/src/chainset_bc.py $W 6 $D/top.json 600 > /dev/null || exit 1
fr() { $PY -I -c "import json,sys; [print(f['id'], json.dumps(f['fix']).replace(' ','')) for f in json.load(open(sys.argv[1]))['frontier']]" $1; }
fr $D/top.json.frontier.json > $D/fr1.txt
while read id fx; do
  INIT_FIX="$fx" GLOBAL_FIX0=$D/top.json INIT_POOL=$D/top.json NODE_LIMIT=3 $PY -I rJ/src/chainset_bc.py $W 6 $D/s_$id.json 600 > /dev/null
  if [ -f $D/s_$id.json.frontier.json ]; then
    fr $D/s_$id.json.frontier.json > $D/fr2_$id.txt
    while read id2 fx2; do
      INIT_FIX="$fx2" GLOBAL_FIX0=$D/top.json INIT_POOL=$D/s_$id.json $PY -I rJ/src/chainset_bc.py $W 6 $D/s_${id}_$id2.json 600 > /dev/null
    done < $D/fr2_$id.txt
  fi
done < $D/fr1.txt
SUBS=$(ls $D/s_*.json | grep -v frontier)
NESTED=$(for f in $SUBS; do b=$(basename $f .json); [ $(echo $b | tr -cd _ | wc -c) -eq 2 ] && echo $f; done)
PARENT=$(for f in $SUBS; do [ -f $f.frontier.json ] && echo $f; done | head -1)
[ -n "$NESTED" ] && [ -n "$PARENT" ] || { echo "test setup did not produce nested delegation"; exit 1; }
ck() { $PY -I rJ/src/composite_check.py $W $D/top.json "$@" > $D/out.txt 2> $D/err.txt; echo $?; }
pass=0; fail=0
expect() { if [ "$2" = "$3" ]; then echo "  ok   $1"; pass=$((pass+1)); else echo "  FAIL $1 (rc=$2)"; fail=$((fail+1)); fi; }
rc=$(ck $SUBS); expect "genuine nested composite accepted" $rc 0; cat $D/out.txt
ONE=$(echo "$NESTED" | head -1)
rc=$(ck $(echo "$SUBS" | grep -v "^$ONE$")); expect "missing sub-subtree rejected" $rc 1
cp $ONE $D/m_dup.json; rc=$(ck $SUBS $D/m_dup.json); expect "duplicate certificate rejected" $rc 1
rc=$(ck $(echo "$SUBS" | grep -v "^$PARENT$")); expect "missing intermediate subtree rejected" $rc 1
$PY -I -c "
import json,sys; c=json.load(open(sys.argv[1])); c['init_fix']=c['init_fix'][:-1]; json.dump(c,open(sys.argv[2],'w'))" $ONE $D/m_fix.json
rc=$(ck $(echo "$SUBS" | grep -v "^$ONE$") $D/m_fix.json); expect "sub-subtree with altered initial fixings rejected" $rc 1
# a subtree that delegates its own root (no progress) must be rejected
FIRST=$(head -1 $D/fr1.txt); id=${FIRST%% *}; fx=${FIRST#* }
INIT_FIX="$fx" GLOBAL_FIX0=$D/top.json INIT_POOL=$D/top.json NODE_LIMIT=0 $PY -I rJ/src/chainset_bc.py $W 6 $D/m_self.json 600 > /dev/null
rc=$(ck $(echo "$SUBS" | grep -v "/s_${id}.json$" | grep -v "/s_${id}_") $D/m_self.json); grep -q "not strictly below" $D/err.txt || rc=99
expect "self-delegating subtree rejected (well-foundedness)" $rc 1
$PY -I -c "
import json,sys; c=json.load(open(sys.argv[1])); c['T']=c['T']+1; json.dump(c,open(sys.argv[2],'w'))" $ONE $D/m_T.json
rc=$(ck $(echo "$SUBS" | grep -v "^$ONE$") $D/m_T.json); expect "sub-subtree with different T rejected" $rc 1
echo "passed $pass, failed $fail"; [ $fail -eq 0 ]
