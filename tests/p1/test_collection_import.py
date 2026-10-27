"""取込時の旧証拠保護とSHA不一致の拒否を検査する。"""
import json
from pathlib import Path
import tempfile
import unittest

from p1.collection_import import file_sha256, import_public_export


class CollectionImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / 'source'
        self.destination = self.root / 'destination'
        self.source.mkdir()
        self.destination.mkdir()
        (self.source / 'test.txt').write_text('公開用に脱敏した記録\n')
        (self.source / 'public-sha256.json').write_text(json.dumps({'test.txt': file_sha256(self.source / 'test.txt')}))

    def test_conflict_preserves_original_and_indexes_alias(self):
        old = b'prior evidence\n'
        (self.destination / 'test.txt').write_bytes(old)
        index = import_public_export(self.source, self.destination)
        self.assertEqual((self.destination / 'test.txt').read_bytes(), old)
        self.assertTrue(index['files']['test.txt']['prior_name_conflict'])
        self.assertEqual(file_sha256(self.destination / index['files']['test.txt']['path']), index['files']['test.txt']['sha256'])

    def test_repeated_import_is_idempotent(self):
        first = import_public_export(self.source, self.destination)
        before = {p.name: p.read_bytes() for p in self.destination.iterdir()}
        self.assertEqual(import_public_export(self.source, self.destination), first)
        self.assertEqual({p.name: p.read_bytes() for p in self.destination.iterdir()}, before)

    def test_bad_source_hash_writes_no_evidence(self):
        (self.source / 'test.txt').write_text('変更された入力')
        with self.assertRaises(ValueError):
            import_public_export(self.source, self.destination)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_alias_conflict_is_rejected_before_writing(self):
        (self.destination / 'test.txt').write_text('元の証拠')
        (self.destination / 'server-final-export-v1-test.txt').write_text('別の証拠')
        before = {p.name: p.read_bytes() for p in self.destination.iterdir()}
        with self.assertRaises(ValueError):
            import_public_export(self.source, self.destination)
        self.assertEqual({p.name: p.read_bytes() for p in self.destination.iterdir()}, before)

    def test_parent_path_is_rejected(self):
        (self.source / 'public-sha256.json').write_text(json.dumps({'../outside.txt': '0' * 64}))
        with self.assertRaises(ValueError):
            import_public_export(self.source, self.destination)

    def test_unlisted_file_is_rejected(self):
        (self.source / 'unexpected.txt').write_text('未登録')
        with self.assertRaises(ValueError):
            import_public_export(self.source, self.destination)


if __name__ == '__main__':
    unittest.main()
