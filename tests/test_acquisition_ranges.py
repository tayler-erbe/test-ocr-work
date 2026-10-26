from contextlib import closing
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from resume_large_downloads import segment

class Response(io.BytesIO):
    def __init__(self,data,status,content_range):
        super().__init__(data);self.status=status;self.headers={'Content-Range':content_range}

class RangeIntegrity(unittest.TestCase):
    def test_resume_appends_exact_missing_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'chunk.part';path.write_bytes(b'ab')
            with patch('resume_large_downloads.request_range',return_value=closing(Response(b'cd',206,'bytes 2-3/4'))) as request:
                segment({'url':'https://example.invalid'},0,3,path)
            self.assertEqual(path.read_bytes(),b'abcd')
            request.assert_called_once_with({'url':'https://example.invalid'},2,3)

    def test_ignored_range_cannot_corrupt_a_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'chunk.part'
            def response(*args):return closing(Response(b'abcdef',200,''))
            with patch('resume_large_downloads.request_range',side_effect=response),patch('resume_large_downloads.time.sleep'):
                with self.assertRaises(ValueError):segment({},2,3,path)
            self.assertFalse(path.exists())

if __name__=='__main__':unittest.main()
