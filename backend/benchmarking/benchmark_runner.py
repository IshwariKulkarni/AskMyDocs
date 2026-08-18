import requests
import json
import csv
import time
from datetime import datetime, timezone
import psutil
import os

# ---- Configuration ----
API_URL = "http://127.0.0.1:8000/ask"
QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "benchmark_questions.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "benchmark_results.csv")

MODELS = ["phi3", "llama3.2:3b", "qwen2.5:3b"]
RUNS_PER_QUESTION = 1  

CSV_FIELDS = [
    "run_id", "timestamp", "model_name", "question_id", "question_category",
    "question", "expected_answer", "answer",
    "total_duration_ms", "load_duration_ms", "prompt_eval_duration_ms",
    "generation_duration_ms", "prompt_tokens", "output_tokens",
    "tokens_per_second", "is_cold_start",
    "ram_before_mb", "peak_ram_mb", "ram_after_mb", "ram_delta_mb",
    "system_ram_percent_used", "error"
]


def load_questions(limit=None):
    with open(QUESTIONS_PATH, "r") as f:
        questions = json.load(f)
    return questions[:limit] if limit else questions


def call_ask_endpoint(question_text, model_name):
    try:
        response = requests.post(
            API_URL,
            json={"question": question_text, "model": model_name},
            timeout=180 
        )
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


def run_benchmark(questions, models, runs_per_question):
    results = []
    run_id = 0

    for model_name in models:
        print(f"\n{'='*50}\nMODEL: {model_name}\n{'='*50}")

        for q in questions:
            for run_num in range(1, runs_per_question + 1):
                run_id += 1
                print(f"[{run_id}] {model_name} | Q{q['id']} ({q['category']}) | run {run_num}...")

                start_time = time.time()
                data, error = call_ask_endpoint(q["question"], model_name)
                elapsed = time.time() - start_time

                system_ram_percent = psutil.virtual_memory().percent

                if error:
                    print(f"    ERROR: {error}")
                    row = {field: "" for field in CSV_FIELDS}
                    row.update({
                        "run_id": run_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "model_name": model_name,
                        "question_id": q["id"],
                        "question_category": q["category"],
                        "question": q["question"],
                        "expected_answer": q.get("expected_answer", ""),
                        "system_ram_percent_used": system_ram_percent,
                        "error": error
                    })
                    results.append(row)
                    continue

                metrics = data.get("metrics", {})
                resources = data.get("resources", {})

                row = {
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "model_name": model_name,
                    "question_id": q["id"],
                    "question_category": q["category"],
                    "question": q["question"],
                    "expected_answer": q.get("expected_answer", ""),
                    "answer": data.get("answer", ""),
                    "total_duration_ms": metrics.get("total_duration_ms"),
                    "load_duration_ms": metrics.get("load_duration_ms"),
                    "prompt_eval_duration_ms": metrics.get("prompt_eval_duration_ms"),
                    "generation_duration_ms": metrics.get("generation_duration_ms"),
                    "prompt_tokens": metrics.get("prompt_tokens"),
                    "output_tokens": metrics.get("output_tokens"),
                    "tokens_per_second": metrics.get("tokens_per_second"),
                    "is_cold_start": metrics.get("is_cold_start"),
                    "ram_before_mb": resources.get("ram_before_mb"),
                    "peak_ram_mb": resources.get("peak_ram_mb"),
                    "ram_after_mb": resources.get("ram_after_mb"),
                    "ram_delta_mb": resources.get("ram_delta_mb"),
                    "system_ram_percent_used": system_ram_percent,
                    "error": ""
                }
                results.append(row)
                print(f"    OK — {elapsed:.1f}s wall clock, "
                      f"{metrics.get('tokens_per_second', '?')} tok/s, "
                      f"cold={metrics.get('is_cold_start')}")

    return results


def save_results(results, path):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved {len(results)} rows to {path}")


if __name__ == "__main__":
    questions = load_questions()
    models_to_test = ["phi3", "llama3.2:3b", "qwen2.5:3b"]

    results = run_benchmark(questions, models_to_test, runs_per_question=1)
    save_results(results, RESULTS_PATH)