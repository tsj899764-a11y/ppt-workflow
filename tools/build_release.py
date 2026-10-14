#!/usr/bin/env python3
"""Build only explicitly public files. Never read the private knowledge library."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

FILES = (
    'README.md', 'LICENSE', '.gitignore',
    'skills/ppt-workflow/SKILL.md',
    'skills/ppt-workflow/agents/openai.yaml',
    'skills/ppt-workflow/scripts/kb_search.py',
    'skills/ppt-workflow/references/library.md',
    'skills/ppt-workflow/references/skeletons.md',
    'skills/ppt-workflow/references/design.md',
    'skills/ppt-workflow/references/lifecycle.md',
    'skills/ppt-workflow/assets/project_manifest.template.json',
    'skills/ppt-workflow/assets/demo-library/csv/page_index.csv',
    'skills/ppt-workflow/assets/demo-library/pages.jsonl',
    'tools/build_release.py', 'tests/test_tools.py',
)
RULES = {
    'personal_absolute_path': re.compile(r'(?:/Users/|/home/)[A-Za-z0-9_-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9_-]+\\'),
    'api_key_like': re.compile(r'sk-[A-Za-z0-9_-]{24,}'),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}


def build(root, target, deny_terms=()):
    root = Path(root).resolve()
    target = Path(target).resolve()
    payload = {}
    errors = []
    for relative in FILES:
        p = root / relative
        if not p.is_file() or any(x.is_symlink() for x in [p, *p.parents] if x.is_relative_to(root)):
            raise ValueError('白名单文件不存在或包含符号链接: ' + relative)
        if not p.resolve().is_relative_to(root):
            raise ValueError('白名单越界: ' + relative)
        content = p.read_bytes()
        text = content.decode('utf-8')
        for label, pattern in RULES.items():
            if pattern.search(text):
                errors.append({'file': relative, 'rule': label})
        for term in deny_terms:
            if term and term.casefold() in text.casefold():
                # Do not put private deny terms or matching passages in logs.
                errors.append({'file': relative, 'rule': 'user_private_term'})
        payload[relative] = content
    if errors:
        raise ValueError('发行检查未通过: ' + json.dumps(errors, ensure_ascii=False))
    if target.is_relative_to(root):
        raise ValueError('压缩包必须写在发行源目录之外')
    if target.exists():
        raise ValueError('目标包已存在，请选择新的版本名，避免覆盖交付')
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'version': '0.1.0', 'private_library_copied': False,
                'audit_scope': 'allowlist and text heuristics; not a full confidentiality certification',
                'files': [{'path': name, 'sha256': hashlib.sha256(content).hexdigest()} for name, content in payload.items()]}
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in payload.items():
            archive.writestr('ppt-workflow-v0.1.0/' + name, content)
        archive.writestr('ppt-workflow-v0.1.0/release_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return {'files': len(payload) + 1, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'text_checks': 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--deny-term', action='append', default=[])
    args = parser.parse_args()
    try:
        result = build(Path(__file__).resolve().parents[1], args.output, args.deny_term)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
