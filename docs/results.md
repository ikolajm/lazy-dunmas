# Results

Every stage hands the answering model 10 SRD entries, so none wins by reading more.

- **Level 1** ranks the entries, chunked by header and embedded with `nomic-embed-text`, by cosine similarity to the question.
- **1 + rerank** reorders level 1's top 30 with the cross-encoder `BAAI/bge-reranker-v2-m3` and fuses that order with level 1's.
- **1 + lookup** puts the records the question names, a weapon, a spell, a condition, a race, a class feature, a magic item or a creature, ahead of level 1's order.
- **Level 3** has the answering model split the question into sub-questions, one per rule it turns on, ranks the entries for the question and each sub-question, and fuses the rankings with reciprocal rank fusion, each cut to its first 10.
- **The loop** gives the answering model two tools, `search`, which returns the top five entries in full, and `lookup`, which resolves a record by name, for up to six calls. The code then hands over the records looked up first, then the question's ranking fused with every search's, each cut to its first 10.

At every stage the model returns a structured ruling (an explanation, an ambiguity flag, a verdict and the entries cited), validated against a Pydantic schema. Scored on the held-out test split once: 67 gold items, 55 with a verdict to judge and 14 that should be flagged as ambiguous.

## Retrieval

all-cites@k, the share of items with every entry their ruling cites in the top k:

| k | level 1 | 1 + rerank | 1 + lookup | level 3, `qwen3.5:9b` | level 3, Opus | loop, `qwen3.5:9b` | loop, Opus |
|---|---|---|---|---|---|---|---|
| 3 | 0.299 | 0.343 | 0.358 | 0.239 | 0.328 | 0.433 | 0.493 |
| 5 | 0.403 | 0.493 | 0.507 | 0.358 | 0.507 | 0.493 | 0.716 |
| 10 | 0.537 | 0.582 | 0.612 | 0.552 | 0.701 | 0.672 | 0.910 |

At the 10 the model is handed, level 1 completes 54% of items and Opus's loop 91%. The loop driven by `qwen3.5:9b` scores 0.672, above the lookup alone at 0.612, and level 3 planned by the 9b scores below level 1 at 3 and 5. Retrieval is deterministic for level 1, rerank and lookup; level 3 and the loop depend on the model's plans and searches, and each column is the one draw the answers below were given.

## Rulings

| Model | Level | Thinking | Agreement | Expected flagged | Settled flagged | Schema failures | Cites resolved, strict | Once unmarked | Commit |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | adaptive | 48 / 55 | 5 / 14 | 1 / 53 | 0 / 67 | 173 / 173 | 173 / 173 | 942fad6 |
| claude-opus-5-5 | 1 + rerank | adaptive | 46 / 55 | 7 / 14 | 0 / 53 | 0 / 67 | 183 / 183 | 183 / 183 | 942fad6 |
| claude-opus-5-5 | 1 + lookup | adaptive | 47 / 55 | 6 / 14 | 2 / 53 | 0 / 67 | 182 / 182 | 182 / 182 | 942fad6 |
| claude-opus-5-5 | 3 | adaptive | 51 / 55 | 5 / 14 | 0 / 53 | 0 / 67 | 186 / 186 | 186 / 186 | 942fad6 |
| claude-opus-5-5 | loop | adaptive | 53 / 55 | 7 / 14 | 0 / 53 | 0 / 67 | 215 / 215 | 215 / 215 | 942fad6 |
| gemma4:12b | 1 | off | 43 / 55 | 3 / 14 | 9 / 53 | 4 / 67 | 115 / 127 | 115 / 127 | 942fad6 |
| qwen3.5:9b | 1 | off | 42 / 55 | 5 / 14 | 5 / 53 | 0 / 67 | 108 / 115 | 113 / 115 | 942fad6 |
| qwen3.5:9b | 1 + rerank | off | 45 / 55 | 0 / 14 | 2 / 53 | 0 / 67 | 94 / 108 | 106 / 108 | 942fad6 |
| qwen3.5:9b | 1 + lookup | off | 42 / 55 | 1 / 14 | 3 / 53 | 3 / 67 | 79 / 108 | 106 / 108 | 942fad6 |
| qwen3.5:9b | 3 | off | 44 / 55 | 0 / 14 | 4 / 53 | 0 / 67 | 108 / 121 | 119 / 121 | 942fad6 |
| qwen3.5:9b | loop | off | 41 / 55 | 3 / 14 | 5 / 53 | 1 / 67 | 86 / 125 | 119 / 125 | 942fad6 |
| qwen3.5:4b | 1 | off | 40 / 55 | 4 / 14 | 7 / 53 | 1 / 67 | 74 / 108 | 86 / 108 | 942fad6 |
| qwen3.5:2b | 1 | off | 36 / 55 | 2 / 14 | 10 / 53 | 0 / 67 | 6 / 92 | 82 / 92 | 942fad6 |
| qwen3.5:0.8b | 1 | off | 19 / 55 | 3 / 14 | 18 / 53 | 3 / 67 | 25 / 87 | 27 / 87 | 942fad6 |
| ministral-3:8b | 1 | off | 38 / 55 | 9 / 14 | 18 / 53 | 0 / 67 | 38 / 125 | 90 / 125 | 942fad6 |
| olmo-3:7b-instruct | 1 | off | 24 / 55 | 2 / 14 | 17 / 53 | 0 / 67 | 53 / 97 | 78 / 97 | 942fad6 |
| floor | - | - | 27 / 55 | 0 / 14 | 0 / 53 | 0 / 67 | 0 / 0 | 0 / 0 | 942fad6 |

