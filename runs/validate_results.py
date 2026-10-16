import json
import runpy
from pathlib import Path

validate_run = runpy.run_path("tests/test_trace_contract.py")["validate_run"]

for output in sorted((Path("runs") / "results").iterdir()):
    report_path = output / "report.json"
    trace_path = output / "trace.jsonl"
    if not report_path.is_file() or not trace_path.is_file():
        continue
    validate_run(trace_path, report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = [
        json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    statuses = {}
    labels = {"0": 0, "1": 0, "null": 0}
    rationales = {}
    for row in report["alerts"]:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
        labels["null" if row["label"] is None else str(row["label"])] += 1
        rationales[row["rationale"]] = rationales.get(row["rationale"], 0) + 1
    print(
        f"{output.name}: alerts={report['scan']['alert_count']} "
        f"tokens={report['budget']['used_tokens']} exhausted={report['budget']['exhausted']} "
        f"terminal={events[-1]['status']} statuses={statuses} labels={labels}"
    )
    for rationale, count in sorted(rationales.items(), key=lambda item: (-item[1], item[0])):
        print(f"  rationale[{count}]={rationale!r}")
