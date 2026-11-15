# Lazy Dunmas

Rules disputes at a D&D table, answered by a local model from the SRD 5.1, every ruling citing the sections it rests on, plus an evaluation harness that measures retrieval and answers separately against a gold set.

<!-- Demo video and screenshots go here. -->

## Running it

You need Python 3.12 or later, Node 20.19 or 22.12 or later, and Ollama.

Pull the two models:

```
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Install the server and the screen, from the repository root:

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cd web
npm install
```

On macOS or Linux, the venv's Python is `.venv/bin/python` rather than `.venv/Scripts/python`.

Then, each in a terminal of its own, with Ollama running:

```
.venv/Scripts/python -m uvicorn rules_attorney.app.server:app
```

```
cd web
npm run dev
```

The server embeds the corpus once at startup, then serves on port 8000. The screen is at `http://localhost:5173`, and forwards questions to the server. The encyclopedia needs only the second terminal: it reads the data files in the browser.

## Docs

- [How it works](docs/how-it-works.md): the run phase by phase, the models, the server, the screen and the corpus.
- [Results](docs/results.md): the retrieval stages and the models, scored on the held-out test split.
- [Evaluation](docs/evaluation.md): reproducing the results, and measuring your own model.
- [Development](docs/development.md): the checks.

This work includes material taken from the System Reference Document 5.1 ("SRD 5.1") by Wizards of the Coast LLC and available at
https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License available at https://creativecommons.org/licenses/by/4.0/legalcode.
