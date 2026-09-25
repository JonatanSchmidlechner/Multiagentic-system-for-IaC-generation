"""Run every requested model/method, then save the existing ablation JSON summary."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import subprocess
import sys

from openai import OpenAI
from true_mas.config import BASE_URL, API_KEY

METHODS = ["RAW", "RAG", "COT", "FSP", "multi-turn", "multi-agent", "true-MAS"]

def validate_models(models):
    """Check every requested model on the configured server before evaluation."""
    try:
        with OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=10, max_retries=0) as client:
            available = {item.id for item in client.models.list().data}
    except Exception as error:
        raise ValueError(f"Cannot check the model server list: {error}") from error
    missing = [model for model in models if model not in available]
    if missing:
        raise ValueError(f"Models unavailable on the configured server: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", required=True, help="Comma-separated model names")
    parser.add_argument("--methods", default="RAW", help=", ".join(METHODS))
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--experiment-id", help="Omit for a fresh experiment; supply an ID to resume")
    subset = parser.add_mutually_exclusive_group()
    subset.add_argument("--sampled", action="store_true", help="Use 10 tasks per difficulty level")
    subset.add_argument("--quick-test", action="store_true", help="Use the existing quick-test dataset (documented as 2 tasks)")
    args = parser.parse_args()
    models = list(dict.fromkeys(m.strip() for m in args.models.split(",")))
    methods = list(dict.fromkeys(m.strip() for m in args.methods.split(",")))
    invalid_methods = [method for method in methods if method not in METHODS]
    if invalid_methods:
        parser.error(f"Unknown methods: {', '.join(invalid_methods)}. Choose from: {', '.join(METHODS)}")
    if not all(models) or args.samples < 1:
        parser.error("Supply model names and a positive sample count")
    safe_models = [re.sub(r"[^\w.\-]", "_", model) for model in models]
    if any(m in (".", "..") for m in safe_models) or len(set(safe_models)) != len(models):
        parser.error("Model names must have distinct, safe directory names")
    experiment_id = args.experiment_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment_id):
        parser.error("Experiment ID must contain only letters, digits, underscores and hyphens")
    try:
        validate_models(models)
    except (ValueError, ImportError, KeyError) as error:
        parser.error(str(error))
    directory = Path(__file__).resolve().parent
    print(f"Experiment: {experiment_id}", flush=True)
    for model in models:
        for method in methods:
            command = [sys.executable, "eval.py", "--models", model,
                       "--samples", str(args.samples), "--experiment-id", experiment_id]
            if method != "RAW":
                command += ["--enhance-strat", method]
            if args.sampled:
                command.append("--sampled")
            if args.quick_test:
                command.append("--quick-test")
            subprocess.run(command, cwd=directory, check=True)
    subprocess.run([sys.executable, "misc/ablation/ablation-iac-eval-pipeline.py",
                    "--experiment-id", experiment_id], cwd=directory, check=True)


if __name__ == "__main__":
    main()
