"""Field-balanced retrieval helper (v2). Widens what is retrieved; it never claims a clause exists.

``select_context(spans, fields)`` picks span IDs for a context window from SourceStore-style spans
({"id", "text", "page", "start", "end"}). Pure Python (BM25 implemented here), deterministic, no model call.

The report's ``context_coverage`` is *context coverage* (share of document characters placed in the context),
NOT answer recall: a span being selected does not mean it contains the answer.
"""
from __future__ import annotations

import math
import re
from collections import Counter

COVERAGE_LABEL = "context coverage, not answer recall"

# Legal synonyms per prototype field. Query expansion only widens retrieval.
FIELD_QUERIES = {
    "parties": ["parties", "between", "by and between", "party", "supplier", "customer", "client", "vendor",
                "company", "licensor", "licensee", "contractor", "agreement is made"],
    "effective_date": ["effective date", "commencement", "dated as of", "entered into", "term begins", "start date",
                       "effective as of", "made as of"],
    "payment": ["payment", "fees", "invoice", "pay", "compensation", "price", "charges", "net 30", "due",
                "remuneration"],
    "termination": ["termination", "terminate", "terminated", "expiration", "expire", "breach", "cause",
                    "notice of termination", "convenience"],
    "deliverables": ["deliverables", "services", "scope of work", "statement of work", "milestone", "acceptance",
                     "work product", "deliver"],
    "confidentiality": ["confidential", "confidentiality", "non-disclosure", "nondisclosure",
                        "proprietary information", "disclose", "trade secret"],
    "renewal": ["renew", "renewal", "automatically extend", "successive", "term", "extension", "extend",
                "initial term", "renewal term"],
    "governing_law": ["governing law", "governed by", "laws of the state", "jurisdiction", "venue", "courts of",
                      "construed in accordance", "choice of law"],
}

_TOKEN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")
_STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to was were will with".split())
_NUMBERED = re.compile(r"^\s*(?:(?:section|article)\s+)?(?:\d+(?:\.\d+)*[.)]?|[ivxlc]+[.)])\s+\S")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


def _terms(text: str) -> list[str]:
    toks = _tokens(text)
    return toks + [a + " " + b for a, b in zip(toks, toks[1:])]


def _phrase_terms(phrases: list[str]) -> list[str]:
    """Unigram terms plus bigrams of each phrase (bigrams reward the phrase appearing intact)."""
    out: list[str] = []
    for p in phrases:
        out += _terms(p)
    return out


