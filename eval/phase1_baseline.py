"""Reproduce the fixture baseline without modifying published evaluation results.

Usage: python eval/phase1_baseline.py --out eval/phase1-output
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command):
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {"command": command, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='eval/phase1-output')
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tests = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'])
    fixtures = run([sys.executable, 'eval/evaluate_fixtures.py', '--out', str(out / 'fixtures')])
    summary_file = out / 'fixtures' / 'fixtures.json'
    summary = json.loads(summary_file.read_text()) if summary_file.exists() else None
    manifest = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source': 'local source archive, not an independently acquired attack corpus',
        'python': sys.version, 'platform': platform.platform(),
        'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / 'tests/fixtures').rglob('*')) if p.is_file()},
        'code_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / 'xrlint').rglob('*.py'))},
        'tests': tests, 'fixture_evaluation': fixtures,
        'fixture_summary': summary,
        'external_artifact_evaluated': False,
        'independent_real_world_detection_validated': False,
    }
    (out / 'baseline-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print('Tests:', tests['exit_code'], 'Fixture evaluation:', fixtures['exit_code'])
    print('Manifest:', out / 'baseline-manifest.json')
    return 0 if tests['exit_code'] == fixtures['exit_code'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
