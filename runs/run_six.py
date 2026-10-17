#!/usr/bin/env python3
"""Run or preflight the six HW1 target/configuration combinations.

Each completed run is saved under runs/evaluation/<target>-<budget>/ with the
exact generated config.toml beside report.json and trace.jsonl.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VENV_BIN = ROOT / ".venv" / "bin"
if VENV_BIN.is_dir():
    os.environ["PATH"] = f"{VENV_BIN}{os.pathsep}{os.environ['PATH']}"
PROJECT_PYTHON = str(VENV_BIN / "python") if (VENV_BIN / "python").is_file() else sys.executable

from config import load_config
from scan import Scan


@dataclass(frozen=True)
class RunCase:
    name: str
    target: Path
    budget: str
    scan_block: Path
    expected_alerts: int
    expected_commit: str


CASES = (
    RunCase(
        "radicale-full",
        ROOT / "targets" / "Radicale",
        "full",
        ROOT / "briefs" / "scan" / "radicale.toml",
        10,
        "eff8027f3dc4910be1659ee71f4b4a454ade5a8c",
    ),
    RunCase(
        "radicale-low",
        ROOT / "targets" / "Radicale",
        "low",
        ROOT / "briefs" / "scan" / "radicale.toml",
        10,
        "eff8027f3dc4910be1659ee71f4b4a454ade5a8c",
    ),
    RunCase(
        "sglang-full",
        ROOT / "targets" / "sglang",
        "full",
        ROOT / "briefs" / "scan" / "sglang.toml",
        21,
        "bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2",
    ),
    RunCase(
        "sglang-low",
        ROOT / "targets" / "sglang",
        "low",
        ROOT / "briefs" / "scan" / "sglang.toml",
        21,
        "bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2",
    ),
    RunCase(
        "owasp-full",
        ROOT / "targets" / "BenchmarkPython",
        "full",
        ROOT / "briefs" / "scan" / "owasp-benchmark-python.toml",
        18,
        "f1291485808b66e20ddb6b01b10dc71b3df8c8ba",
    ),
    RunCase(
        "owasp-low",
        ROOT / "targets" / "BenchmarkPython",
        "low",
        ROOT / "briefs" / "scan" / "owasp-benchmark-python.toml",
        18,
        "f1291485808b66e20ddb6b01b10dc71b3df8c8ba",
    ),
)


def config_without_scan(path: Path) -> str:
    """Return the canonical config with its top-level [scan] table removed."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == "[scan]"), None)
    if start is None:
        raise ValueError(f"{path} has no [scan] table")
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("[")),
        len(lines),
    )
    return "".join([*lines[:start], *lines[end:]]).lstrip("\n")


def generated_config(case: RunCase) -> str:
    base = ROOT / "configs" / f"{case.budget}.toml"
    scan = case.scan_block.read_text(encoding="utf-8").rstrip()
    return f"{scan}\n\n{config_without_scan(base)}"


def verify_target(case: RunCase, config_path: Path) -> int:
    if not case.target.is_dir():
        raise RuntimeError(f"{case.name}: target is missing: {case.target}")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=case.target, text=True
    ).strip()
    if commit != case.expected_commit:
        raise RuntimeError(
            f"{case.name}: expected pinned commit {case.expected_commit}, got {commit}"
        )
    config = load_config(config_path, case.target)
    alerts = Scan(case.target).discover(config.scan)
    if len(alerts) != case.expected_alerts:
        raise RuntimeError(
            f"{case.name}: expected {case.expected_alerts} Bandit alerts, got {len(alerts)}"
        )
    return len(alerts)


def run_case(case: RunCase, output_root: Path, dry_run: bool, force: bool) -> None:
    output = output_root / case.name
    config_path = output / "config.toml"
    config_text = generated_config(case)

    if output.exists():
        if not force:
            raise RuntimeError(
                f"{case.name}: output already exists at {output}; use --force to replace it"
            )
        if not dry_run:
            shutil.rmtree(output)

    if dry_run:
        with tempfile.TemporaryDirectory(prefix=f"hw1-{case.name}-") as temporary:
            scratch_config = Path(temporary) / "config.toml"
            scratch_config.write_text(config_text, encoding="utf-8")
            alert_count = verify_target(case, scratch_config)
        print(f"OK {case.name}: {alert_count} alerts; would write {output}")
        return

    output.mkdir(parents=True)
    config_path.write_text(config_text, encoding="utf-8")
    alert_count = verify_target(case, config_path)
    print(f"RUN {case.name}: {alert_count} alerts -> {output}", flush=True)
    completed = subprocess.run(
        [
            PROJECT_PYTHON,
            "main.py",
            "--input",
            str(case.target),
            "--output",
            str(output),
            "--config",
            str(config_path),
        ],
        cwd=ROOT,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{case.name}: agent exited {completed.returncode}; retained {output} for inspection"
        )
    missing = [name for name in ("report.json", "trace.jsonl", "config.toml") if not (output / name).is_file()]
    if missing:
        raise RuntimeError(f"{case.name}: missing expected artifacts: {', '.join(missing)}")
    print(f"DONE {case.name}: report.json, trace.jsonl, config.toml", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        choices=[case.name for case in CASES],
        help="Run one named case; repeat this option for multiple cases.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check target commits, scan scopes, and expected alert counts without model calls.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing case output directory (ignored by --dry-run).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "runs" / "evaluation",
        help="Directory that receives the six preserved run artifacts.",
    )
    args = parser.parse_args()

    selected = [case for case in CASES if not args.only or case.name in args.only]
    for case in selected:
        run_case(case, args.output_root.resolve(), args.dry_run, args.force)


if __name__ == "__main__":
    main()
