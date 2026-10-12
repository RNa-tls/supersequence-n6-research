#!/bin/bash
# Wait for the running queue driver to finish, then start another pass (re-runs jobs that have no
# certificate yet -- e.g. failed ones -- and all nested delegated jobs).  Repeats until a pass
# launches nothing new or an INCUMBENT is reported.
PY=$1; WORD=$2; T=$3; TOP=$4; W=$5; TL=$6; shift 6
while pgrep -f "queue_drive[r].py $WORD $T $TOP" > /dev/null; do sleep 30; done
for pass in 2 3 4 5 6; do
  echo "pass $pass $(date +%T)" >> ${TOP%.json}.chain.log
  $PY -I rJ/src/queue_driver.py $WORD $T $TOP $W $TL "$@" >> ${TOP%.json}.queue.stdout 2>&1
  grep -q INCUMBENT ${TOP%.json}.queue.jsonl && break
  last_start=$(grep '"event": "start"' ${TOP%.json}.queue.jsonl | tail -1)
  echo "$last_start" | grep -q '"pending": 0' && break
done
echo "chain done $(date +%T)" >> ${TOP%.json}.chain.log
