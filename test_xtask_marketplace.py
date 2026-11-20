# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('marketplace_build', Path(__file__).with_name('xtask-marketplace.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MarketplaceTests(unittest.TestCase):
    def insight_package(self):
        folder = self.root / 'packages/insights/author/sessions/1.0.0'
        folder.mkdir(parents=True)
        meta = {'id':'sessions','publisher':'author','version':'1.0.0','title':'Review sessions','description':'Valuable records, not disposable cache'}
        entry = {'schema':1,'kind':'insight-pack','publisher':'author','metadata':meta,'platforms':[],
                 'requires':[builder.INSIGHT_CAPABILITY],'path':'packages/insights/author/sessions/1.0.0/pack.json'}
        document = {'schema':1,'kind':'insight-pack','metadata':meta,'platforms':[],'requires':[builder.INSIGHT_CAPABILITY],
                    'insights':[{'id':'session-history','title':'Review history','detail':'Keep valuable conversations.','subject':'directory','location':{'base':'home','path':'.assistant/sessions'},'action':'review-only'}]}
        (folder/'manifest.json').write_bytes(builder.encode(entry))
        (folder/'pack.json').write_bytes(builder.encode(document))
        return folder, entry, document

    def test_insight_contract_generates_a_distinct_bounded_index(self):
        folder, entry, document = self.insight_package()
        result = builder.generated(self.root)
        record = json.loads(result['indexes/insights.jsonl'])
        self.assertEqual(record['kind'],'insight-pack')
        self.assertEqual(record['requires'],[builder.INSIGHT_CAPABILITY])
        self.assertEqual(record['sha256'],hashlib.sha256((folder/'pack.json').read_bytes()).hexdigest())

    def test_insight_contract_refuses_destructive_or_executable_fields(self):
        folder, entry, document = self.insight_package()
        import copy
        for key, value in [('action','trash'),('command','run something'),('under-home','../outside'),('under-home','C:/Windows'),('under-home','.')]:
            bad = copy.deepcopy(document)
            bad['insights'][0][key] = value
            (folder/'pack.json').write_bytes(builder.encode(bad))
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                builder.generated(self.root)
        document['platforms'] = ['windows']
        (folder/'pack.json').write_bytes(builder.encode(document))
        with self.assertRaisesRegex(ValueError,'disagree'):
            builder.generated(self.root)

    def test_shared_location_corpus(self):
        source = Path(__file__).parent / "crates/kosha-analyze/tests/fixtures/location_cases.jsonl"
        if not source.exists():
            source = Path(__file__).parent / "tests/fixtures/location_cases.jsonl"
        for line, text in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            case = json.loads(text)
            with self.subTest(line=line):
                if case["valid"]:
                    self.assertEqual(builder.validate_location(case["location"]), case["normalized"])
                else:
                    with self.assertRaises(ValueError):
                        builder.validate_location(case["location"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # /var is a symlink on macOS; use the canonical fixture root so the
        # path-safety guard still rejects actual links inside the marketplace.
        self.root = Path(self.temp.name).resolve()

    def package(self, publisher='author', name='tools', version='1.0.0', kind='recipe-pack', listed=True):
        group = builder.KINDS.get(kind, kind)
        prefix = f'packages/{group}/{publisher}/{name}/{version}/'
        folder = self.root / prefix
        folder.mkdir(parents=True)
        meta = {'id': name, 'publisher': publisher, 'version': version, 'title': 'Tools', 'description': 'Test artifacts'}
        artifact = 'pack.json' if kind == 'recipe-pack' else 'module.wasm'
        requires = ['recipe.exact'] if kind == 'recipe-pack' else ['plugin.wasi']
        content = builder.encode({'schema': 1, 'kind': kind, 'metadata': meta, 'requires': requires,
                                  'recipes': [{'phrase': 'tool files', 'dsl': 'file'}]}) if kind == 'recipe-pack' else b'\0asm'
        (folder / artifact).write_bytes(content)
        manifest = {'schema': 1, 'kind': kind, 'publisher': publisher, 'metadata': meta,
                    'platforms': [], 'requires': requires, 'path': prefix + artifact, 'listed': listed}
        path = folder / 'manifest.json'
        path.write_bytes(builder.encode(manifest))
        return path, manifest

    def test_indexes_are_deterministic_and_digest_exact_artifact_bytes(self):
        self.package(publisher='zeta')
        self.package(publisher='alpha')
        result = builder.generated(self.root)
        self.assertEqual(result, builder.generated(self.root))
        catalog = json.loads(result['catalog.json'])
        self.assertEqual(catalog['schema'], 1)
        index = catalog['indexes'][0]
        data = result[index['path']]
        self.assertEqual(index['bytes'], len(data))
        self.assertEqual(index['sha256'], hashlib.sha256(data).hexdigest())
        entries = [json.loads(line) for line in data.splitlines()]
        self.assertEqual([e['publisher'] for e in entries], ['alpha', 'zeta'])
        for entry in entries:
            artifact = (self.root / entry['path']).read_bytes()
            self.assertEqual(entry['bytes'], len(artifact))
            self.assertEqual(entry['sha256'], hashlib.sha256(artifact).hexdigest())

    def test_shards_respect_bounds_without_dropping_records(self):
        for name in ['one', 'two', 'three']:
            self.package(name=name)
        with patch.object(builder, 'MAX_SHARD', 900):
            result = builder.generated(self.root)
        indexes = json.loads(result['catalog.json'])['indexes']
        self.assertGreater(len(indexes), 1)
        self.assertEqual(sum(i['entries'] for i in indexes), 3)
        self.assertTrue(all(i['bytes'] <= 900 for i in indexes))

    def test_package_kind_separation_and_unlisted_versions(self):
        self.package()
        self.package(version='0.9.0', listed=False)
        self.package(name='extension', kind='plugin')
        self.package(name='palette', kind='theme')
        result = builder.generated(self.root)
        kinds = {i['kind'] for i in json.loads(result['catalog.json'])['indexes']}
        self.assertEqual(kinds, {'recipe-pack', 'plugin', 'theme'})
        entries = [json.loads(line) for line in result['indexes/recipes.jsonl'].splitlines()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['metadata']['version'], '1.0.0')

    def test_duplicate_listed_identity_fails(self):
        self.package()
        self.package(version='1.1.0')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            builder.generated(self.root)

    def test_build_metadata_version_is_one_safe_directory_component(self):
        self.package(version='1.0.0+build.7')
        result = builder.generated(self.root)
        entry = json.loads(result['indexes/recipes.jsonl'])
        self.assertIn('/1.0.0+build.7/', entry['path'])
        for version in ['1/2', '../1', '1%2f2', '-1', '1 build']:
            with self.assertRaises(ValueError):
                builder.metadata({'id': 'tools', 'publisher': 'author', 'title': 'Tools',
                                  'description': 'Test', 'version': version})

    def test_total_budget_includes_the_root_descriptor(self):
        self.package()
        result = builder.generated(self.root)
        index_bytes = len(result['indexes/recipes.jsonl'])
        with patch.object(builder, 'MAX_TOTAL', index_bytes):
            with self.assertRaisesRegex(ValueError, 'Root and indexes'):
                builder.generated(self.root)

    def test_mismatched_metadata_and_capabilities_fail(self):
        path, manifest = self.package()
        artifact = self.root / manifest['path']
        document = json.loads(artifact.read_bytes())
        for field, value in [('metadata', dict(document['metadata'], title='Other')), ('requires', ['recipe.regex'])]:
            broken = dict(document, **{field: value})
            artifact.write_bytes(builder.encode(broken))
            with self.assertRaisesRegex(ValueError, 'disagree'):
                builder.generated(self.root)

    def test_traversal_and_encoded_paths_fail(self):
        path, manifest = self.package()
        for name in ['../escape', '/absolute', 'packages/%2e%2e/secret', manifest['path'] + '/../escape', 'C:/escape']:
            path.write_bytes(builder.encode(dict(manifest, path=name)))
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.generated(self.root)

    def test_links_inside_the_marketplace_are_still_refused(self):
        with patch.object(Path, 'is_symlink', autospec=True,
                          side_effect=lambda path: path == self.root / 'indexes'):
            with self.assertRaisesRegex(ValueError, 'traverse links'):
                builder.safe(self.root, 'indexes/recipes.jsonl')

    def test_check_is_read_only_and_refuses_stale_indexes(self):
        self.package()
        args = ['xtask-marketplace.py', '--root', str(self.root), '--check']
        with patch.object(builder.sys, 'argv', args), redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 1)
        self.assertFalse((self.root / 'indexes').exists())
        for name, data in builder.generated(self.root).items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        with patch.object(builder.sys, 'argv', args), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 0)
        (self.root / 'indexes/recipes.jsonl').write_bytes(b'stale\n')
        with patch.object(builder.sys, 'argv', args), redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 1)
        self.assertEqual((self.root / 'indexes/recipes.jsonl').read_bytes(), b'stale\n')

    def test_writer_maintains_only_indexed_layout_without_rewriting_packages(self):
        manifest, entry = self.package()
        artifact = self.root / entry['path']
        original = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in (manifest, artifact)}
        args = ['xtask-marketplace.py', '--root', str(self.root)]
        with patch.object(builder.sys, 'argv', args), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 0)
        paths = {p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(paths, set(original) | {'catalog.json', 'indexes/recipes.jsonl'})
        self.assertNotIn('packages', json.loads((self.root / 'catalog.json').read_bytes()))
        self.assertTrue(json.loads((self.root / 'catalog.json').read_bytes())['indexes'])
        for name, data in original.items():
            self.assertEqual((self.root / name).read_bytes(), data)

    def test_corpus_records_are_validated_and_do_not_enter_client_indexes(self):
        path, manifest = self.package()
        cases = path.parent / 'cases.jsonl'
        manifest['cases'] = cases.relative_to(self.root).as_posix()
        path.write_bytes(builder.encode(manifest))
        cases.write_text('{"input":"tools","dsl":"file"}\n{"input":"unclear","error":true}\n', encoding='utf-8')
        result = builder.generated(self.root)
        self.assertNotIn('cases', json.loads(result['indexes/recipes.jsonl'].splitlines()[0]))
        for text in ['\n', '{"input":"tools"}\n', '{"input":"tools","error":false}\n', '{"input":"tools","error":true,"dsl":"file"}\n']:
            cases.write_text(text, encoding='utf-8')
            with self.subTest(text=text), self.assertRaises(ValueError):
                builder.generated(self.root)


if __name__ == '__main__':
    unittest.main()
