"""Validate the local retinal dataset manifest without loading image pixels."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'manifest.csv'
REQUIRED = {'image_path', 'label', 'split', 'source', 'notes'}
VALID_SPLITS = {'train', 'validation', 'val', 'test'}


def main():
    if not MANIFEST.exists():
        raise SystemExit(f'Missing manifest: {MANIFEST}')
    with MANIFEST.open(newline='', encoding='utf-8-sig') as handle:
        lines = (line for line in handle if not line.lstrip().startswith('#'))
        reader = csv.DictReader(lines)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f'Missing required columns: {", ".join(sorted(missing))}')
        rows = list(reader)
    errors = []
    seen = set()
    for number, row in enumerate(rows, start=2):
        path = (row.get('image_path') or '').strip()
        label = (row.get('label') or '').strip()
        split = (row.get('split') or '').strip().lower()
        if not path or not label or not split:
            errors.append(f'row {number}: image_path, label, and split are required')
            continue
        if path in seen:
            errors.append(f'row {number}: duplicate image_path {path!r}')
        seen.add(path)
        if split not in VALID_SPLITS:
            errors.append(f'row {number}: split must be one of {sorted(VALID_SPLITS)}')
        resolved = (ROOT / path).resolve()
        if ROOT.resolve() not in resolved.parents:
            errors.append(f'row {number}: image_path must remain inside dataset folder')
        elif not resolved.is_file():
            errors.append(f'row {number}: image file not found: {path}')
    if errors:
        print('\n'.join(f'ERROR: {e}' for e in errors))
        raise SystemExit(1)
    print(f'Manifest valid: {len(rows)} image row(s).')
    if not rows:
        print('No dataset images are included. Add licensed images and rows before training.')


if __name__ == '__main__':
    main()
