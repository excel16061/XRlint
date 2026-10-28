#!/usr/bin/env bash
# Re-run the tests and every evaluation in the README.
# Usage: bash scripts/run_all.sh   (run scripts/fetch_corpora.sh first)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

$PY -m unittest discover -s tests
$PY eval/evaluate_fixtures.py --out eval/results > /dev/null && echo "fixtures -> eval/results/fixtures.md"

C=data/corpora
$PY eval/scan_corpus.py $C/aframe/examples --name aframe_examples --out eval/results \
  --source-note "aframevr/aframe @ 022bcc5 2026-07-13, examples/" > /dev/null
for n in a-painter moonrider superframe aframe-extras; do
  $PY eval/scan_corpus.py $C/$n --name $n --out eval/results/heldout \
    --source-note "$(git -C $C/$n remote get-url origin | sed 's|https://github.com/||;s|\.git$||') @ $(git -C $C/$n log -1 --format='%h %cs')" > /dev/null
done
echo "corpora -> eval/results/aframe_examples.json, eval/results/heldout/"

if [ -d data/shadowed_realities ]; then
  $PY eval/evaluate_artifact.py data/shadowed_realities
else
  echo "Shadowed Realities artifact not found in data/shadowed_realities (see README)."
fi
