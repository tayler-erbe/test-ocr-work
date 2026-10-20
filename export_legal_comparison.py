"""Export the exact 24 already-exposed public diagnostic requests, without model calls."""
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

from document_lab import DEFAULT_ROOT, connect, digest
from nim_evaluation import frozen


def main():
    protocol = frozen()
    events = DEFAULT_ROOT / 'reports/nim-audit/events.jsonl'
    rows = [json.loads(line) for line in events.read_text(encoding='utf8').splitlines()]
    original = [r for r in rows if r['arm'] == 'original_2000']
    if len(original) != 24 or len({r['case_id'] for r in original}) != 24:
        raise ValueError('Expected exactly 24 unique original diagnostic cases')
    db = connect(DEFAULT_ROOT)
    requests, references = [], []

    class Capture:
        Request = __import__('urllib.request', fromlist=['Request']).Request
        def urlopen(self, request, timeout=None):
            self.payload = json.loads(request.data)
            raise RuntimeError('capture-only')

    capture = Capture()
    protocol.urllib = SimpleNamespace(request=capture)
    for row in original:
        case = dict(db.execute('SELECT * FROM cases WHERE id=?', (row['case_id'],)).fetchone())
        if case['dataset'] not in ['cuad', 'contractnli']:
            raise ValueError('Public cases only')
        try:
            protocol.ollama('MODEL_PLACEHOLDER', case['question'], row['visible'], case['task'])
        except RuntimeError as exc:
            if str(exc) != 'capture-only':
                raise
        payload = capture.payload
        requests.append({'case_id': case['id'], 'task': case['task'], 'messages': payload['messages'],
                         'schema': payload['format'], 'temperature': 0, 'max_tokens': 2000,
                         'enable_thinking': False, 'request_sha256': digest(json.dumps({'messages': payload['messages'], 'schema': payload['format']}, sort_keys=True))})
        references.append({'case': case, 'visible': row['visible'], 'nemotron_original_2000': {
            k: row[k] for k in ['status', 'metrics', 'raw'] if k in row}})
    db.close()
    directory = Path.home() / 'Downloads/legal-comparison-24'
    directory.mkdir(exist_ok=True)
    (directory / 'requests.json').write_text(json.dumps(requests, indent=2), encoding='utf8')
    (directory / 'references.DO_NOT_SEND_TO_MODEL.json').write_text(json.dumps(references, indent=2), encoding='utf8')
    for source, target in [('protocols/evaluation_v3.py', 'frozen_evaluation_v3.py'), ('document_lab.py', 'document_lab.py')]:
        (directory / target).write_bytes((Path(__file__).parent / source).read_bytes())
    instructions = '''# Desktop legal-text comparison: 24 exposed public cases

This is separate from vision-v1. Do not modify the OCR handoff, manifests, contract, or merge.
Use local Qwen3-32B and the available Qwen3-VL model; record exact model IDs, weights/digests, quantization and server versions. No model downloads or inference were performed by this exporter.

requests.json contains exact messages and JSON schemas reconstructed by the checksum-pinned original request builder. Send ONLY messages/schema to each model, never references. Keep case order, temperature 0, reasoning disabled, output budget 2000, and the supplied retrieved context unchanged for the first matched comparison. Map schema to Ollama format or OpenAI response_format.json_schema; record transport differences. Also retain observed reasoning and truncation rather than assuming the switch worked.

The model-placeholder and transport options are not part of the request hash. request_sha256 hashes json.dumps({messages, schema}, sort_keys=True) with default Python JSON settings. References contain the same public contexts, published gold, and Nemotron final responses. They are for code scoring only. Raw responses and per-case results stay local.

Import frozen_evaluation_v3.py, call validate_response(prediction, reference["visible"], reference["case"]["task"]), then score(reference["case"], prediction, evidence, visible). Failed and truncated requests count as incorrect/zero F1. Retain failed final answers separately for diagnosis. Do not call the frozen evaluate() function: it would select a different case set or use the old 600-token defaults.

Keep strict correctness and evidence F1 unchanged. Add graded metrics separately: per-reference-answer recovery, field presence/absence accuracy, partial literal validity and NLI confusion matrix. Distinguish raw-content recovery from accepted citation-bound evidence; code copying guarantees text fidelity, not semantic relevance.

Report all 24 cases, not just successful ones, grouped by 12 CUAD and 12 NLI; compare paired outcomes against the supplied Nemotron run. This small, reused diagnostic is not a fresh holdout, significance claim, or model-family verdict. Full-document context, reasoning-on/16000 tokens and ID-only extraction are NEW labelled configurations; never mix their results into the matched baseline. Full documents are not included in this pack. Review actual token counts and output reserve before sending them.

Source scorer SHA256 must equal 43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f. Dependencies for the supplied scorer's imports are Python standard library; rank-bm25 is needed only if recomputing retrieval, which this comparison must not do.
'''
    (directory / 'README.md').write_text(instructions, encoding='utf8')
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.name != 'SHA256.json')
    (directory / 'SHA256.json').write_text(json.dumps({p.name: digest(p.read_bytes()) for p in files}, indent=2), encoding='utf8')
    target = directory.with_suffix('.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.iterdir()):
            archive.write(path, directory.name + '/' + path.name)
    print(json.dumps({'cases': len(requests), 'path': str(target), 'sha256': digest(target.read_bytes()), 'model_calls': 0}))


if __name__ == '__main__':
    main()
