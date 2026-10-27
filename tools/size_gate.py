"""Hard physical-line, column, encoding and syntax limits for maintained source."""
import ast
import json
import tomllib

from .files import CODE, ROOT, source_files


def check_file(path):
    errors = []
    raw = path.read_bytes()
    if b'\x00' in raw:
        binary = {'.png', '.jpg', '.jpeg', '.ico', '.webp'}
        return errors if path.suffix in binary else ['NUL in maintained text']
    if b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
        errors.append('LF UTF-8 without BOM required')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return ['UTF-8 required']
    if text and not text.endswith('\n'):
        errors.append('Missing final LF')
    lines = text.splitlines()
    if path.suffix in CODE:
        if len(lines) > 100:
            errors.append(f'{len(lines)} physical source lines > 100')
        for number, line in enumerate(lines, 1):
            if len(line) > 120:
                errors.append(f'line {number}: {len(line)} columns > 120')
    try:
        if path.suffix == '.py':
            ast.parse(text, filename=str(path))
        elif path.suffix == '.json':
            json.loads(text)
        elif path.suffix == '.toml':
            tomllib.loads(text)
    except (SyntaxError, ValueError) as error:
        errors.append(str(error))
    return errors


def run():
    try:
        files = list(source_files())
    except ValueError as error:
        return {'checked_files': 0, 'errors': [str(error)], 'passed': False}
    errors = []
    for path in files:
        errors += [f'{path.relative_to(ROOT)}: {e}' for e in check_file(path)]
    return {'checked_files': len(files), 'errors': errors, 'passed': not errors}
