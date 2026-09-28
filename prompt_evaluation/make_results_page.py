"""Write the results section of the companion page from results/*.json.

    uv run python make_results_page.py

Replaces everything between <!-- RESULTS:START --> and <!-- RESULTS:END --> in
site/prompt_evaluation/index.html. Rerun it whenever the results change.
"""
import html
import json
import re

from exam_qs import HERE

PAGE = HERE.parent / "site" / "prompt_evaluation" / "index.html"
RESULTS = HERE / "results"
STAGES = [
    ("baseline", "Baseline", "The plain prompt DSPy writes from the signature."),
    ("handwritten", "Hand-written rules", "A person copies the checklist rules into the prompt's instructions."),
    ("bootstrap", "BootstrapFewShot", "Adds up to three worked examples that pass the metric."),
    ("mipro", "MIPROv2", "Proposes new instructions and picks the best instruction and examples."),
    ("combined", "Hand-written + MIPROv2", "MIPROv2 starting from the hand-written instructions."),
]
TASK_NAMES = {"short_answer": "Short answer", "mcq": "Multiple choice"}
CHECK_NAMES = {
    "is_a_question": "Is a question", "stands_alone": "Stands alone (no “passage”)",
    "answer_is_short": "Answer ≤ 12 words", "answer_grounded": "Answer grounded in passage",
    "answer_not_leaked": "Answer not in question", "four_options": "Four options",
    "options_distinct": "Options distinct", "index_valid": "Correct option identified",
    "correct_grounded": "Correct option grounded", "distractors_not_copied": "Wrong options not copied from passage",
    "no_length_giveaway": "Correct option not the longest",
}


def load(stage, task):
    return json.loads((RESULTS / f"{stage}_{task}.json").read_text())


def e(text):
    return html.escape(str(text))


def proposals(stage, task):
    """Instruction candidates MIPROv2 proposed, from its log."""
    log = RESULTS / f"{stage}_{task}.log"
    if not log.exists():
        return []
    text = log.read_text()
    block = text.split("Proposed Instructions for Predictor 0:", 1)[-1].split("==> STEP 3", 1)[0]
    return [c.strip() for c in re.split(r"^\d+: ", block, flags=re.M)[1:]]


def same_as_baseline(stage):
    """Tasks where this stage kept the plain prompt and chose no examples."""
    return [TASK_NAMES[t].lower() for t in TASK_NAMES if stage != "baseline"
            and load(stage, t)["prompt"] == load("baseline", t)["prompt"]]


def takeaway():
    s = {st: load(st, "short_answer")["score"] for st, _, _ in STAGES}
    text = (f'On short-answer questions, writing the checklist into the prompt as plain rules raised the score '
            f'from {s["baseline"]:.1f} to {s["handwritten"]:.1f} out of 100. Adding the optimiser on top reached '
            f'{s["combined"]:.1f}. The optimiser on its own scored {s["mipro"]:.1f}.')
    if s["handwritten"] - s["baseline"] > s["combined"] - s["handwritten"]:
        text += " The person’s rules did most of the work."
    return f'<div class="callout governance"><strong>In short</strong><div class="callout-body">{text}</div></div>'


