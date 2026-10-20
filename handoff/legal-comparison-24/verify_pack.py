"""Provider-free integrity check; never sends inputs or references to a model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    checksums = json.loads((ROOT / 'SHA256.json').read_text(encoding='utf8'))
    expected = {'requests.json', 'references.DO_NOT_SEND_TO_MODEL.json', 'frozen_evaluation_v3.py', 'document_lab.py', 'README.md', 'verify_pack.py'}
    assert set(checksums) == expected, 'Unexpected pack file list'
    for name, expected_hash in checksums.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash, name + ': checksum mismatch'
    requests = json.loads((ROOT / 'requests.json').read_text(encoding='utf8'))
    references = json.loads((ROOT / 'references.DO_NOT_SEND_TO_MODEL.json').read_text(encoding='utf8'))
    assert len(requests) == len(references) == 24
    assert len({r['case_id'] for r in requests}) == 24
    assert [r['case_id'] for r in requests] == [r['case']['id'] for r in references]
    assert Counter(r['case']['dataset'] for r in references) == {'cuad': 12, 'contractnli': 12}
    for request, reference in zip(requests, references):
        assert set(reference) == {'case', 'visible'}, 'Model output or unexpected reference field'
        assert request['temperature'] == 0 and request['max_tokens'] == 2000 and request['enable_thinking'] is False
        hashed = json.dumps({'messages': request['messages'], 'schema': request['schema']}, sort_keys=True)
        assert hashlib.sha256(hashed.encode()).hexdigest() == request['request_sha256']
        assert request['task'] == reference['case']['task']
        assert 'gold' not in request and 'prediction' not in request and 'raw' not in request
        properties = request['schema']['properties']
        array = properties['matches'] if request['task'] == 'extraction' else properties['ids']
        assert array.get('minItems', 0) == 0, 'Empty evidence prohibited'
    assert hashlib.sha256((ROOT / 'frozen_evaluation_v3.py').read_bytes()).hexdigest() == '43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f'
    spec = importlib.util.spec_from_file_location('legal_frozen_scorer', ROOT / 'frozen_evaluation_v3.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    assert scorer.validate_response({'matches': []}, [], 'extraction') == []
    assert scorer.validate_response({'label': 'NotMentioned', 'ids': []}, [], 'nli') == []
    print('INPUT PACK VERIFIED: 24 public cases, unchanged scorer, no saved model responses')


if __name__ == '__main__':
    main()
