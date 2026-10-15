"""Meaningful local tests using only fictional fixtures and isolated temporary files."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


search = module('search_tool', ROOT / 'skills/ppt-workflow/scripts/kb_search.py')
release = module('release_tool', ROOT / 'tools/build_release.py')


class ToolTests(unittest.TestCase):
    def test_demo_search_and_text(self):
        rows = search.search(ROOT / 'skills/ppt-workflow/assets/demo-library', '运营', include_text=True)
        self.assertEqual([r['page_id'] for r in rows], ['DEMO001_P002'])
        self.assertEqual(rows[0]['fact_status'], 'fictional_demo')
        self.assertIn('没有', search.search(ROOT / 'skills/ppt-workflow/assets/demo-library', '任务', include_text=True)[0]['text']['speaker_notes'])
        self.assertEqual(search.search(ROOT / 'skills/ppt-workflow/assets/demo-library', '不存在的主题'), [])

    def test_filter_dedupe_and_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'csv').mkdir()
            keys = ['page_id', 'doc_id', 'content_topic', 'reuse_level', 'eligible_for_generation', 'canonical_page_id', 'preview_path', 'fact_status']
            rows = [dict(zip(keys, values)) for values in [
                ['X1', 'X', '任务', 'A', 'true', 'X1', '../outside.png', 'generated_unverified'],
                ['X2', 'X', '任务', 'B', 'true', 'X1', '', 'generated_unverified'],
                ['X3', 'X', '任务', 'C', 'true', 'X3', '', 'generated_unverified'],
                ['X4', 'X', '任务', 'A', 'false', 'X4', '', 'generated_unverified'],
            ]]
            p = root / 'csv/page_index.csv'
            with p.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, keys)
                writer.writeheader()
                writer.writerows(rows)
            before = p.read_bytes()
            result = search.search(root, '任务')
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['preview_path'], '')
            self.assertEqual(result[0]['fact_status'], 'generated_unverified')
            self.assertEqual(p.read_bytes(), before)
            self.assertEqual(search.search(root, '任务', doc_id='NOT-X'), [])
            (root / 'escape').symlink_to(ROOT, target_is_directory=True)
            self.assertIsNone(search.safe_child(root, 'escape/README.md'))

    def test_skeleton_budget_integrity(self):
        folder = ROOT / 'skills/ppt-workflow/assets/skeleton-library'
        with (folder / 'skeletons.csv').open(encoding='utf-8-sig') as stream:
            skeletons = list(csv.DictReader(stream))
        with (folder / 'skeleton_steps.csv').open(encoding='utf-8-sig') as stream:
            steps = list(csv.DictReader(stream))
        self.assertEqual({s['skeleton_id'] for s in skeletons}, {f'S{i:03}' for i in range(1, 11)})
        self.assertFalse(any('reference_page_ids' in s for s in steps))
        for skeleton in skeletons:
            sequence = [s for s in steps if s['skeleton_id'] == skeleton['skeleton_id']]
            self.assertEqual(sum(int(s['page_budget']) for s in sequence), int(skeleton['default_page_count']))
            position = 1
            for step in sequence:
                self.assertEqual(int(step['suggested_page_start']), position)
                position += int(step['page_budget'])
                self.assertEqual(int(step['suggested_page_end']), position - 1)

    def test_release_whitelist(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'release.zip'
            result = release.build(ROOT, target)
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(release.FILES) + 1)
                manifest = json.loads(archive.read('ppt-workflow-v0.2.3/release_manifest.json'))
                self.assertFalse(manifest['private_library_copied'])
                guide = 'skills/ppt-workflow/references/AI建库与Skill绑定执行说明_V1.1.md'
                self.assertIn('ppt-workflow-v0.2.3/' + guide, names)
                self.assertEqual(archive.read('ppt-workflow-v0.2.3/' + guide), (ROOT / guide).read_bytes())
                self.assertEqual(result['files'], len(names))
                self.assertFalse(any(n.endswith(('.pptx', '.pdf', '.xlsx', '.png')) for n in names))
            with self.assertRaises(ValueError):
                release.build(ROOT, Path(folder) / 'denied.zip', ['PPT Workflow'])
            with self.assertRaises(ValueError):
                release.build(ROOT, target)


if __name__ == '__main__':
    unittest.main()
