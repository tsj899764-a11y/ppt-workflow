#!/usr/bin/env python3
"""Read-only local index search. No networking, source opening, or library writes."""
import argparse
import csv
import json
import os
from pathlib import Path


def safe_child(base, relative):
    if not relative:
        return None
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        return None
    candidate = base / p
    if any(x.is_symlink() for x in [candidate, *candidate.parents] if x != base.parent):
        return None
    resolved = candidate.resolve()
    return resolved if resolved.is_relative_to(base) else None


def search(base, query='', limit=5, business='', page_type='', doc_id='', include_text=False):
    base = Path(base).expanduser().resolve()
    index = safe_child(base, 'csv/page_index.csv')
    if index is None or not index.is_file():
        raise ValueError('指定目录缺少安全可读的csv/page_index.csv')
    words = query.casefold().split()
    selected = []
    with index.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'page_id', 'doc_id', 'content_topic', 'reuse_level', 'eligible_for_generation'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('页面索引缺少必要字段')
        for row in reader:
            if row['reuse_level'] not in ('A', 'B') or row['eligible_for_generation'].lower() not in ('true', '1', 'yes'):
                continue
            if row.get('document_status') in ('superseded', 'source_changed_pending'):
                continue
            if business and business not in row.get('business_tags', '').split('|'):
                continue
            if page_type and page_type != row.get('page_type'):
                continue
            if doc_id and doc_id != row['doc_id']:
                continue
            haystack = ' '.join(row.get(x, '') for x in ('content_topic', 'content_summary', 'business_tags', 'business_labels')).casefold()
            score = sum(haystack.count(word) for word in words)
            if words and not score:
                continue
            selected.append((score, row))
    selected.sort(key=lambda x: (-x[0], x[1]['page_id']))
    seen = set()
    results = []
    for score, row in selected:
        key = row.get('canonical_page_id') or row['page_id']
        if key in seen:
            continue
        seen.add(key)
        item = {k: row.get(k, '') for k in ('page_id', 'doc_id', 'page_no', 'content_topic', 'page_type', 'layout_type', 'reuse_level', 'fact_status', 'source_kind', 'source_file', 'source_path', 'reuse_notes', 'derived_from_page_ids')}
        item['canonical_page_id'] = key
        preview = safe_child(base, row.get('preview_path', ''))
        item['preview_path'] = str(preview) if preview and preview.is_file() else ''
        item['score'] = score
        results.append(item)
        if len(results) >= limit:
            break
    if include_text and results:
        full = safe_child(base, 'pages.jsonl')
        if full and full.is_file():
            wanted = {r['page_id']: r for r in results}
            with full.open(encoding='utf-8') as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    page = json.loads(line)
                    if page.get('page_id') in wanted:
                        row = wanted.pop(page['page_id'])
                        row['text'] = {k: str(page.get(k, ''))[:6000] for k in ('full_text', 'speaker_notes', 'visual_text')}
                        row['text_truncated'] = any(len(str(page.get(k, ''))) > 6000 for k in row['text'])
                    if not wanted:
                        break
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--kb', default=os.environ.get('PPT_KB_ROOT'))
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--business', default='')
    parser.add_argument('--page-type', default='')
    parser.add_argument('--doc-id', default='')
    parser.add_argument('--include-text', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error('--limit必须为1至20')
    demo = Path(__file__).resolve().parents[1] / 'assets/demo-library'
    base = Path(args.kb).expanduser().resolve() if args.kb else demo
    try:
        results = search(base, args.query, args.limit, args.business, args.page_type, args.doc_id, args.include_text)
    except (OSError, ValueError) as exc:
        parser.exit(1, '检索失败：' + str(exc) + '\n')
    print(json.dumps({'library_mode': 'fictional_demo' if base == demo else 'user_private_library',
                      'fictional_demo': base == demo, 'results': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
