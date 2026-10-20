# ADR 0001 — citations are structural, not prompted

## Decision

The writer only receives claims that carry a `source_id` and an accept
verdict from the critic. There is no code path by which an uncited
claim can reach the report — citation isn't a prompt instruction the
model might ignore, it's a data-flow property.

## Why

Prompted citation ("please cite your sources") degrades the moment the
model is confused; structural citation survives confusion, because the
writer literally never sees the forbidden material. This is the same
instinct as the support-agent's approval gate: the dangerous path
shouldn't exist, not be guarded by a polite request.

## Cost

Claims the researcher found but the critic rejected are lost to the
report — including some true ones rejected on thin containment. The
report is shorter but checkable; that trade is the whole point of the
project.
