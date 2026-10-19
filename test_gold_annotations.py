import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from document_lab import connect, put_doc
from gold_annotations import initialize, validate

class GoldLabels(unittest.TestCase):
    def test_blank_labels_are_not_scored_as_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);db=connect(root);put_doc(db,'private','synthetic','Synthetic','synthetic text');db.commit();db.close()
            path=root/'gold.csv'
            with patch('builtins.print'):
                initialize(root,path);result=validate(root,path)
            self.assertFalse(result['ready_for_private_scoring'])
            self.assertEqual(result['scoring_ready_rows'],0)
            with self.assertRaises(ValueError):initialize(root,path)

if __name__=='__main__':unittest.main()
