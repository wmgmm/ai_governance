"""Evaluate, then optimise, the exam question prompts.

    uv run python run.py baseline     # the plain prompt DSPy writes from the signature
    uv run python run.py handwritten  # a person writes the rules into the instructions
    uv run python run.py bootstrap    # + BootstrapFewShot: adds worked examples that pass the metric
    uv run python run.py mipro        # + MIPROv2: also rewrites the instruction text
    uv run python run.py combined     # MIPROv2 starting from the hand-written instructions
    uv run python run.py noise        # repeat baseline and hand-written 5 times, cache off
    uv run python run.py all

Optimisers only see the train split. Every score is measured on the dev split, which the
optimisers never see. Results go to results/<stage>_<task>.json.
"""
import json
import logging
import statistics
import sys
import time

import dspy

from exam_qs import HAND_WRITTEN, HERE, TASKS, configure_lm, load_examples

RESULTS = HERE / "results"
SEED = 7


def evaluate(program, task, devset):
    _, metric, checks, _ = TASKS[task]
    result = dspy.Evaluate(devset=devset, metric=metric, num_threads=4,
                           display_progress=True, failure_score=0.0)(program)
    rows = []
    for ex, pred, score in result.results:
        try:
            c = checks(ex.passage, pred)
        except Exception:  # the model's reply could not be parsed into the fields
            c = None
        rows.append({"passage": ex.passage, "output": dict(pred) if pred else None,
                     "checks": c, "score": float(score)})
    names = [k for r in rows if r["checks"] for k in r["checks"]]
    pass_rates = {k: sum(bool(r["checks"] and r["checks"][k]) for r in rows) / len(rows)
                  for k in dict.fromkeys(names)}
    out = {"score": round(result.score, 1), "pass_rates": pass_rates, "examples": rows}
    if task == "mcq":  # position bias only shows across a set, so report it, don't score it
        idx = [r["output"].get("answer_index") for r in rows if r["output"]]
        out["answer_positions"] = {p: idx.count(i) for i, p in enumerate("ABCD")}
    return out


def prompt_of(program):
    """The instruction text and worked examples that the optimiser settled on."""
    p = program.predictors()[0]
    return {"instructions": p.signature.instructions,
            "demos": [{k: v for k, v in d.items() if k != "augmented"} for d in p.demos]}


def optimise(stage, task, trainset):
    _, metric, _, _ = TASKS[task]
    student = dspy.Predict(TASKS[task][0])
    if stage == "baseline":
        return student
    if stage == "handwritten":
        return dspy.Predict(TASKS[task][0].with_instructions(HAND_WRITTEN[task]))
    if stage == "bootstrap":
        opt = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=3, max_labeled_demos=3)
        return opt.compile(student, trainset=trainset)
    if stage in ("mipro", "combined"):
        if stage == "combined":
            student = dspy.Predict(TASKS[task][0].with_instructions(HAND_WRITTEN[task]))
        opt = dspy.MIPROv2(metric=metric, auto="light", num_threads=4, seed=SEED,
                           max_bootstrapped_demos=3, max_labeled_demos=3)
        return opt.compile(student, trainset=trainset, minibatch=False,
                           requires_permission_to_run=False)
    raise SystemExit(f"unknown stage {stage}")


def run(stage):
    configure_lm()
    for task, (_, _, _, pos) in TASKS.items():
        trainset, devset = load_examples("train")[pos], load_examples("dev")[pos]
        t0 = time.time()
        # Keep MIPROv2's log: it records every instruction it proposed, not just the winner.
        log = logging.FileHandler(RESULTS / f"{stage}_{task}.log", mode="w")
        logging.getLogger("dspy.teleprompt").addHandler(log)
        program = optimise(stage, task, trainset)
        logging.getLogger("dspy.teleprompt").removeHandler(log)
        out = {"stage": stage, "task": task, "seed": SEED, "n_train": len(trainset),
               "n_dev": len(devset), "dspy_version": dspy.__version__,
               "prompt": prompt_of(program)}
        out.update(evaluate(program, task, devset))
        out["seconds"] = round(time.time() - t0)
        program.save(RESULTS / f"{stage}_{task}_program.json")
        (RESULTS / f"{stage}_{task}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"{stage:9} {task:12} dev score {out['score']:5.1f}  ({out['seconds']}s)")


def noise(repeats=5):
    """Same prompt, same data, fresh samples: how much do scores move by chance alone?"""
    lm = configure_lm()
    out = {}
    for stage in ("baseline", "handwritten"):
        for task, (_, _, _, pos) in TASKS.items():
            devset = load_examples("dev")[pos]
            program = optimise(stage, task, [])
            scores = []
            for r in range(repeats):
                with dspy.context(lm=lm.copy(cache=False)):
                    scores.append(evaluate(program, task, devset)["score"])
            out[f"{stage}_{task}"] = {"scores": scores, "mean": round(statistics.mean(scores), 1),
                                      "sd": round(statistics.stdev(scores), 1)}
            print(stage, task, out[f"{stage}_{task}"])
    (RESULTS / "noise.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    stages = sys.argv[1:] or ["baseline"]
    if stages == ["all"]:
        stages = ["baseline", "handwritten", "bootstrap", "mipro", "combined", "noise"]
    for s in stages:
        noise() if s == "noise" else run(s)
