"""Serial NIM comparison using frozen evidence scoring; credentials stay local."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
import urllib.error
import urllib.parse
import urllib.request

from document_lab import DEFAULT_ROOT, connect, digest, now

PROTOCOL_SHA = '43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f'


class ServiceError(RuntimeError):
    pass


class Client:
    def __init__(self, base, key='', model=None):
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Use an HTTP(S) base URL without credentials, query, or fragment')
        if parsed.scheme != 'https' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('Use HTTPS for a remote API')
        self.base = base.rstrip('/')
        if not self.base.endswith('/v1'):
            self.base += '/v1'
        self.key, self.model = key, model
        self.identity = digest(self.base)

    def request(self, path, payload=None):
        headers = {'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        request = urllib.request.Request(self.base + path, headers=headers, data=None if payload is None else json.dumps(payload).encode())
        # Do not forward authorization through redirects to another endpoint.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):
                return None
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=300 if payload else 30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise ServiceError(f'HTTP {exc.code}; response body omitted to protect service details') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ServiceError('Connection/TLS/timeout error; check VPN, endpoint and credentials') from None

    def discover(self):
        models = self.request('/models')
        ids = [m['id'] for m in models.get('data', [])]
        if self.model and self.model not in ids:
            raise ValueError('Requested model is absent from /models')
        if not self.model:
            if len(ids) != 1:
                raise ValueError('Set NIM_MODEL to an exact /models ID when zero or multiple models are listed')
            self.model = ids[0]
        metadata = {}
        for path in ['/metadata', '/version']:
            try:
                metadata[path] = self.request(path)
            except ServiceError as exc:
                metadata[path] = {'unavailable': str(exc)}
        self.revision = digest(json.dumps({'model': self.model, 'metadata': metadata, 'endpoint_sha256': self.identity}, sort_keys=True))
        return {'models': models, 'deployment': metadata, 'selected_model': self.model, 'deployment_snapshot_sha256': self.revision,
                'warning': 'Snapshot hash is not a cryptographic model-weight revision; backend may change'}

    def chat(self, payload):
        body = {'model': self.model, 'messages': payload['messages'], 'temperature': 0,
                'max_tokens': payload['options']['num_predict'], 'stream': False,
                'response_format': {'type': 'json_schema', 'json_schema': {'name': 'evidence', 'strict': True, 'schema': payload['format']}}}
        started = time.perf_counter()
        raw = self.request('/chat/completions', body)
        choice = raw['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('Non-stop generation: ' + str(choice.get('finish_reason')))
        if choice.get('message', {}).get('refusal'):
            raise ValueError('Model refused request')
        return {'message': {'content': choice['message']['content']}, 'done_reason': 'stop',
                'total_duration': int((time.perf_counter() - started) * 1e9),
                'prompt_eval_count': raw.get('usage', {}).get('prompt_tokens'),
                'eval_count': raw.get('usage', {}).get('completion_tokens'),
                'api_usage': raw.get('usage', {}), 'api_finish_reason': choice.get('finish_reason')}


def frozen():
    path = Path(__file__).parent / 'protocols/evaluation_v3.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != PROTOCOL_SHA:
        raise ValueError('Frozen evaluator checksum mismatch')
    spec = importlib.util.spec_from_file_location('nim_frozen_protocol', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Transport:
    """Module-local bridge; never monkeypatch process-global urllib."""
    Request = urllib.request.Request

    def __init__(self, client):
        self.client = client

    def urlopen(self, request, timeout=None):
        url = request if isinstance(request, str) else request.full_url
        if url.endswith('/api/tags'):
            value = {'models': [{'name': 'nim/' + self.client.model, 'digest': self.client.revision}]}
        elif url.endswith('/api/chat'):
            value = self.client.chat(json.loads(request.data))
        else:
            raise ValueError('Unexpected compatibility bridge route')
        return io.BytesIO(json.dumps(value).encode())


def public(root, client, manifest, limit=None):
    protocol = frozen()
    definition = json.loads(manifest.read_text(encoding='utf8'))
    if definition['source_code_sha256'] != PROTOCOL_SHA:
        raise ValueError('Manifest does not identify the frozen scoring protocol')
    protocol.urllib = SimpleNamespace(request=Transport(client))
    db = connect(root)
    cases = [db.execute("SELECT * FROM cases WHERE id=? AND split='test'", (i,)).fetchone() for i in definition['case_ids']]
    if any(c is None for c in cases):
        raise ValueError('Manifest case missing from local library')
    if limit:
        cases = cases[:limit]
    model = 'nim/' + client.model
    config = {'protocol': 'nim-api-comparison-v1', 'scoring_protocol_sha256': PROTOCOL_SHA,
              'manifest_sha256': digest(manifest.read_bytes()), 'cases': len(cases),
              'deployment_snapshot_sha256': client.revision, 'endpoint_sha256': client.identity,
              'temperature': 0, 'num_predict': 600, 'retrieval': 'retrieved',
              'evaluation_role': 'api_comparison_same_public_holdout',
              'source_hashes': {c['doc_id']: db.execute('SELECT sha256 FROM documents WHERE id=?', (c['doc_id'],)).fetchone()[0] for c in cases},
              'limitations': 'Previously exposed public holdout; server context is not forced to 32768; backend reasoning/defaults may differ. No hardware inference from latency.'}
    run_id = digest(json.dumps(config, sort_keys=True))[:24]
    db.execute('INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?)', (run_id, model, now(), json.dumps(config), 'running')); db.commit()
    try:
        for index, case in enumerate(cases):
            if db.execute('SELECT 1 FROM results WHERE run_id=? AND case_id=?', (run_id, case['id'])).fetchone():
                continue
            started = time.perf_counter()
            try:
                spans = json.loads(db.execute('SELECT spans FROM document_spans WHERE doc_id=?', (case['doc_id'],)).fetchone()[0])
                visible = protocol.select_context(spans, case['question'])
                prediction, timing = protocol.ollama(model, case['question'], visible, case['task'])
                evidence = protocol.validate_response(prediction, visible, case['task'])
                metrics = protocol.score(case, prediction, evidence, visible)
                metrics.update(timing)
                prediction = {'response': prediction, 'evidence': evidence, 'visible_ids': [s['id'] for s in visible]}
                status, error = 'complete', None
            except ServiceError:
                raise  # Stop on service errors rather than generating hundreds of bad attempts.
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                prediction, metrics, status, error = {}, {'correct': False, 'evidence_f1': 0}, 'failed', str(exc)
            db.execute('INSERT INTO results VALUES (?,?,?,?,?,?,?,?)', (run_id, case['id'], model, status, json.dumps(prediction), json.dumps(metrics), time.perf_counter() - started, error)); db.commit()
            print(json.dumps({'run_id': run_id, 'progress': index + 1, 'total': len(cases), 'status': status}), flush=True)
        db.execute("UPDATE runs SET status='complete' WHERE id=?", (run_id,)); db.commit()
    except BaseException:
        db.execute("UPDATE runs SET status='interrupted' WHERE id=?", (run_id,)); db.commit()
        raise
    finally:
        db.close()
    return run_id


def private(root, client):
    # Reuse the existing line selection and copying protocol unchanged.
    spec = importlib.util.spec_from_file_location('nim_private_protocol', Path(__file__).parent / 'private_extraction.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    class AbortPrivate(BaseException):
        pass
    class PrivateTransport(Transport):
        def urlopen(self, request, timeout=None):
            try:
                return super().urlopen(request, timeout)
            except ServiceError as exc:
                raise AbortPrivate(str(exc)) from None
    transport = PrivateTransport(client)
    module.urllib = SimpleNamespace(request=transport)
    model = 'nim/' + client.model
    try:
        module.extract(root, model)
    except AbortPrivate as exc:
        raise ServiceError(str(exc)) from None
    # Retain explicit records for every field of documents with unread pages.
    from local_demo import FIELDS
    db = connect(root)
    for doc in db.execute("SELECT * FROM documents WHERE dataset='private' AND status!='needs_review'").fetchall():
        run_id = digest(doc['sha256'] + client.revision + 'nim-blocked-incomplete-v1')[:24]
        metadata = {'protocol': 'nim-private-comparison-v1', 'gold_status': 'unlabeled', 'reason': 'Incomplete source; no model request made'}
        for field in FIELDS:
            db.execute('INSERT OR REPLACE INTO findings VALUES (?,?,?,?,?,?,?)', (run_id, doc['id'], model, field, '[]', 'blocked_incomplete_source', json.dumps(metadata)))
    db.commit(); db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--stage', choices=['discover', 'public', 'private', 'all'], default='discover')
    parser.add_argument('--limit', type=int, help='Public smoke-test subset only; omit for the full 200-case manifest')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    base = os.getenv('NIM_BASE_URL')
    if not base:
        parser.error('Set NIM_BASE_URL locally; do not paste credentials into chat')
    client = Client(base, os.getenv('NIM_API_KEY', ''), os.getenv('NIM_MODEL'))
    snapshot = client.discover()
    report = args.root / 'reports/nim'; report.mkdir(parents=True, exist_ok=True)
    # Local only: deployment metadata can contain internal infrastructure details.
    (report / 'deployment.json').write_text(json.dumps(snapshot, indent=2), encoding='utf8')
    print(json.dumps({'model': client.model, 'metadata_saved_locally': True}), flush=True)
    if args.stage in ['public', 'all']:
        public(args.root, client, args.root / 'evaluation/frozen_public_holdout.json', args.limit)
    if args.stage in ['private', 'all']:
        private(args.root, client)


if __name__ == '__main__':
    try:
        main()
    except ServiceError as exc:
        raise SystemExit(str(exc)) from None
