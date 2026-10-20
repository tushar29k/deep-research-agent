"""Research evals: citation coverage + claim verifiability (offline).

For each seeded topic:
  citation coverage     — every claim in the final report carries at
                          least one [n] citation (structural: the writer
                          can't emit anything else)
  claim verifiability   — each accepted claim's content tokens are
                          contained in its cited source (the critic's
                          check, re-run independently here)
  planted leak rate     — the researcher's planted fabrications that
                          SURVIVED into the report. Must be zero.
  rejection honesty     — the critic must actually reject the planted
                          ones (a critic that passes everything is a
                          rubber stamp, so we count that too)

Run: python3 evals/run_eval.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import agents  # noqa: E402
import tools  # noqa: E402

TOPICS = list(tools.CORPUS.keys())
_CITE = re.compile(r"\[\d+\]")


def main():
    totals = {"claims": 0, "cited": 0, "verified": 0,
              "planted_in": 0, "planted_leaked": 0, "planted_caught": 0}
    for topic in TOPICS:
        out = agents.run(topic)
        claims = out["claims"]
        rejected = out["rejected"]
        totals["planted_in"] += sum(1 for c in claims + rejected
                                    if c["planted"])
        totals["planted_caught"] += sum(1 for c in rejected if c["planted"])
        totals["planted_leaked"] += sum(1 for c in claims if c["planted"])
        body_lines = [ln for ln in out["report"].splitlines()
                      if ln.startswith("- ")]
        totals["claims"] += len(claims)
        totals["cited"] += sum(1 for ln in body_lines if _CITE.search(ln))
        # independent verifiability re-check of every accepted claim
        cache = {}
        for c in claims:
            if c["url"] not in cache:
                cache[c["url"]] = agents._content_tokens(
                    tools.fetch_source(c["url"])["text"])
            ct = agents._content_tokens(c["claim"])
            cont = len(ct & cache[c["url"]]) / max(len(ct), 1)
            totals["verified"] += cont >= 0.75
        print(f"{topic}: {len(claims)} accepted, {len(rejected)} rejected, "
              f"{out['reruns']} rerun(s)")
    n = max(totals["claims"], 1)
    print(f"citation coverage: {totals['cited']}/{totals['claims']} "
          f"({totals['cited'] / n:.0%})")
    print(f"claim verifiability: {totals['verified']}/{totals['claims']} "
          f"({totals['verified'] / n:.0%})")
    print(f"planted fabrications: {totals['planted_in']} in, "
          f"{totals['planted_caught']} caught, "
          f"{totals['planted_leaked']} leaked")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "eval-history.jsonl"), "a") as f:
        f.write(json.dumps(totals) + "\n")
    ok = (totals["cited"] == totals["claims"]
          and totals["planted_leaked"] == 0
          and totals["planted_caught"] == totals["planted_in"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
