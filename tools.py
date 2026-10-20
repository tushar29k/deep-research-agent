"""MCP-style research tools over a seeded mock web.

Deterministic and offline: search returns ranked hits from the seeded
corpus, fetch returns the source text. The pipeline code can't tell it
apart from a real search API — the seam is these two functions.
"""
import re

_WORD = re.compile(r"[a-z0-9]+")


def tokens(text):
    out = set()
    for t in _WORD.findall(text.lower()):
        # crude stem so vector/vectors, database/databases collide
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        out.add(t)
    # stopwords: without this, "in" and "the" leak topics into each other
    out -= {"in", "the", "a", "an", "and", "or", "of", "to", "on", "with",
            "for", "it", "is", "as", "at", "by", "from", "this", "that",
            "are", "was", "an", "be", "will", "which"}
    return out


# topic -> list of sources. sources are small but realistic: enough facts
# per source for claims to be grounded, and at least one distractor per
# topic so the researcher has to rank.
CORPUS = {
    "vector databases 2025": [
        {"url": "https://vectordb-weekly.example/pgvector-2025",
         "title": "pgvector at scale: what changed in 2025",
         "text": "pgvector added HNSW index build parallelism in 2025, "
                 "cutting index build times by 40 percent on 10 million "
                 "vectors. It runs inside PostgreSQL, so teams keep their "
                 "existing backup and permission tooling. It lacks "
                 "distributed sharding, which limits it past about "
                 "50 million vectors per node."},
        {"url": "https://vectordb-weekly.example/qdrant-2025",
         "title": "Qdrant 2025 review: speed and filters",
         "text": "Qdrant's 2025 releases focused on filtered HNSW search, "
                 "with p99 latency under 15 milliseconds on 20 million "
                 "768-dimensional vectors. It supports payload filters and "
                 "replication, but operating it means running a separate "
                 "cluster outside your primary database."},
        {"url": "https://vectordb-weekly.example/serverless-tradeoffs",
         "title": "Serverless vector search: the 2025 tradeoff",
         "text": "Serverless vector services charge per query and scale to "
                 "zero, which fits spiky workloads. Per-query cost is "
                 "roughly 5 to 10 times a self-hosted setup at steady load, "
                 "so teams with predictable traffic usually self-host."},
        {"url": "https://vectordb-weekly.example/unrelated-index",
         "title": "SQLite in embedded devices",
         "text": "SQLite remains the default embedded database for mobile "
                 "apps, with a tiny footprint and ACID guarantees."},
    ],
    "eval-driven development": [
        {"url": "https://evalsguide.example/edd-101",
         "title": "Eval-driven development, explained",
         "text": "Eval-driven development means writing a golden dataset "
                 "before changing a prompt, the way tests precede code in "
                 "TDD. Teams at the 2025 LLMs-in-production survey reported "
                 "it as the most common practice for catching regressions: "
                 "61 percent of teams with 20 or more evals said it caught "
                 "a production regression in the previous quarter."},
        {"url": "https://evalsguide.example/judge-agreement",
         "title": "Measuring your LLM judge",
         "text": "In eval-driven development, an LLM-as-judge should be "
                 "measured against human labels: "
                 "report agreement (Cohen's kappa) on a fixed set before "
                 "trusting it. Typical well-prompted judges reach kappa "
                 "0.7 to 0.8; below 0.5 the judge is noise."},
        {"url": "https://evalsguide.example/deterministic-first",
         "title": "Deterministic scorers first",
         "text": "Eval-driven development starts with deterministic "
                 "scorers: exact match, substring and schema checks cost "
                 "nothing "
                 "and never argue. Reserve the judge model for what "
                 "determinism can't score: tone, helpfulness, and whether "
                 "the answer actually addressed the question."},
        {"url": "https://evalsguide.example/cooking-blog",
         "title": "Weeknight pasta recipes",
         "text": "A good carbonara needs guanciale, pecorino, and no "
                 "cream. Toss the pasta in the pan off the heat."},
    ],
    "mcp in production": [
        {"url": "https://agenteng.example/mcp-auth",
         "title": "MCP authentication patterns",
         "text": "Production MCP deployments separate the tool server from "
                 "credential storage: OAuth tokens live server-side and the "
                 "agent receives scoped, short-lived credentials. The 2025 "
                 "agent-security review flagged plaintext API keys in tool "
                 "configs as the most common MCP misconfiguration."},
        {"url": "https://agenteng.example/mcp-evals",
         "title": "Testing MCP tool calls",
         "text": "In production MCP setups, mock the MCP server with "
                 "recorded fixtures and assert "
                 "on the tool-call arguments, not on the model text. "
                 "Replay tests catch schema drift when a tool's parameters "
                 "change."},
        {"url": "https://agenteng.example/mcp-vs-plugins",
         "title": "MCP vs plugin architectures",
         "text": "In production, MCP standardises tool discovery and "
                 "schema, so an agent "
                 "can use new tools without code changes. Plugin systems "
                 "couple tools to one host; MCP servers work across any "
                 "MCP-compatible client."},
        {"url": "https://agenteng.example/gardening",
         "title": "Container gardening basics",
         "text": "Tomatoes need full sun and consistent watering. Mulch "
                 "keeps the soil temperature stable."},
    ],
}


def web_search(query, k=4):
    """Ranked mock hits: overlap-ranked, with distractors ranked low."""
    q = tokens(query)
    hits = []
    for topic, sources in CORPUS.items():
        for s in sources:
            st = tokens(s["title"] + " " + s["text"])
            score = len(q & st) / max(len(q), 1)
            hits.append({"url": s["url"], "title": s["title"],
                         "score": round(score, 3), "_text": s["text"]})
    hits.sort(key=lambda h: -h["score"])
    return hits[:k]


def fetch_source(url):
    for sources in CORPUS.values():
        for s in sources:
            if s["url"] == url:
                return {"url": url, "title": s["title"], "text": s["text"]}
    return {"url": url, "title": "not found", "text": ""}