def score_table():
    noise = json.loads((RESULTS / "noise.json").read_text())
    rows = []
    for stage, name, desc in STAGES:
        kept = same_as_baseline(stage)
        if kept:
            which = "" if len(kept) == len(TASK_NAMES) else f"For {' and '.join(kept)} questions, i"
            desc_note = (f'<br><span class="muted">{which or "I"}t kept the plain prompt and no examples, '
                         'so it scored the same as the baseline.</span>')
        else:
            desc_note = ""
        cells = []
        for task in TASK_NAMES:
            score = load(stage, task)["score"]
            n = noise.get(f"{stage}_{task}")
            spread = f'<span class="muted"> (5 reruns: {n["mean"]} ± {n["sd"]})</span>' if n else ""
            cells.append(f"<td><strong>{score:.1f}</strong>{spread}</td>")
        rows.append(f'<tr><th scope="row"><strong>{e(name)}</strong><br><span class="muted">{e(desc)}</span>'
                    f'{desc_note}</th>{"".join(cells)}</tr>')
    return ('<div class="table-wrap"><table><thead><tr><th scope="col">Prompt</th><th scope="col">Short answer</th>'
            f'<th scope="col">Multiple choice</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def checks_table(task):
    names = list(load("baseline", task)["pass_rates"])
    head = "".join(f'<th scope="col">{e(n)}</th>' for _, n, _ in STAGES)
    rows = []
    for c in names:
        cells = "".join(f'<td>{round(100 * load(s, task)["pass_rates"][c])}%</td>' for s, _, _ in STAGES)
        rows.append(f'<tr><th scope="row">{e(CHECK_NAMES.get(c, c))}</th>{cells}</tr>')
    return (f'<div class="table-wrap"><table class="compact"><thead><tr><th scope="col">Check</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def positions():
    rows = []
    for stage, name, _ in STAGES:
        pos = load(stage, "mcq")["answer_positions"]
        cells = "".join(f"<td>{pos[p]}</td>" for p in "ABCD")
        rows.append(f'<tr><th scope="row">{e(name)}</th>{cells}</tr>')
    return ('<div class="table-wrap"><table class="compact"><thead><tr><th scope="col">Prompt</th>'
            + "".join(f'<th scope="col">{p}</th>' for p in "ABCD") + '</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def example_output(stage, task, i=0):
    ex = load(stage, task)["examples"][i]
    out = ex["output"] or {}
    if task == "mcq":
        opts = "\n".join(f"  {'ABCD'[j]}. {o}" + ("   ← marked correct" if j == out.get("answer_index") else "")
                         for j, o in enumerate(out.get("options", [])))
        body = f"Q: {out.get('question')}\n{opts}"
    else:
        body = f"Q: {out.get('question')}\nA: {out.get('answer')}"
    failed = [CHECK_NAMES.get(k, k) for k, v in (ex["checks"] or {}).items() if not v]
    verdict = "Passes every check" if not failed else "Fails: " + ", ".join(failed)
    return f'<div class="prompt-box">{e(body)}</div><p class="muted">{e(verdict)}</p>'


def prompts(stage, task):
    p = load(stage, task)["prompt"]
    demos = f"<p class=\"muted\">Plus {len(p['demos'])} worked example(s).</p>" if p["demos"] else ""
    return f'<div class="prompt-box">{e(p["instructions"])}</div>{demos}'


def build():
    meta = load("baseline", "short_answer")
    parts = [
        takeaway(),
        f'<p class="exercise-note">Measured on the <strong>{meta["n_dev"]} held-back test passages</strong> the '
        f'optimisers never saw (DSPy {e(meta["dspy_version"])}, Gemma 4 E2B (Q8) on llama.cpp, random seed '
        f'{meta["seed"]}). Each score is the share of checklist items passed, averaged over the passages, out of '
        '100: 100 means every question passed every check. Where a prompt was run five times, the bracket shows '
        'the average and the typical spread. Single runs move by up to about 3 points by chance alone, '
        'so treat smaller gaps as ties.</p>',
        score_table(),
        '<h3>Which checks each prompt passes</h3>',
    ]
    for task, name in TASK_NAMES.items():
        parts.append(f"<h4>{name}</h4>{checks_table(task)}")
    parts += [
        '<h3>Where the correct answer sits</h3>'
        '<p class="exercise-note">Counts of which letter (A to D) held the correct answer. '
        f'Across {meta["n_dev"]} multiple-choice questions a fair spread is about {meta["n_dev"] // 4} per '
        'letter. No prompt fixed this, because each question is written on its own. '
        'Shuffle the options in code instead.</p>', positions(),
        '<h3>The same passage, before and after</h3>',
    ]
    for task, name in TASK_NAMES.items():
        parts.append(f'<div class="inner-grid"><div class="inner-card"><strong>{name}: baseline</strong>'
                     f'{example_output("baseline", task)}</div><div class="inner-card"><strong>{name}: '
                     f'hand-written + MIPROv2</strong>{example_output("combined", task)}</div></div>')
    parts.append("<h3>The prompts the optimisers chose</h3>")
    for stage, name, _ in STAGES[1:]:
        for task, tname in TASK_NAMES.items():
            parts.append(f"<details><summary><span>{e(name)}: {tname}</span></summary>"
                         f'<div class="details-content">{prompts(stage, task)}</div></details>')
    cands = proposals("mipro", "short_answer")
    if cands:
        items = "".join(f'<div class="prompt-box">{e(c)}</div>' for c in cands[1:])
        parts.append("<h3>What MIPROv2 proposed, and threw away</h3>"
                     '<p class="exercise-note">Candidate instructions for the short-answer task, '
                     "written by the same 2B model. None mentions answer length or the passage, "
                     "because the proposer never sees the metric. Notice the narrowed topic list: "
                     "the data covers twelve principles.</p>" + items)
    return "\n".join(parts)


def main():
    page = PAGE.read_text()
    start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
    before, rest = page.split(start, 1)
    _, after = rest.split(end, 1)
    PAGE.write_text(f"{before}{start}\n{build()}\n{end}{after}")
    print(f"wrote results into {PAGE}")


if __name__ == "__main__":
    main()
