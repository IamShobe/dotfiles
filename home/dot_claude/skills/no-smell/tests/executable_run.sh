#!/usr/bin/env bash
# Regression test for check.sh: clean fixtures must not be flagged, every smelly line must be.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd); check="$here/../scripts/check.sh"
[[ -f $check ]] || check="$here/../scripts/executable_check.sh"
cd "$here/fixtures" || exit 2
fail=0
out=$(bash "$check" -- src/clean.ts src/__tests__/mock.spec.ts); status=$?
if (( status != 0 )) && grep -q '^== SMELL' <<< "$out"; then echo "FALSE POSITIVES:"; grep '^src/' <<< "$out"; fail=1; fi
out=$(bash "$check" -- src/smelly.ts src/smelly.py)
for n in 1 2 3 4 5 7 8; do grep -q "^src/smelly.ts:$n:" <<< "$out" || { echo "MISSED smelly.ts:$n"; fail=1; }; done
grep -q '^src/smelly.ts:6:' <<< "$out" || { echo "MISSED smelly.ts:6 (review)"; fail=1; }
grep -q '^src/smelly.ts:9:' <<< "$out" || { echo "MISSED smelly.ts:9 (review)"; fail=1; }
for n in 2 3 4 6; do grep -q "^src/smelly.py:$n:" <<< "$out" || { echo "MISSED smelly.py:$n"; fail=1; }; done
grep -q '^src/smelly.py:7:' <<< "$out" && { echo "FALSE POSITIVE smelly.py:7 (comment)"; fail=1; }
(( fail )) && exit 1; echo "check.sh: all fixtures pass"
