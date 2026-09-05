import csv
import os
from datetime import datetime

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from judge import judge_answer
from calibration_set import CALIBRATION_SET

# ---- Config ----
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "benchmark_results.csv")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

RUN2_START = datetime.fromisoformat("2026-08-18T10:11:00+00:00")
RUN2_END = datetime.fromisoformat("2026-08-18T10:22:00+00:00")

embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

MANUAL_TO_JUDGE_BUCKET = {
    "correct": "correct",
    "safe_miss": "correct_decline",
    "hallucinated": "hallucinated",
    "partial": "partial",
    "non_answer": "non_answer",
}


def get_context_for_question(question_text, k=3):
    chunks = db.similarity_search(question_text, k=k)
    return "\n\n".join(chunk.page_content for chunk in chunks)


def load_run2_rows(csv_path):
    rows_by_key = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = datetime.fromisoformat(row["timestamp"])
            if not (RUN2_START <= ts <= RUN2_END):
                continue
            key = (int(row["question_id"]), row["model_name"])
            rows_by_key[key] = row
    return rows_by_key


def check_agreement(entry, row, judge_category):
    """Returns True/False, with a special case for unanswerable questions: your manual
    "correct" label and the judge's "correct_decline" both describe the same outcome —
    the model correctly said the info wasn't there, which IS the expected answer for
    these specific questions. Without this, the comparison treats them as a mismatch
    purely because they're spelled differently."""
    manual_bucket = MANUAL_TO_JUDGE_BUCKET[entry["manual_label"]]

    if row["question_category"] == "unanswerable" and manual_bucket == "correct":
        return judge_category in ("correct", "correct_decline")

    return manual_bucket == judge_category


def main():
    print("Loading Run 2 rows from CSV...")
    rows_by_key = load_run2_rows(CSV_PATH)
    print(f"Found {len(rows_by_key)} Run 2 rows.\n")

    context_cache = {}

    agreements = 0
    comparable_total = 0
    disagreements = []
    parse_errors = 0
    uncomparable = []

    for entry in CALIBRATION_SET:
        key = (entry["question_id"], entry["model"])
        row = rows_by_key.get(key)

        if not row:
            print(f"WARNING: no CSV row found for {key} — skipping")
            continue

        if entry["question_id"] not in context_cache:
            context_cache[entry["question_id"]] = get_context_for_question(row["question"])
        context = context_cache[entry["question_id"]]

        result = judge_answer(
            question=row["question"],
            context=context,
            expected_answer=row["expected_answer"],
            answer=row["answer"],
        )

        if result["judge_parse_error"]:
            parse_errors += 1
            print(f"[Q{entry['question_id']:>2} / {entry['model']:<12}] PARSE ERROR: {result['judge_reasoning']}")
            continue

        manual_bucket = MANUAL_TO_JUDGE_BUCKET[entry["manual_label"]]
        judge_category = result["judge_category"]

        if manual_bucket in ("partial", "non_answer"):
            uncomparable.append({
                "question_id": entry["question_id"],
                "model": entry["model"],
                "manual_label": entry["manual_label"],
                "judge_category": judge_category,
                "judge_reasoning": result["judge_reasoning"],
            })
            print(f"[Q{entry['question_id']:>2} / {entry['model']:<12}] "
                  f"manual={entry['manual_label']:<13} judge={judge_category:<19} (uncomparable, not counted)")
            continue

        comparable_total += 1
        agree = check_agreement(entry, row, judge_category)
        if agree:
            agreements += 1
        else:
            disagreements.append({
                "question_id": entry["question_id"],
                "model": entry["model"],
                "manual_label": entry["manual_label"],
                "judge_category": judge_category,
                "judge_reasoning": result["judge_reasoning"],
            })

        print(f"[Q{entry['question_id']:>2} / {entry['model']:<12}] "
              f"manual={entry['manual_label']:<13} judge={judge_category:<19} "
              f"{'<-- DISAGREE' if not agree else ''}")

    print(f"\n{'='*60}")
    print(f"Agreement rate: {agreements}/{comparable_total} ({100*agreements/comparable_total:.1f}%)")
    print(f"Judge JSON parse errors: {parse_errors}/{len(CALIBRATION_SET)}")
    print(f"Uncomparable rows (partial/non_answer): {len(uncomparable)}")
    print(f"{'='*60}\n")

    if disagreements:
        print(f"Disagreements ({len(disagreements)}):\n")
        for d in disagreements:
            print(d)
            print()

    if uncomparable:
        print(f"Uncomparable rows, judge's take for reference ({len(uncomparable)}):\n")
        for u in uncomparable:
            print(u)
            print()


if __name__ == "__main__":
    main()