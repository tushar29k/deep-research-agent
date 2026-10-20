# ADR 0002 — the critic is graded too

## Decision

The eval suite counts not only the report's quality but the critic's
behaviour: planted fabrications in, caught, leaked. A critic that
rejects nothing would pass a report-quality-only eval; ours must
actively reject 2 of every researcher's planted claims.

## Why

In production, the most dangerous evaluator is the one that always
says yes — it looks like quality infrastructure while doing nothing.
Grading the grader (recall on known-bad inputs) is how you know the
gate is real. The planted claims are the project's adversarial suite,
same role as support-agent's bait questions.

## Cost

The planted claims are hand-written, not sampled from real model
hallucinations — the suite measures the critic against fabrications we
chose, which is a weaker claim than measuring it against the wild. The
researcher is also seeded to plant, which is honest about being a
simulation.