- **Agreement** is whether the verdict means the same as the gold verdict, decided by Claude Sonnet 5.5 as judge. The judge was checked against hand grades before its scores were counted, and matched twelve of twelve graded blind, on a run made before the corpus held magic items and monsters. With 55 judged items, one item is about 1.8 points.
- **The flag** is read as two rates, never one count: a system that never flags would score well on a count, since settled items outnumber the rest.
- **Cites** are checked against the corpus as written and once a leading `## ` marker, the commonest slip, is removed.
- **The floor** answers "no" to every item, never flags and cites nothing, judged like any other row, so the bottom of the table is measured. It agrees on 27 of 55, and two models score below it.
- **Local models** run through Ollama as their default tags ship them, `Q4_K_M` except `qwen3.5:2b` and `qwen3.5:0.8b` at `Q8_0`, with thinking off and temperature 0. **Opus 5.5** is the ceiling, through the API at effort `high`; it cannot turn thinking off.
- **Answer runs do not reproduce.** Measured on the earlier corpus and its 52 test items, before magic items and monsters: rerun on the same prompts in the same session, `qwen3.5:9b` shared 6 to 11 of 52 replies with its first draw at every stage but level 3, which matched in all three draws. Its agreement across draws, of 44: level 1 32 and 34, rerank 35 and 32, lookup 36, 32 and 32, level 3 33 three times, the loop 31 and 30. No 9b stage separates from level 1 by more than that spread, here or on the earlier corpus, and its rows above, one draw each, are not ranked against each other. The other local models were run once, their spread unmeasured.
- **Opus's loop gains five items against level 1 and loses none**, alongside the largest retrieval gain: `ranged-prone-five-feet`, `readied-attack-extra-attack`, `halfling-greatsword`, `relentless-endurance-massive-damage` and `grappler-pin-attacks`. Level 3 gains three and loses none, the lookup gains one and loses two, and rerank loses two. Each is one draw. The loop flags 7 of the 14 ambiguous items to level 1's 5, and no settled item to level 1's one.
- **The loop's cost**, per item before the answer call: Opus makes 4.58 calls over 3.21 turns, 8,240 input and 827 output tokens, in 11.1 seconds, and 18 of 67 items reach the six-call cap; `qwen3.5:9b` makes 3.15 calls, 3,117 and 452 tokens, in 5.7 seconds, and 5 reach the cap.

Every number is computed from run records by `scripts/evals/summarize_runs.py --table` and `--gains`, `scripts/evals/score_handed.py` and `scripts/evals/eval_agentic.py --records`, all written by `scripts/evals/rescore_published.py` at commit `942fad6`. The records are in `results/`: `results/test/` holds the test run and the floor; `results/reruns/` the 9b's draws on the earlier corpus, the first at `15463d8` and the reruns at `fcd6d77`; and `results/judge-check/` the run the judge was checked against, with its judged file, recorded on a dirty tree at `66a051b`, also on the earlier corpus.
