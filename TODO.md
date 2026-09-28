# TODO: ai_governance

## Vision
A public set of hands-on AI governance modules. Each one builds something small, measures it
and publishes the evidence, with a companion page in The Matts style.

## Roadmap
- [x] Module 1: prompt_evaluation (DSPy + llama.cpp + Gemma 4 E2B, exam questions)
- [ ] Matt: review site wording, then push and enable Pages (Settings > Pages > Source: GitHub Actions)
- [ ] Module 1 extras (optional): option shuffle in code as a demonstrated fix; larger dev set to shrink noise
- [ ] Further modules: to be decided

## Worklog

### 2026-09-28
- Built llama.cpp v0.5.0 from source with CUDA at `~/src/llama.cpp`. Set up a uv environment with DSPy 3.4.0.
- Wrote 24 passages on 12 principles, each with a gold short-answer and a gold MCQ. MCQ answer positions are balanced at 3 per letter per split.
- Metric iterations:
  - v1, form only: the baseline scored 83 and 96, which was misleading.
  - v2: added stands_alone, a 12-word answer limit and the length giveaway check.
  - The gold data then failed v2 (15 of 24 MCQs had the longest option correct), so the distractors were rewritten.
- Clean run (empty cache, 186 s), short answer then MCQ:

  | Stage | Short answer | MCQ |
  |---|---|---|
  | Baseline | 76.7 | 85.4 |
  | Hand-written | 93.3 | 89.6 |
  | Bootstrap | 81.7 | 84.4 |
  | MIPROv2 | 76.7 | 85.4 |
  | Combined | 98.3 | 89.6 |

  Noise SD is 0.9 to 1.9.
- Built the site (landing page and module page), plus the Pages workflow. Checked in Chrome: no overflow at 375 px or on desktop, tabs work, 12 copy buttons.

### 2026-09-28 (later)
- Ran two review subagents on the site: one for clarity and reading level, one user-centred. Matt approved all 36 merged items.
- Changes:
  - Added a "Start here" card with two routes and "If you only read one thing".
  - Added an "On Monday" section with 8 steps for chat-tool users. Setup moved to the end, and all lessons are open.
  - Defined jargon on first use. Landing page reading ease went from 59 to about 75, module page from 72 to about 76 (Flesch, reviewer's estimate).
  - Setup: added the missing `cd` in step 4, what success looks like, and a troubleshooting panel.
  - Results: added a generated "In short" takeaway. Its closing claim is printed only while the data supports it. Added a note when a stage kept the baseline prompt, plain check names, and table row headers.
- Verified in Chrome: 0 broken anchors, 9/9 lessons open, no overflow at 375 px even with all panels open (fixed one long inline code path), results generation gives identical output on repeat.
- Accessibility:
  - Decorative emoji are hidden from screen readers.
  - The OS tabs have full tab ARIA (roles, labels, tabindex) and arrow/Home/End keys, plus focus-visible outlines.
  - The footer and subtitle colour changed from tertiary to secondary grey. Links use `--link` #0066cc.
  - Contrast audit in Chrome: 409/409 text elements on the module page and 28/28 on the landing page pass WCAG AA. Text on the dark gradient card was not measured.
- Licence: CC BY 4.0. Official legal code in `LICENSE`, plus the footer on both pages and the README.
- Open: whether to split the module page into Findings and Run-it pages.

## HANDOVER
State: module 1 is complete locally. The git repo is initialised with origin set. **Not pushed.** Pages is not enabled yet.
Next: Matt reviews the site text, then pushes. Enable Pages with Source: GitHub Actions.

**Traps**
- The browser keeps an old `site.js`/`style.css` after edits (it loaded from cache, transferring 0 bytes). Refetch with `fetch(url, {cache: "reload"})` then reload before testing.
- The Chrome tool's key presses never reach the page (a document keydown listener saw nothing). Test keyboard code with dispatched KeyboardEvents, and ask Matt for a real key check.
- Port 8080 is Tomcat on this machine, so llama-server uses 8090.
- `pkill -f` or `kill $(pgrep -f ...)` kills the calling shell, because the pattern also matches the shell's own command line. Use `pgrep -x <name>` and kill by PID.
- DSPy's cache makes reruns identical. Earlier mixed-code results differed from the clean run (MCQ "combined wins" was noise). Use `DSPY_CACHEDIR=<empty dir>` for the published run.
- MIPROv2 on 12 train items splits them 3 for demos and 9 for validation. Its proposer never sees the metric.