class BM25:
    """Okapi BM25 over unigrams and bigrams. Deterministic; idf is floored at a small positive value."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(_terms(d)) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 0.0
        df: Counter = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: max(math.log(1 + (n - f + 0.5) / (f + 0.5)), 1e-6) for t, f in df.items()}

    def score(self, query_terms: list[str], i: int) -> float:
        tf = self.tf[i]
        norm = (1 - self.b) + self.b * (self.len[i] / self.avg if self.avg else 0.0)
        s = 0.0
        for t in dict.fromkeys(query_terms):  # unique, order-stable
            f = tf.get(t, 0)
            if f:
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * norm)
        return s


def looks_like_heading(text: str, max_chars: int = 80) -> bool:
    """Short single line that is numbered ("12. Governing Law"), Title Case or ALL CAPS."""
    line = text.strip()
    if not line or "\n" in line or len(line) > max_chars:
        return False
    cap_ok = lambda w: w[:1].isupper() or w.lower() in _STOP or not w[:1].isalpha()  # noqa: E731
    if _NUMBERED.match(line):
        words = re.sub(r"^\S+\s+", "", line).rstrip(".:").split()
        return 1 <= len(words) <= 7 and all(cap_ok(w) for w in words)
    words = line.rstrip(".:").split()
    if not 1 <= len(words) <= 6 or line.endswith((",", ";")):
        return False
    return line.isupper() or all(cap_ok(w) for w in words)


def _bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def select_context(spans: list[dict], fields: list[str] | None = None, budget_bytes: int = 20000,
                   per_field_min_bytes: int = 1500, opening_lines: int = 3, closing_lines: int = 3,
                   heading_follow: int = 2, heading_boost: float = 2.0,
                   field_queries: dict | None = None) -> tuple[list[str], dict]:
    """Choose span IDs for the context, in document order, within ``budget_bytes`` (UTF-8 bytes of span text).

    Priority: (1) opening and closing spans, (2) each field's top-scoring spans up to ``per_field_min_bytes``
    (round-robin so no field starves another), (3) the remaining budget by best score across fields. A heading
    hit pulls in the next ``heading_follow`` spans with it. A span that does not fit is skipped, never
    truncated, so the budget is a hard ceiling (opening/closing included).
    """
    queries = field_queries or FIELD_QUERIES
    names = list(fields) if fields else list(queries)
    unknown = [f for f in names if f not in queries]
    if unknown:
        raise ValueError(f"no query terms for fields: {unknown}")
    n = len(spans)
    sizes = [_bytes(s["text"]) for s in spans]
    bm = BM25([s["text"] for s in spans])

    scores: dict[str, list[float]] = {}
    headed: dict[str, set[int]] = {}
    for f in names:
        terms = _phrase_terms(queries[f])
        term_set = set(terms)
        sc = [bm.score(terms, i) for i in range(n)]
        hs: set[int] = set()
        for i, s in enumerate(spans):
            if looks_like_heading(s["text"]) and term_set & set(_terms(s["text"])):
                sc[i] = sc[i] * heading_boost + 1.0  # the constant lets a heading win even with zero BM25
                hs.add(i)
        scores[f], headed[f] = sc, hs

    chosen: dict[int, str] = {}  # span index -> reason (first reason wins)
    used = 0

    def take(i: int, reason: str) -> bool:
        nonlocal used
        if i in chosen:
            return True
        if used + sizes[i] > budget_bytes:
            return False
        chosen[i] = reason
        used += sizes[i]
        return True

    for i in list(range(min(opening_lines, n))) + list(range(max(n - closing_lines, opening_lines), n)):
        take(i, "opening" if i < opening_lines else "closing")

    def take_with_followers(f: str, i: int, reason: str) -> int:
        before = used
        if take(i, reason) and i in headed[f]:
            for j in range(i + 1, min(i + 1 + heading_follow, n)):
                take(j, "heading_follow")
        return used - before

    ranked = {f: sorted((i for i in range(n) if scores[f][i] > 0), key=lambda i: (-scores[f][i], i)) for f in names}
    per_field_bytes = {f: 0 for f in names}
    cursor = {f: 0 for f in names}
    active = set(names)
    while active:  # one span per field per round
        for f in names:
            if f not in active:
                continue
            if per_field_bytes[f] >= per_field_min_bytes or cursor[f] >= len(ranked[f]):
                active.discard(f)
                continue
            i = ranked[f][cursor[f]]
            cursor[f] += 1
            if i in chosen:
                per_field_bytes[f] += sizes[i]  # already in context: counts toward this field's minimum
            else:
                per_field_bytes[f] += take_with_followers(f, i, "field_min:" + f)

    pool = sorted(((max(scores[f][i] for f in names), i) for i in range(n) if i not in chosen),
                  key=lambda x: (-x[0], x[1]))
    for sc, i in pool:
        if sc <= 0:
            break
        take_with_followers(max(names, key=lambda f: (scores[f][i], f)), i, "score")

    order = sorted(chosen)
    ids = [spans[i]["id"] for i in order]
    per_field = {}
    for f in names:  # a selected span counts for every field it scores for
        hit = [i for i in order if scores[f][i] > 0]
        per_field[f] = {"spans": len(hit), "bytes": sum(sizes[i] for i in hit),
                        "min_bytes_met": per_field_bytes[f] >= per_field_min_bytes or cursor[f] >= len(ranked[f]),  # or every scoring span was taken
                        "heading_hits": sorted(spans[i]["id"] for i in headed[f] if i in chosen)}
    total_chars = sum(len(s["text"]) for s in spans)
    sel_chars = sum(len(spans[i]["text"]) for i in order)
    report = {
        "label": COVERAGE_LABEL,
        "context_coverage": (sel_chars / total_chars) if total_chars else 0.0,
        "coverage_note": "Fraction of document characters placed in context. Selecting a span does not mean it contains the answer.",
        "selected_spans": len(ids), "total_spans": n, "selected_bytes": used, "budget_bytes": budget_bytes,
        "per_field": per_field,
        "reasons": {spans[i]["id"]: chosen[i] for i in order},
    }
    return ids, report
