import copy
import json
from pathlib import Path
import tempfile
import unittest
from datasets import DIST, import_snapshot, import_batch, read_snapshots, validate

class DatasetTests(unittest.TestCase):
    def test_batch_validates_before_writing_and_is_idempotent(self):
        batch=json.loads((DIST.parent/'imports/historical-batch.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dist=root/'dist';dist.mkdir();file=root/'batch.json'
            broken=copy.deepcopy(batch);broken['datasets'][-1]['schools'][0]['rankings']['oto']['rank']=0
            file.write_text(json.dumps(broken),encoding='utf-8')
            with self.assertRaises(ValueError):import_batch(file,dist=dist)
            self.assertFalse((dist/'data').exists())
            file.write_text(json.dumps(batch),encoding='utf-8');import_batch(file,dist=dist)
            before=(dist/'data.js').read_bytes();import_batch(file,dist=dist)
            self.assertEqual(before,(dist/'data.js').read_bytes())
            self.assertEqual(len(read_snapshots(dist/'data')),9)
            batch['datasets'][-1]['schools'][0]['rankings']['oto']['rank']=99
            file.write_text(json.dumps(batch),encoding='utf-8')
            with self.assertRaises(ValueError):import_batch(file,dist=dist)
            self.assertEqual(before,(dist/'data.js').read_bytes())
    def setUp(self):
        self.original=json.loads((DIST/'data/rankings-2026.json').read_text(encoding='utf-8'))

    def test_preserved_snapshot(self):
        validate(self.original)
        self.assertEqual(len(self.original['schools']),72)
        self.assertEqual(self.original['updated'],'2026-10-04')
        self.assertEqual(self.original['rankingYear'],2026)
        self.assertTrue(all(s['examYear']==2025 for s in self.original['schools']))

    def test_import_preserves_old_year_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dist=root/'dist';dist.mkdir()
            first=root/'first.json';first.write_text(json.dumps(self.original),encoding='utf-8')
            import_snapshot(first,dist=dist)
            before=(dist/'data/rankings-2026.json').read_bytes()
            next_data=copy.deepcopy(self.original)
            next_data.update(rankingYear=2027,examYear=2026,updated='2027-01-10')
            for s in next_data['schools']:s['examYear']=2026
            later=root/'later.json';later.write_text(json.dumps(next_data),encoding='utf-8')
            import_snapshot(later,dist=dist)
            self.assertEqual(before,(dist/'data/rankings-2026.json').read_bytes())
            self.assertEqual(set(read_snapshots(dist/'data')),{'2026','2027'})
            self.assertEqual(json.loads((dist/'data/index.json').read_text())['defaultYear'],2027)
            with self.assertRaises(ValueError):import_snapshot(later,dist=dist)
            next_data['schools'][0]['rankings']['oto']['math']=101
            later.write_text(json.dumps(next_data),encoding='utf-8')
            bundle_before=(dist/'data.js').read_bytes()
            with self.assertRaises(ValueError):import_snapshot(later,replace=True,dist=dist)
            self.assertEqual(bundle_before,(dist/'data.js').read_bytes())

    def test_bad_identity_coordinates_year_and_percent(self):
        mutations=[lambda d:d['schools'].append(copy.deepcopy(d['schools'][0])),
                   lambda d:d['schools'][0].update(coords=[0,0]),
                   lambda d:d.update(rankingYear='2027'),
                   lambda d:d['schools'][0].update(examYear=2024),
                   lambda d:d['schools'][0]['rankings']['oto'].update(score=float('nan'))]
        for change in mutations:
            data=copy.deepcopy(self.original);change(data)
            with self.assertRaises(ValueError):validate(data)

if __name__=='__main__':unittest.main()
