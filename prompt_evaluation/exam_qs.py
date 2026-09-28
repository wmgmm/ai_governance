"""Exam question generation with DSPy: the task, the data and the metric.

Two tasks, both written from a short AI governance passage:
  - a short-answer question with its answer
  - a multiple-choice question with four options and the index of the correct one

The metric is deliberately simple and deterministic (no LLM judge), so every run is
reproducible and free. It checks that a question is well formed and grounded in the
passage. It does not measure whether the question is a *good* exam question: that still
needs a human reviewer.
"""
import json
import os
import re
from pathlib import Path

import dspy

HERE = Path(__file__).parent
API_BASE = os.environ.get("LLM_API_BASE", "http://localhost:8090/v1")


def configure_lm(temperature=0.7):
    """Point DSPy at the local llama-server (OpenAI-compatible API)."""
    lm = dspy.LM("openai/gemma-4-e2b", api_base=API_BASE, api_key="local",
                 temperature=temperature, max_tokens=600)
    dspy.configure(lm=lm)
    return lm


# ---------------------------------------------------------------- 1. the task (signatures)

class ShortAnswerQuestion(dspy.Signature):
    """Write one exam question, answerable from the passage, with its short answer."""

    passage: str = dspy.InputField()
    question: str = dspy.OutputField()
    answer: str = dspy.OutputField()


class MultipleChoiceQuestion(dspy.Signature):
    """Write one multiple-choice exam question about the passage."""

    passage: str = dspy.InputField()
    question: str = dspy.OutputField()
    options: list[str] = dspy.OutputField()
    answer_index: int = dspy.OutputField()


# ---------------------------------------------------------------- 2. the data

def load_examples(split):
    """Return (short_answer_examples, mcq_examples) for 'train' or 'dev'."""
    rows = [json.loads(line) for line in open(HERE / "data" / "passages.jsonl")]
    rows = [r for r in rows if r["split"] == split]
    sa = [dspy.Example(passage=r["passage"], question=r["sa_question"],
                       answer=r["sa_answer"]).with_inputs("passage") for r in rows]
    mcq = [dspy.Example(passage=r["passage"], question=r["mcq_question"],
                        options=r["mcq_options"],
                        answer_index=r["mcq_answer_index"]).with_inputs("passage") for r in rows]
    return sa, mcq


# ---------------------------------------------------------------- 3. the metric

STOP = set("""a an the of to in on for and or is are was were be been it its this that
these those with by as at from can may not no do does what which who whom why how when
there their they them than then so such any each more most very""".split())


def words(text):
    # First five letters is a crude stem, so "builds" and "building" match.
    return [w[:5] for w in re.findall(r"[a-z0-9]+", str(text).lower()) if w not in STOP]


def overlap(text, source):
    """Fraction of the content words in `text` that also appear in `source`."""
    w = words(text)
    return sum(x in set(words(source)) for x in w) / len(w) if w else 0.0


def norm(text):
    return " ".join(re.findall(r"[a-z0-9]+", str(text).lower()))


def stands_alone(question):
    """Students sit the exam without the passage, so the question must not refer to it."""
    return not re.search(r"\b(passage|the text|according to|mentioned|described above)\b",
                         question, re.I)


def short_answer_checks(passage, pred):
    q, a = str(pred.question).strip(), str(pred.answer).strip()
    return {
        "is_a_question": q.endswith("?") and len(q.split()) >= 5,
        "stands_alone": stands_alone(q),
        "answer_is_short": 0 < len(a.split()) <= 12,
        "answer_grounded": overlap(a, passage) >= 0.6,
        "answer_not_leaked": overlap(a, q) < 0.6,
    }


def mcq_checks(passage, pred):
    q, opts = str(pred.question).strip(), list(pred.options or [])
    idx = pred.answer_index if isinstance(pred.answer_index, int) else -1
    valid = 0 <= idx < len(opts)
    distractors = [o for i, o in enumerate(opts) if i != idx]
    return {
        "is_a_question": q.endswith("?") and len(q.split()) >= 5,
        "stands_alone": stands_alone(q),
        "four_options": len(opts) == 4,
        "options_distinct": len({norm(o) for o in opts}) == len(opts) > 0,
        "index_valid": valid,
        "correct_grounded": valid and overlap(opts[idx], passage) >= 0.5,
        "distractors_not_copied": valid and all(norm(d) not in norm(passage) for d in distractors),
        # Test-wise students pick the longest option; the right answer must not stand out.
        "no_length_giveaway": valid and bool(distractors) and
            len(opts[idx]) <= 1.2 * sum(map(len, distractors)) / len(distractors),
    }


def _score(checks, trace):
    # While optimisers bootstrap demos (trace is set) only perfect outputs count;
    # when evaluating, give partial credit so small improvements are visible.
    return all(checks.values()) if trace is not None else sum(checks.values()) / len(checks)


def short_answer_metric(example, pred, trace=None):
    return _score(short_answer_checks(example.passage, pred), trace)


def mcq_metric(example, pred, trace=None):
    return _score(mcq_checks(example.passage, pred), trace)


# A person's attempt: the same rules the metric checks, written into the instructions.
HAND_WRITTEN = {
    "short_answer": """Write one exam question about the passage, with its answer.
Rules:
- Students will not see the passage, so never mention "the passage" or "the text".
- The question must end with a question mark.
- The answer must be 12 words or fewer, taken from the passage's own ideas.
- Do not repeat the question's words in the answer.""",
    "mcq": """Write one multiple-choice exam question about the passage.
Rules:
- Students will not see the passage, so never mention "the passage" or "the text".
- Give exactly four options: one correct, three plausible but wrong.
- Keep all four options about the same length, so the answer does not stand out.
- Write the wrong options in your own words, not copied from the passage.
- answer_index is the 0-based position of the correct option.""",
}

TASKS = {
    "short_answer": (ShortAnswerQuestion, short_answer_metric, short_answer_checks, 0),
    "mcq": (MultipleChoiceQuestion, mcq_metric, mcq_checks, 1),
}
