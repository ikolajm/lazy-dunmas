# How it works

You ask one rules question, and the screen shows the run in the order it happens:

1. **Question.** A gate call first decides whether the question is about the rules of D&D 5e at all. A question off the game is refused and handed back to edit; a question that might be about the rules goes on.
2. **Splitting the dispute.** The model names the separate rules the question turns on, one short sub-question per rule.
3. **Rules found.** The question and each sub-question are embedded and ranked against every SRD entry by cosine similarity, and the rankings are fused into one. The first ten entries are what the model is handed.
4. **Verdict.** The model rules from those ten entries alone and returns a structured ruling: the verdict, an ambiguity flag, an explanation, and the entries it cites. Each cited entry opens beside the ruling, as the encyclopedia shows it.

This is level 3 in [the results](results.md). The server streams each phase to the screen as server-sent events as it lands. A stop cancels the request to the model, and a run is ended at 30 seconds.

- **Models:** `qwen3.5:9b` for the gate, the plan and the ruling, and `nomic-embed-text` for the embeddings, both through [Ollama](https://ollama.com), locally.
- **Server:** Python and FastAPI, in `src/rules_attorney/app/`. The served calls build the same request the measured runs did, so what the screen shows is what the results table measured.
- **Screen:** React and Vite in `web/`, styled with [Loom](https://github.com/ikolajm/loom). Beside the ask screen, an encyclopedia lists the SRD's spells, magic items, monsters, weapons and armor, races, conditions and weapon properties in a table you can search, filter and sort. A row opens beside the table as a stat block built from its record, or as its SRD entry for the kinds that have no record view, with the entry the model is handed a tab away. It reads `data/srd-5.1/` in the browser, so browsing needs neither the server nor Ollama.
- **Corpus:** the SRD 5.1's rule sections, conditions, spells, weapon properties, weapons, armor and gear with rules, class features and the classes' spellcasting, classes, races, racial traits, feats, magic items and monster stat blocks, from [5e-bits/5e-database](https://github.com/5e-bits/5e-database) at a pinned commit, in `data/srd-5.1/`; and `supplement.json` beside them, the rules only the SRD 5.1 document's prose holds, copied verbatim by hand: multiclassing, the equipment chapter's armor and weapon rules, inspiration, gaining a level, the feats chapter, reaction spell triggers, the monster introduction's rules for damage immunities, multiattack, limited usage, grappling and legendary creatures, and a few lines more.
