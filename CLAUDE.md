# CLAUDE.md: ai_governance

Public teaching repo on AI governance. Remote: github.com/wmgmm/ai_governance (public).
Pages: wmgmm.github.io/ai_governance/, deployed from `site/` by GitHub Actions. Not pushable
without Matt's ask in the same message.

## Rules
- Each module is a top-level folder with its own `pyproject.toml` (uv) and `results/`.
- `site/` is plain static HTML using The Matts style (tokens in `site/assets/style.css`,
  source: wmgmm.github.io/thematts/workshop.html). No build step. Light theme only, to match.
- Results on the site are generated, never hand-typed: rerun
  `prompt_evaluation/make_results_page.py` after any run. It rewrites only the block between
  `<!-- RESULTS:START -->` and `<!-- RESULTS:END -->`.
- Lesson prose on the site quotes measured numbers. After a rerun, check every number in the
  lessons against `results/*.json` and correct the prose.
- Governance topics must be future proof: principles only, no article numbers, deadlines or
  named regulations as answers.
- `.venv/` and `.git/` carry the `user.com.dropbox.ignored` xattr. Re-apply after recreating
  them (see the git-in-dropbox skill). Never `dropbox exclude add`.
- Licence: CC BY 4.0 for everything (`LICENSE`). The footer on every page carries the licence line.
- Accessibility bar: WCAG AA contrast on every text element (links use `--link`, not `--apple-blue`),
  decorative icons `aria-hidden`, tabs keyboard-operable. Re-run the contrast audit after colour changes.

## prompt_evaluation
- Server: `prompt_evaluation/scripts/start_server.sh`, port **8090** (8080 is Tomcat on this
  machine). llama.cpp built at `~/src/llama.cpp` (v0.5.0, CUDA, sm_89 for the RTX 4080 SUPER).
- `--reasoning off` is required: Gemma 4 thinks by default (269 vs 13 tokens on a short answer).
- DSPy talks to `/v1` with the default ChatAdapter. Do not use JSONAdapter or
  `response_format`: llama.cpp's `/v1` json_schema path is unreliable.
- DSPy caches LM calls in `~/.dspy_cache`. For a clean, honest rerun set
  `DSPY_CACHEDIR` to an empty directory. The `noise` stage disables the cache itself.
- The metric is deterministic on purpose (no LLM judge). Every gold item in
  `data/passages.jsonl` must pass it; check after editing data or metric.
