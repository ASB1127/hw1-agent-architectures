# A Bounded Agent for Bandit Alert Classification

COMS E6998-019 — Design of Production Agentic Systems  
Columbia University · Fall 2026

## Overview

This project implements a bounded, sequential reactive agent that investigates and classifies security alerts discovered by Bandit in pinned Python repositories.

The agent uses Bandit 1.9.4 with a minimum severity of MEDIUM, investigates alerts using read-only repository tools, and produces evidence-supported classifications under configurable token and step budgets.

Each run generates:

- `report.json` — alert classifications and supporting evidence.
- `trace.jsonl` — the agent's execution trace.

## 1. Prerequisites

- Python 3.12
- Git
- pip
- An OpenAI API key

On macOS:

```bash
brew install python@3.12
```

On **Ubuntu 24.04**, install Python 3.12 and virtual-environment support:

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv
```

On **Ubuntu 22.04**, add the Deadsnakes PPA to install Python 3.12:

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv
```

These Ubuntu commands are distribution-specific; other Linux distributions, including Debian, require their own Python 3.12 installation method. In all cases, `python3.12` must be available before proceeding.

## 2. Installation

Clone the agent repository:

```bash
git clone https://github.com/ASB1127/hw1-agent-architectures.git
cd hw1-agent-architectures
```

Create and activate a Python 3.12 virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify the required versions:

```bash
python --version
bandit --version
```

The expected versions are Python 3.12.x and Bandit 1.9.4.

## 3. Environment Variables

The agent uses the following environment variable:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Authenticates requests to the OpenAI model provider |

Create a local environment file:

```bash
cp .env.example .env
```

Edit `.env` to provide your API key, then export its variables:

```bash
set -a
source .env
set +a
```

Repeat the export commands in each new terminal session.

Never commit `.env` or API credentials.

## 4. Target Repositories

The agent is evaluated on three repositories at the exact commits specified in Section 3 of the assignment.

| Target | Required commit |
|---|---|
| Radicale | `eff8027f3dc4910be1659ee71f4b4a454ade5a8c` |
| SGLang | `bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2` |
| OWASP BenchmarkPython | `f1291485808b66e20ddb6b01b10dc71b3df8c8ba` |

### Clone the targets

From the agent repository root:

```bash
mkdir -p targets

git clone https://github.com/Kozea/Radicale.git targets/Radicale

git clone https://github.com/sgl-project/sglang.git targets/sglang

git clone https://github.com/OWASP-Benchmark/BenchmarkPython.git targets/BenchmarkPython
```

### Check out the required commits

```bash
git -C targets/Radicale checkout eff8027f3dc4910be1659ee71f4b4a454ade5a8c

git -C targets/sglang checkout bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2

git -C targets/BenchmarkPython checkout f1291485808b66e20ddb6b01b10dc71b3df8c8ba
```

### Verify the commits

```bash
git -C targets/Radicale rev-parse HEAD
git -C targets/sglang rev-parse HEAD
git -C targets/BenchmarkPython rev-parse HEAD
```

Expected output, in order:

```text
eff8027f3dc4910be1659ee71f4b4a454ade5a8c
bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2
f1291485808b66e20ddb6b01b10dc71b3df8c8ba
```

The agent reads these target repositories without modifying or executing their code.

## 5. Configuration

Two configuration files are required and included in the repository:

- `configs/full.toml` — full token budget for a complete run.
- `configs/low.toml` — reduced token budget designed to exhaust during the Radicale run.

Both files must validate against `config.schema.json` and initially contain the required Radicale `[scan]` block.

The required target-specific scan blocks are available in:

```text
briefs/scan/radicale.toml
briefs/scan/sglang.toml
briefs/scan/owasp-benchmark-python.toml
```

For SGLang or BenchmarkPython, replace only the `[scan]` block in the chosen configuration with the corresponding block above. Keep all other settings unchanged.

The agent enforces the configured token budget, per-call output allowance, and maximum execution steps.

## 6. Running the Agent

The command-line interface is:

```bash
python main.py \
  --input <TARGET_DIRECTORY> \
  --output <OUTPUT_DIRECTORY> \
  --config <CONFIG_FILE>
```

### Radicale — full budget

Using the default Radicale `[scan]` block:

```bash
python main.py \
  --input targets/Radicale \
  --output results/radicale-full \
  --config configs/full.toml
```

### Radicale — low budget

```bash
python main.py \
  --input targets/Radicale \
  --output results/radicale-low \
  --config configs/low.toml
```

The low-budget configuration is intended to produce at least one report row with status `budget_exhausted`.

### SGLang — full and low budgets

First, replace the `[scan]` block with the required SGLang block in both configurations.

```bash
python main.py \
  --input targets/sglang \
  --output results/sglang-full \
  --config configs/full.toml

python main.py \
  --input targets/sglang \
  --output results/sglang-low \
  --config configs/low.toml
```

### OWASP BenchmarkPython — full and low budgets

First, replace the `[scan]` block with the required OWASP BenchmarkPython block in both configurations.

```bash
python main.py \
  --input targets/BenchmarkPython \
  --output results/owasp-full \
  --config configs/full.toml

python main.py \
  --input targets/BenchmarkPython \
  --output results/owasp-low \
  --config configs/low.toml
```

Each run uses the target's pinned checkout and required scan scope.

## 7. Output Files

Each invocation writes the following files under the directory specified by `--output`:

```text
<OUTPUT_DIRECTORY>/
├── report.json
└── trace.jsonl
```

### report.json

Contains one row per discovered Bandit alert, including the classification, rationale, evidence, and processing status.

Classification values are:

- `1` — potential vulnerability.
- `0` — not a vulnerability.
- `null` — not classified.

The output must conform to `report.schema.json`.

### trace.jsonl

Records the agent's execution, including model interactions, tool calls, state transitions, budget usage, and termination.

The trace must conform to `trace.schema.json`.

## 8. Required Evaluation Runs

The assignment evaluates six runs:

| Target | Full budget | Low budget |
|---|---|---|
| Radicale | `configs/full.toml` | `configs/low.toml` |
| SGLang | `configs/full.toml` | `configs/low.toml` |
| OWASP BenchmarkPython | `configs/full.toml` | `configs/low.toml` |

For each target, the grader replaces the `[scan]` block while preserving the other configuration settings.

Every run must produce `report.json` and `trace.jsonl`. The Radicale low-budget run must demonstrate budget exhaustion.
