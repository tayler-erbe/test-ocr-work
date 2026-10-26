"""Provider-free project gates. No inference, private files or external services."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'benchmarks/harness'


def privacy_check():
    # Assemble denied historical identifiers so the gate itself contains none.
    denied = [r'\b' + 'ua' + 'fr' + r'\b', r'\b' + 'uf' + 'ar' + r'\b',
              'urba' + 'icompute', 'urbadvan' + 'alytics', 'uill' + 'inois.edu',
              'pram' + 'od', 'terbe' + '2022']
    pattern = re.compile('|'.join(denied), re.I)
    extensions = {'.md', '.py', '.json', '.jsonl', '.html', '.js', '.css', '.toml', '.yml', '.yaml', '.txt', '.ps1', '.cmd', '.ics'}
    failures = []
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(p in ('.git', '__pycache__', '.venv', 'node_modules') for p in path.relative_to(ROOT).parts):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if pattern.search(relative) or 'laptop-integration-2026' in relative or 'unread-page-ocr-diagnostics' in relative:
            failures.append(relative + ': excluded path')
        if path.suffix.lower() in extensions:
            with path.open(encoding='utf8', errors='replace') as stream:
                for line in stream:
                    if pattern.search(line):
                        failures.append(relative + ': historical identity')
                        break
    dashboard = json.loads((ROOT / 'site/data/benchmark.json').read_text())
    if 'evidence_fields' in dashboard:
        failures.append('dashboard: excluded pilot-derived field data')
    if failures:
        raise SystemExit('PRIVACY CHECK FAILED\n' + '\n'.join(failures))
    print('PASS current-tree privacy boundaries', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', action='store_true')
    parser.add_argument('--privacy-only', action='store_true')
    args = parser.parse_args()
    privacy_check()
    if args.privacy_only:
        return
    for path in [ROOT / 'src', HARNESS, HARNESS / 'tools']:
        sys.path.insert(0, str(path))
    tests = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    tests.addTests(unittest.defaultTestLoader.discover(str(HARNESS / 'tools'), pattern='test_nemotron_reassessment.py', top_level_dir=str(HARNESS / 'tools')))
    if not unittest.TextTestRunner(verbosity=1).run(tests).wasSuccessful():
        raise SystemExit(1)
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT / 'src'), str(HARNESS), env.get('PYTHONPATH', '')])
    commands = [[str(HARNESS / 'quality_check.py'), '--policy-only'],
                [str(HARNESS / 'tools/check_conformance.py'), '--root', str(ROOT / 'data/public')],
                [str(HARNESS / 'tools/check_conformance.py'), '--root', str(ROOT / 'data/public'), '--round2', '--results', str(ROOT / 'results/vision/exports/laptop.jsonl')],
                [str(HARNESS / 'handoff/legal-comparison-24/verify_pack.py')]]
    if args.data:
        commands[1].append('--data')
        commands[2].append('--data')
    for command in commands:
        subprocess.run([sys.executable, '-X', 'utf8', *command], cwd=HARNESS, env=env, check=True)
    print('PROJECT CHECKS PASSED', flush=True)


if __name__ == '__main__':
    main()
