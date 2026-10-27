#!/usr/bin/env bash
set -uo pipefail

EVAL_FILE="${1:?Usage: bash evals/check.sh evals/refund-policy.json}"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required. Install jq and try again." >&2
  exit 2
fi

if ! jq -e '.checks | type == "array" and length > 0' "$EVAL_FILE" >/dev/null; then
  echo "ERROR: $EVAL_FILE must contain a non-empty checks array." >&2
  exit 2
fi

total=$(jq '.checks | length' "$EVAL_FILE")
passed=0
failed=0

for ((i = 0; i < total; i++)); do
  name=$(jq -r ".checks[$i].name" "$EVAL_FILE")
  command=$(jq -r ".checks[$i].run" "$EVAL_FILE")

  echo
  echo "==> Running: $name"
  # WARNING: Commands in evaluation JSON are executable shell code.
  # Only run evaluation files that are trusted and version-controlled.
  if bash -o pipefail -c "$command"; then
    echo "PASS: $name"
    passed=$((passed + 1))
  else
    status=$?
    echo "FAIL: $name (exit $status)"
    failed=$((failed + 1))
  fi
done

echo
echo "Result: $passed/$total checks passed; $failed failed."
test "$failed" -eq 0
