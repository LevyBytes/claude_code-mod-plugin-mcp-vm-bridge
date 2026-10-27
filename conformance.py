"""Run deterministic source and behavior checks. No VM mutation or model generation."""
import argparse
import json
from datetime import datetime, timezone

from bridge_runtime.paths import STATE
from tools.size_gate import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only', action='store_true', help='Only size/LF/syntax; not full conformance')
    args = parser.parse_args()
    source = run()
    print(json.dumps(source), flush=True)
    checks = []
    if not args.source_only and source['passed']:
        from tools.checkers import run_checks
        try:
            checks = run_checks()
        except (OSError, RuntimeError) as error:
            checks.append({'check': 'checker_availability', 'passed': False, 'error': str(error)})
    passed = source['passed'] and (args.source_only or bool(checks) and all(r['passed'] for r in checks))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt = {'passed': passed, 'source_only': args.source_only, 'source': source, 'checks': checks}
    path = STATE / 'checks' / (stamp + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': passed, 'receipt': str(path)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
