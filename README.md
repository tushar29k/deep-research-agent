# deep-research-agent

## Release notes — v1.0 (2026-10-20)

Measured numbers, offline, deterministic pipeline — every figure below
comes from `python3 evals/run_eval.py`, re-run today, across the 3
seeded topics.

- **Citation coverage: 19/19 (100%)** — every claim in every report
  carries a checkable `[n]` citation.
- **Claim verifiability: 19/19 (100%)** — every accepted claim's content
  words are contained in its cited source (re-checked independently in
  the eval, not trusted from the pipeline).
- **Planted fabrications: 6 in, 6 caught, 0 leaked** — the researcher is
  seeded to invent mid-task (the way real agents do); the critic rejected
  all of them, and the suite counts that — a critic that passes
  everything would fail as a rubber stamp.
- Cross-topic noise fixed during the build: aspect queries were dragging
  in other topics' sources; the researcher now selects sources by
  on-topic token overlap and files claims by aspect rules instead.

A research pipeline you can run, inspect, and argue with — no key, no
cost. Open the UI and watch the critic's rejections.

## Live demo

**[https://tushar29k-deep-research-agent.onrender.com](https://tushar29k-deep-research-agent.onrender.com)** — Run a research task on one of the seeded topics, watch the four pipeline stages fire, read the cited report and the fabrications the critic caught.
> Hosted on Render's free tier — the first visit after a while can take ~30s while the instance wakes up.

## The idea

Research agents fail at exactly one thing: they cite like
undergraduates. Confident claims, plausible citations, wrong sources —
or no sources at all. This project makes citation a property of the
data flow instead of a prompt instruction (see `docs/adr/0001`):

1. **Plan** — the topic splits into three aspects (what it is / the
   numbers / the trade-offs), so research has depth on purpose.
2. **Research** — mock MCP web tools return ranked hits; the researcher
   extracts candidate claims from sources and, deliberately, mixes in
   fabricated ones — the way a real LLM researcher hallucinates.
3. **Critic** — every claim is token-checked against its cited source
   (containment ≥ 0.75). Too many rejections and research re-runs once
   with a wider net, like a human would.
4. **Write** — the writer only ever sees accepted claims with source
   ids. An uncited claim has no code path to the report.

## Architecture

```
topic
  │
  ▼
┌─────────┐
│ planner  │  topic -> [overview, numbers, tradeoffs]
└────┬────┘
     ▼
┌─────────┐  web_search / fetch_source (tools.py, seeded mock web)
│researcher│ ── claims + citations ──┐
└────┬────┘                          │
     │ deliberately plants           │
     │ fabrications                  │
     ▼                               │
┌─────────┐                          │
│ critic   │  token-containment      │
│          │  vs cited source        │
└────┬────┘                          │
     │ accepted / rejected           │
     ▼                               │
┌─────────┐                          │
│ writer   │  report + [n] sources ◀─┘ (accepted claims only)
└─────────┘
```

`service.py` wraps it in FastAPI: `POST /research` returns the report,
accept/reject counts, the rejected list (the UI shows it), and the
sources. The mock web corpus lives in `tools.py` — three topics, with
one distractor source each so the researcher actually has to rank.

## API

```
POST /research  {"topic": "mcp in production"} -> {report, accepted, rejected[], reruns, sources}
GET  /topics    the seeded topics the mock web knows
GET  /info      backend honesty badge
```

## Evals

```
python3 evals/run_eval.py
```

For each seeded topic: citation coverage, claim verifiability
(re-checked independently), planted leak rate, and critic rejection
honesty. Results append to `evals/eval-history.jsonl`. Docs:
`docs/adr/` (why citation is structural, why the critic is graded,
why claims stay extractive).
