"""The pipeline: planner -> researcher -> critic -> writer.

Four small agents with explicit contracts, not one big prompt:

- planner    splits the topic into 3 aspects to research
- researcher gathers candidate claims from the mock web tools and — on
  purpose — mixes in a few PLANTED claims it cannot source, the way a
  real LLM researcher hallucinates mid-task
- critic     verifies every claim against its cited source (token
  containment) and rejects what it cannot verify; if too much is
  rejected, research re-runs once with a wider net
- writer     assembles the report from accepted claims only, with
  [n] citations a reader can check

Citation enforcement is structural: the writer only ever sees claims
that carry a source_id and a critic verdict, so an uncited claim
cannot reach the report.
"""
import re

import tools

ASPECTS = [
    ("overview", "what is it and how does it work"),
    ("numbers", "performance cost benchmarks survey percent"),
    ("tradeoffs", "limitations tradeoffs risks"),
]

# fabricated mid-research — these are the claims a real agent invents;
# the critic's job is to keep them out
_PLANTED = [
    ("Experts agree adoption grew 300 percent in 2024 across all teams.",
     "https://evalsguide.example/edd-101"),
    ("A Stanford study proved this approach is always the best choice.",
     "https://vectordb-weekly.example/qdrant-2025"),
]

_SENT = re.compile(r"(?<=[.!?])\s+")

_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "it",
         "for", "on", "with", "are", "was", "it"}


def _content_tokens(text):
    return {t for t in tools.tokens(text) if t not in _STOP}


def plan(topic):
    return [{"aspect": name, "query": f"{topic} {hints}"}
            for name, hints in ASPECTS]


def _aspect_of(sentence):
    s = sentence.lower()
    if re.search(r"\d|percent|times|kappa|ms|milliseconds", s):
        return "numbers"
    if re.search(r"but |lack|limit|tradeoff|risk|flagged|separate|outside", s):
        return "tradeoffs"
    return "overview"


def research(topic, aspects, wide=False):
    """Gather candidate claims: real ones from sources + planted ones.

    Sources are selected by the TOPIC query (score above a floor — keeps
    aspect queries from dragging in cross-topic noise), then each
    sentence is filed under an aspect by keyword rules. Aspect keywords
    decide the filing, never the fetching.
    """
    claims, seen_src = [], {}
    seen_claims = set()
    hits = tools.web_search(topic, k=6 if wide else 5)
    # on-topic = shares >= 2 of the topic's tokens. a single shared token
    # ("2025") is how cross-topic noise sneaks in
    q_tokens = tools.tokens(topic)
    on_topic = []
    for h in hits:
        overlap = len(q_tokens & tools.tokens(h["title"] + " " + h["_text"]))
        if overlap >= 2:
            on_topic.append(h)
    for h in on_topic:
        src = tools.fetch_source(h["url"])
        sid = seen_src.setdefault(h["url"], len(seen_src) + 1)
        for sent in _SENT.split(src["text"]):
            sent = sent.strip()
            if len(_content_tokens(sent)) < 6 or sent in seen_claims:
                continue
            seen_claims.add(sent)
            claims.append({"claim": sent, "aspect": _aspect_of(sent),
                           "url": h["url"], "source_id": sid,
                           "planted": False})
    for text, url in _PLANTED:
        claims.append({"claim": text, "aspect": "overview", "url": url,
                       "source_id": seen_src.get(url, 0), "planted": True})
    return claims, seen_src


def critic(claims):
    """Verify each claim against its cited source; return (ok, rejected)."""
    ok, rejected = [], []
    cache = {}
    for c in claims:
        if c["url"] not in cache:
            cache[c["url"]] = _content_tokens(
                tools.fetch_source(c["url"])["text"])
        src_tokens = cache[c["url"]]
        ct = _content_tokens(c["claim"])
        # verifiable = nearly all content words survive in the source
        containment = len(ct & src_tokens) / max(len(ct), 1)
        c = {**c, "containment": round(containment, 2)}
        if containment >= 0.75:
            ok.append(c)
        else:
            rejected.append({**c, "reason":
                             f"containment {containment:.2f} < 0.75"})
    return ok, rejected


def write_report(topic, ok, seen_src):
    cited = sorted({c["source_id"] for c in ok if c["source_id"]})
    by_aspect = {}
    for c in ok:
        by_aspect.setdefault(c["aspect"], []).append(c)
    lines = [f"# Research report: {topic}", ""]
    titles = {"overview": "What it is", "numbers": "The numbers",
              "tradeoffs": "Trade-offs and limits"}
    for aspect in ("overview", "numbers", "tradeoffs"):
        group = by_aspect.get(aspect)
        if not group:
            continue
        lines.append(f"## {titles[aspect]}")
        for c in group:
            lines.append(f"- {c['claim']} [{c['source_id']}]")
        lines.append("")
    lines.append("## Sources")
    for sid in cited:
        url = next(u for u, i in seen_src.items() if i == sid)
        src = tools.fetch_source(url)
        lines.append(f"[{sid}] {src['title']} — {url}")
    return "\n".join(lines)


def run(topic):
    aspects = plan(topic)
    claims, seen_src = research(topic, aspects)
    ok, rejected = critic(claims)
    reruns = 0
    # too much rejected -> widen the net once, like a human would
    if claims and len(rejected) / len(claims) > 0.4:
        reruns = 1
        claims, seen_src = research(topic, aspects, wide=True)
        ok, rejected = critic(claims)
    report = write_report(topic, ok, seen_src)
    return {"topic": topic, "report": report,
            "claims": ok, "rejected": rejected, "reruns": reruns,
            "sources": seen_src}
