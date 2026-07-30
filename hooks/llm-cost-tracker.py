#!/usr/bin/env python3
"""
LLM Cost Tracker — parses Claude Code session files and reports per-project costs.
Designed to run in the background (non-blocking).
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Import config from ~/scripts
import sys
sys.path.insert(0, str(Path.home() / "scripts"))
from llm_cost_tracker_config import PRICING, PROJECT_NAMES, BASE_PREFIX

PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUTPUT_DIR   = Path.home() / "plans" / "llm-cost-tracker"
COSTS_MD     = OUTPUT_DIR / "costs.md"
COSTS_JSON   = OUTPUT_DIR / "costs.json"


def get_project_name(dir_name: str) -> str:
    if dir_name in PROJECT_NAMES:
        return PROJECT_NAMES[dir_name]
    if dir_name.startswith(BASE_PREFIX):
        return dir_name[len(BASE_PREFIX):]
    return dir_name


def get_price(model: str, token_type: str) -> float:
    pricing = PRICING.get(model) or PRICING.get("default")
    return pricing.get(token_type, 0.0)


def compute_cost(model: str, usage: dict) -> float:
    input_tokens       = usage.get("input_tokens", 0)
    output_tokens      = usage.get("output_tokens", 0)
    cache_write_tokens = usage.get("cache_creation_input_tokens", 0)
    cache_read_tokens  = usage.get("cache_read_input_tokens", 0)

    cost = (
        input_tokens       * get_price(model, "input") +
        output_tokens      * get_price(model, "output") +
        cache_write_tokens * get_price(model, "cache_write") +
        cache_read_tokens  * get_price(model, "cache_read")
    ) / 1_000_000

    return cost


def parse_projects():
    results = defaultdict(lambda: defaultdict(lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_write_tokens": 0,
        "cache_read_tokens": 0,
        "cost_usd": 0.0,
        "message_count": 0,
    }))

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        slug = project_dir.name
        project_name = get_project_name(slug)

        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                with open(jsonl_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if record.get("type") != "assistant":
                            continue

                        msg = record.get("message", {})
                        if not isinstance(msg, dict):
                            continue

                        usage = msg.get("usage")
                        model = msg.get("model", "")
                        if not usage or not model or model == "<synthetic>":
                            continue

                        cost = compute_cost(model, usage)
                        bucket = results[project_name][model]
                        bucket["input_tokens"]       += usage.get("input_tokens", 0)
                        bucket["output_tokens"]       += usage.get("output_tokens", 0)
                        bucket["cache_write_tokens"]  += usage.get("cache_creation_input_tokens", 0)
                        bucket["cache_read_tokens"]   += usage.get("cache_read_input_tokens", 0)
                        bucket["cost_usd"]            += cost
                        bucket["message_count"]       += 1

            except (OSError, PermissionError):
                continue

    return results


def format_num(n: int) -> str:
    return f"{n:,}"


def format_cost(c: float) -> str:
    return f"${c:.4f}"


def write_markdown(results: dict, timestamp: str):
    lines = [
        "# LLM Cost Report",
        f"_Last updated: {timestamp}_",
        "",
    ]

    lines += ["## By Project", ""]
    lines += ["| Project | Messages | Input | Output | Cache Read | Cache Write | Est. Cost |"]
    lines += ["|---------|----------|-------|--------|------------|-------------|-----------|"]

    grand_total = 0.0
    project_rows = []

    for project, models in sorted(results.items()):
        totals = {
            "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "cost_usd": 0.0, "message_count": 0,
        }
        for model_data in models.values():
            for k in totals:
                totals[k] += model_data[k]

        grand_total += totals["cost_usd"]
        project_rows.append((project, totals))

        lines.append(
            f"| **{project}** "
            f"| {format_num(totals['message_count'])} "
            f"| {format_num(totals['input_tokens'])} "
            f"| {format_num(totals['output_tokens'])} "
            f"| {format_num(totals['cache_read_tokens'])} "
            f"| {format_num(totals['cache_write_tokens'])} "
            f"| **{format_cost(totals['cost_usd'])}** |"
        )
        for model, data in sorted(models.items(), key=lambda x: -x[1]["cost_usd"]):
            lines.append(
                f"| &nbsp;&nbsp;↳ {model} "
                f"| {format_num(data['message_count'])} "
                f"| {format_num(data['input_tokens'])} "
                f"| {format_num(data['output_tokens'])} "
                f"| {format_num(data['cache_read_tokens'])} "
                f"| {format_num(data['cache_write_tokens'])} "
                f"| {format_cost(data['cost_usd'])} |"
            )

    all_totals = {k: sum(r[k] for _, r in project_rows) for k in
                  ["message_count", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"]}
    lines.append(
        f"| **TOTAL** "
        f"| **{format_num(all_totals['message_count'])}** "
        f"| **{format_num(all_totals['input_tokens'])}** "
        f"| **{format_num(all_totals['output_tokens'])}** "
        f"| **{format_num(all_totals['cache_read_tokens'])}** "
        f"| **{format_num(all_totals['cache_write_tokens'])}** "
        f"| **{format_cost(grand_total)}** |"
    )

    lines += ["", "## By Model (all projects)", ""]
    lines += ["| Model | Messages | Est. Cost |"]
    lines += ["|-------|----------|-----------|"]

    model_totals = defaultdict(lambda: {"cost_usd": 0.0, "message_count": 0})
    for models in results.values():
        for model, data in models.items():
            model_totals[model]["cost_usd"]      += data["cost_usd"]
            model_totals[model]["message_count"] += data["message_count"]

    for model, data in sorted(model_totals.items(), key=lambda x: -x[1]["cost_usd"]):
        lines.append(f"| {model} | {format_num(data['message_count'])} | {format_cost(data['cost_usd'])} |")

    lines += ["", "---", f"_Generated by `~/plans/llm-cost-tracker/tracker.py`_", ""]

    COSTS_MD.write_text("\n".join(lines))


def write_json(results: dict, timestamp: str):
    output = {
        "generated_at": timestamp,
        "projects": {},
        "models": {},
        "grand_total_usd": 0.0,
    }

    for project, models in results.items():
        proj_total = 0.0
        output["projects"][project] = {}
        for model, data in models.items():
            output["projects"][project][model] = data
            proj_total += data["cost_usd"]

            if model not in output["models"]:
                output["models"][model] = {"cost_usd": 0.0, "message_count": 0}
            output["models"][model]["cost_usd"]      += data["cost_usd"]
            output["models"][model]["message_count"] += data["message_count"]

        output["projects"][project]["_total_cost_usd"] = proj_total
        output["grand_total_usd"] += proj_total

    COSTS_JSON.write_text(json.dumps(output, indent=2))


def print_table(results: dict):
    from tabulate import tabulate
    cols = ["Model", "Msgs", "Input", "Output", "Cache Read", "Cache Write", "Est. Cost"]
    grand_total = 0.0

    for project, models in sorted(results.items()):
        proj_total = sum(d["cost_usd"] for d in models.values())
        grand_total += proj_total
        rows = []
        for model, d in sorted(models.items(), key=lambda x: -x[1]["cost_usd"]):
            rows.append([
                model,
                f"{d['message_count']:,}",
                f"{d['input_tokens']:,}",
                f"{d['output_tokens']:,}",
                f"{d['cache_read_tokens']:,}",
                f"{d['cache_write_tokens']:,}",
                f"${d['cost_usd']:.4f}",
            ])
        rows.append(["Subtotal", "", "", "", "", "", f"${proj_total:.4f}"])
        print(f"\n  {project}")
        print(tabulate(rows, headers=cols, tablefmt="simple_grid", colalign=("left","right","right","right","right","right","right")))

    print(f"\n  Grand Total: ${grand_total:.4f}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LLM Cost Tracker")
    parser.add_argument("--table", action="store_true", help="Print formatted table to terminal")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = parse_projects()
    write_markdown(results, timestamp)
    write_json(results, timestamp)

    if args.table:
        print_table(results)


if __name__ == "__main__":
    main()
