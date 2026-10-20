"""Thin HTTP wrapper around the research pipeline.

  POST /research  {topic} -> report + accepted claims + rejected list
  GET  /topics     the seeded topics the mock web knows about
  GET  /health, /info
"""
import os as _os

from fastapi import FastAPI
from fastapi.responses import FileResponse as _FileResponse

import agents
import tools

app = FastAPI(title="deep-research-agent")


@app.post("/research")
def research(body: dict):
    out = agents.run(body["topic"])
    return {"topic": out["topic"], "report": out["report"],
            "accepted": len(out["claims"]), "rejected": out["rejected"],
            "reruns": out["reruns"], "sources": out["sources"]}


@app.get("/topics")
def topics():
    return {"topics": list(tools.CORPUS.keys())}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"real_llm": False, "backend": "DeterministicPipeline",
            "note": "mock web tools; claims are extractive so every "
                    "citation can be verified mechanically"}

_UI_INDEX = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                          "ui", "index.html")


@app.get("/", include_in_schema=False)
def _demo_ui():
    return _FileResponse(_UI_INDEX)
