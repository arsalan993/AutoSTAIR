# Blinded answer judging

Manual judgments use four 1–5 scales:

- **Correctness:** agreement with the manually written reference answer.
- **Grounding:** whether factual claims are supported by the supplied evidence.
- **Completeness:** coverage of the important parts of the question.
- **Citation quality:** whether cited passage IDs are present and support nearby claims.

The judge chooses system A, system B, or a tie before the hidden method key is read.
Extra detail is not rewarded automatically; irrelevant or weakly supported additions can
reduce correctness or grounding.

Run the evaluation with generation enabled, then create a randomized file:

```sh
autostair evaluate --generate
autostair blind
```

The command creates:

- `artifacts/results/blinded.jsonl`, which can be shared for judging.
- `artifacts/results/blinded.key.json`, which must remain hidden until judging ends.

For each question, score System A and System B independently from 0–2 for:

1. Answer correctness.
2. Support from the supplied evidence.
3. Citation correctness.
4. Completeness.
5. Appropriate abstention.

Also record `A`, `B`, or `tie`, unsupported claims, and whether a failure came
primarily from retrieval or answer generation. LLM judging is secondary evidence;
the automated retrieval metrics and human source checks remain part of the report.
