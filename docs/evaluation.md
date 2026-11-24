# Evaluation

## Reproducing the results

The gold set is `gold/gold.json`, each item a question, its expected verdict, whether it is settled or ambiguous, and the entries its ruling cites, split into dev and test. Tuning happens on dev; test is scored once. The scripts that run a split take `--split test` for the test split and run dev without it. Those that write records write them to `runs/`, which git ignores, each record carrying the commit it ran at and whether the tree was dirty. The records behind the published numbers are in `results/`, so a new run never lands beside them.

| Script | What it does |
|---|---|
| `scripts/evals/split_gold.py` | Assigns dev or test to every gold item without a split, never changing one already assigned; run after new labels are added and before anything is tuned |
| `scripts/evals/eval_retrieval.py` | Scores level 1's retrieval: recall@k and all-cites@k |
| `scripts/evals/eval_multihop.py <model>` | Plans with the model named and scores level 3's fused retrieval |
| `scripts/evals/eval_rerank.py` | Reranks level 1's top 30 with `BAAI/bge-reranker-v2-m3` and scores level 1's order, the reranked order and the two fused |
| `scripts/evals/eval_lookup.py [--kinds <root> ...]` | Links the records each question names ahead of level 1's order and scores both orders, with each kind's link precision and recall |
| `scripts/evals/eval_agentic.py <model> [--records runs/<agentic>.jsonl]` | Runs the loop on every item of the split and scores the ten it hands over, with its calls, turns, tokens and seconds; `--records` prints the same from records already written |
| `scripts/evals/answer_dev.py <model> [--level 1\|3] [--rerank\|--lookup\|--loop-records runs/<agentic>.jsonl]` | Rules on every item of the split; a model named `claude-…` answers through the API; `--rerank` answers level 1 from its order fused with the reranked one; `--lookup` answers from the records the question names ahead of level 1's order; `--loop-records` answers from the ten each loop record handed over |
| `scripts/evals/judge_dev.py runs/<run>.jsonl` | Judges a run's verdicts and flags with Claude Sonnet 5.5 |
| `scripts/evals/grading_sheet.py runs/<run>.jsonl` | Writes a blind hand-grading template for a run to `gold/hand-grades-<run>.json`: every rules-as-intended item and every third settled item, with gold's and the run's verdicts and no judge |
| `scripts/evals/check_judge.py runs/<run>.judged-<judge>.jsonl` | Compares a judged run with its hand grades and lists every item where they differ, with the judge's reason |
| `scripts/evals/floor_dev.py` | Writes the floor row: "no" to every item, no flag, no cites |
| `scripts/evals/summarize_runs.py --table runs/<run>.jsonl ...` | Prints the results table from judged runs; `--gains <base> <stage>` names the items each of two runs agreed on and the other did not; `--compare <old> <new>` compares two runs' replies |
| `scripts/evals/score_handed.py runs/<run>.jsonl ...` | Scores the ten each answer run retrieved, recall@k and all-cites@k against the gold cites, and refuses a run recorded on a dirty tree |
| `scripts/evals/rescore_published.py [--dry-run]` | Reruns every published row on test at one clean commit, judges each and prints the tables, stopping on the first failure; run again at the same commit, it skips the steps already done; `--dry-run` prints the commands |
| `scripts/evals/check_gate.py <model>` | Runs the gate over the gold questions and `gold/gate-refusals.json`, a set it must refuse |
| `scripts/evals/check_tools.py <model> [--items <n>]` | Checks that the model calls a declared tool with valid arguments on the first n dev items, five unless set; the entry gate for the loop's rows |
| `scripts/corpus/check_supplement.py <srd.txt>` | Checks every passage in `supplement.json` word for word against the SRD 5.1 document's text |

The judge and the hosted rows call the Claude API and authenticate with the profile `ant auth login` stores; a set `ANTHROPIC_API_KEY` takes precedence over it, even an empty one. Everything else runs locally. `scripts/corpus/pull_srd.py` refetches the corpus at its pinned commit.

The rerank scripts need the `rerank` extra, sentence-transformers on PyTorch, which the screen does not use. On Windows, PyPI's torch is CPU-only, so it comes from PyTorch's CUDA 13.2 index:

```
python -m pip install -e ".[dev,rerank]" --extra-index-url https://download.pytorch.org/whl/cu132
```

## Measuring your own model

A model pulled into Ollama is measured on the test split, the split the published rows are scored on, so its row sits beside theirs. Dev is where a choice is tuned before test is run. Every step but the judge runs locally. Each record carries the commit it ran at, so commit any change first: `score_handed.py` refuses a run recorded on a dirty tree.

**1. The key-order check.** The ruling's fields are ordered so the model reasons and flags before it rules, and some models' templates make Ollama sort a schema's keys. A model that fails this check rules before it reasons, and its row would not measure the same thing:

```
python scripts/evals/check_key_order.py <model>
```

The model runs with its template and penalties as shipped, and no row gets a prompt of its own.

**2. The answers.** One record per test item, written to `runs/<stamp>-test-<model>.jsonl`, any `:` in the model's name written as `-`. `--level 3` has the model plan sub-questions first and writes `runs/<stamp>-test-level3-<model>.jsonl`:

```
python scripts/evals/answer_dev.py <model> --split test
```

**3. Retrieval.** recall@k and all-cites@k on the ten entries the model was handed, read beside [the Retrieval table](results.md#retrieval):

```
python scripts/evals/score_handed.py runs/<run>.jsonl
```

At level 1 these are the embedder's, the same for every answering model; at level 3 they are the model's plans, which change from draw to draw. This is as far as the measurement goes without a Claude account. To compare an embedder instead, add it to `EMBEDDERS` in `src/rules_attorney/retrieve.py` and run `scripts/evals/eval_retrieval.py`.

**4. The judge.** Claude Sonnet 5.5 decides each verdict's agreement and writes `runs/<run>.judged-claude-sonnet-5-5.jsonl` beside the run. It needs a Claude account, authenticated as above:

```
python scripts/evals/judge_dev.py runs/<run>.jsonl
```

**5. The table.** Your row, with any published run after it for comparison, here `qwen3.5:9b` at level 1:

```
python scripts/evals/summarize_runs.py --table runs/<run>.jsonl results/test/20261109-144535-test-qwen3.5-9b.jsonl
```

An answer run is one draw. Rerun on the same prompts, `qwen3.5:9b`'s agreement moved by up to four items, and one item of 55 is about 1.8 points, so a gap of one item between rows is not a finding.
