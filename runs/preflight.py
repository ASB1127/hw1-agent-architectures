from pathlib import Path
import subprocess

from config import load_config
from scan import Scan

CASES = [
    ("owasp", Path("targets/BenchmarkPython"), Path("runs/configs/owasp-full.toml"), 18,
     "f1291485808b66e20ddb6b01b10dc71b3df8c8ba"),
    ("radicale", Path("targets/Radicale"), Path("runs/configs/radicale-full.toml"), 10,
     "eff8027f3dc4910be1659ee71f4b4a454ade5a8c"),
    ("sglang", Path("targets/sglang"), Path("runs/configs/sglang-full.toml"), 21,
     "bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2"),
]

for name, target, config_path, expected_count, expected_commit in CASES:
    config = load_config(config_path, target)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=target, text=True
    ).strip()
    alerts = Scan(target).discover(config.scan)
    assert commit == expected_commit, (name, commit)
    assert len(alerts) == expected_count, (name, len(alerts))
    print(f"{name}: commit={commit} alerts={len(alerts)}")
