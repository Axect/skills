# Remote Python Environment Setup with uv

This reference describes how to set up a Python environment on a Vast.ai instance using `uv` so that PyTorch automatically resolves to a CUDA build compatible with the rented GPU.

## Why uv (not pip or conda)

- **Automatic CUDA matching**: `uv pip install -U torch` queries your detected CUDA runtime and installs the correct PyTorch wheel (e.g., `2.11.0+cu130` for Blackwell sm_120 GPUs).
- **Isolated venvs per Python version**: `uv python install 3.13` provisions interpreters without touching system Python.
- **Fast**: ~10× faster than `pip` for large dependency trees.

## Image choice: prefer a plain Ubuntu image

Rent with `--image ubuntu:22.04` (or similar minimal Ubuntu), NOT a `pytorch/pytorch:*` image. A pytorch image ships a torch+CUDA you will just override and tempts a `--index-url cuXY` pin that breaks on a different GPU arch; plain Ubuntu + `uv pip install -U torch` auto-resolves the right wheel for the actual GPU (cu124 Ampere, cu130 Blackwell — verified `2.12.0+cu130` on a 5060 Ti). **A bare Ubuntu image has none of `/workspace`, `rsync`, `curl`, `git`, `tmux`** — install them and create the workspace dir FIRST (Step 0 below), or rsync fails with "code 11 / mkdir failed: File exists" and `uv`/`tmux` are missing.

## Standard Setup Pattern

Always do these, in order:

```bash
# 0. Bare-Ubuntu prerequisites (a fresh ubuntu:22.04 lacks all of these)
apt-get update -qq && apt-get install -y -qq rsync curl git build-essential tmux
mkdir -p /workspace/<project>

# 1. Install uv (once per instance)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
# (if PATH is unreliable in non-interactive ssh, force a known on-PATH location:
#  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh )

# 2. Install a Python interpreter (pick one: 3.12, 3.13)
uv python install 3.13

# 3. Create a fresh venv (always rm -rf the old one — never reuse)
cd /workspace/<project>
rm -rf .venv
uv venv --python 3.13

# 4. Activate and install deps (uv picks CUDA-correct torch automatically)
source .venv/bin/activate
uv pip install -U torch <other deps...>

# 5. Verify GPU works
python -c "import torch; x=torch.randn(3,3,device='cuda'); print('ok:', (x@x).sum().item())"
```

## Critical Warnings

### 1. Modern GPUs need recent PyTorch

Blackwell (RTX 5070/5080/5090, sm_120) requires **PyTorch 2.7+** with **CUDA 12.8+** or CUDA 13.x.
- Symptom of mismatch: `CUDA error: no kernel image is available for execution on the device`
- PyTorch warning: `CUDA capability sm_120 is not compatible with the current PyTorch installation`

**Fix**: Let `uv pip install -U torch` pick the latest — do NOT pin `--index-url .../cu124` unless you know the GPU supports sm_90 or lower.

### 2. Fresh venv every time

Never reuse an existing `.venv` when switching Python versions or GPU architectures. Always `rm -rf .venv` first, then `uv venv --python <version>`. Mixing Python versions in one venv breaks obscurely.

### 3. PATH export is not persistent

`uv` installer puts binaries in `~/.local/bin/`. This is NOT on PATH in fresh SSH sessions.
- Add `export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"` to every remote script
- Or append it to `~/.bashrc` on the instance

### 4. Container CUDA version vs GPU driver

The Docker image's CUDA version (e.g., `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel`) is mostly irrelevant — what matters is:
- The **GPU driver version** on the host (shown in `nvidia-smi`)
- The **PyTorch wheel's CUDA version** (must be ≤ driver's max supported)

A CUDA 12.4 container can run a PyTorch 2.11+cu130 wheel as long as the host driver supports CUDA 13.

### 5. uv can install a torch NEWER than the host driver supports (silent cuda=False)

`uv pip install -U torch` always grabs the LATEST wheel (currently `2.12.0+cu130`, CUDA 13). On a host whose driver only supports CUDA 12.8 (e.g. driver 570.x), that cu130 wheel installs fine but `torch.cuda.is_available()` returns **False** at runtime (no forward-compat across the CUDA major). The runtime error is `The NVIDIA driver on your system is too old (found version 12080)`.

So "Ubuntu + uv auto-resolves torch" is NOT fully safe by itself. Two guards:
- **Before renting**, prefer offers whose `cuda_max_good >= 13` if you want the latest cu13x torch. Hosts with new drivers (e.g. 590.x, `cuda_max_good 13.1`) run cu130 cleanly; older 12.8 hosts do not.
- **After install, ALWAYS verify** `python -c "import torch; print(torch.cuda.is_available())"`. If it prints False, check `nvidia-smi` "CUDA Version" (the driver's max) and pin torch DOWN to match that EXACT version, not a blanket cu128: a driver showing CUDA 12.4 needs `--index-url .../cu124`, CUDA 12.8 needs `cu128`, CUDA 13.x runs `cu130`. cu128 is NOT universal: it is too new for a 12.4 driver (gives `driver too old, found version 12040`). So read the driver's CUDA version first, then `uv pip install torch --index-url https://download.pytorch.org/whl/cu<XYZ>` matching it. This is the ONE case where a torch pin is correct (pinning DOWN to the driver).

**The re-break trap:** if you pin DOWN to cu128, do NOT relaunch via a script that re-runs your bootstrap/`install_requirements.sh` (whose `uv pip install -U torch` will re-fetch cu130 and re-break it). Launch a bootstrap-free training loop (`source .venv/bin/activate` + `python main.py ...`, no `-U torch`) so torch is never upgraded back.

### 6. Launching a long remote job robustly (logging + process control)

Common failures when starting a detached training run over SSH:
- `tmux new-session -d "cmd > log"` puts `log` in the LAUNCHER's CWD (often `~`), not the script's post-`cd` directory, and the tmux server sometimes does not persist in a bare container, so the session vanishes and you cannot find the log.
- `pkill -f <pattern>` / `pgrep -f <pattern>` run over SSH **self-match the command string** (the remote shell's argv contains your pattern), so `pkill -9 -f remote_sweep` kills its own wrapper before reaching the relaunch, and `pgrep -fc` returns N+1.

Robust recipe:
- Have the script write its OWN log via an absolute path right after `cd`: `exec > /workspace/<proj>/train.log 2>&1`. Then external redirection cannot misplace it.
- Launch with `setsid bash script.sh </dev/null >/dev/null 2>&1 &` (survives SSH exit without depending on tmux).
- To find/kill the old process without self-matching, use the bracket trick: `ps -eo pid,args | grep "[r]emote_sweep" | awk '{print $1}'` then `kill -9 <pid>`. For the definitive trainer count use `nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l` (immune to self-match).
- git-untracked config/data files do NOT rsync unless named explicitly. A missing config makes the trainer exit in <1s (FileNotFoundError before torch import, `cputime=00:00:00`), which a relaunch loop turns into a crash-loop that LOOKS like a GPU/torch failure. Verify configs exist on the remote with an ABSOLUTE path before launching, and `rsync` untracked files by name.

## Full Setup Script Template

```bash
#!/bin/bash
set -e
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Install uv if missing
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Project setup
cd /workspace/<project>
rm -rf .venv
uv python install 3.13
uv venv --python 3.13
source .venv/bin/activate

# Install deps — uv picks CUDA-correct torch automatically
uv pip install -U torch wandb optuna matplotlib numpy scipy scikit-learn \
    <your other deps...>

# Verify
python -c "import torch; print('torch:', torch.__version__); \
    print('cuda:', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Copy this to the instance and run it via `ssh -p <port> root@<host> 'bash /root/setup.sh'`.

## Common Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` in SSH | PATH not set in non-interactive shell | Explicit `export PATH=...` in every script |
| `CUDA capability sm_XXX not supported` | Old PyTorch on new GPU | `uv pip install -U torch` (no index-url pin) |
| `No CUDA GPUs are available` | Wrong container or driver issue | Check `nvidia-smi` on the host; recreate instance |
| Broken symlinks after rsync | Local repo has a symlinked dir (e.g. `runs -> ~/Dropbox/...`) pointing at a host path absent on the instance | Exclude it with BOTH the bare name AND trailing-slash form: `--exclude='runs' --exclude='runs/'` (a trailing-slash-only pattern won't match the symlink itself); or `rsync --copy-links` to follow it |
| `rsync: mkdir failed: File exists` | Destination is a broken symlink | `ssh ... 'rm <path> && mkdir -p <path>'` first |
| `ModuleNotFoundError` mid-batch (job 24 of 30 dies) | Late-bound import (`from X import Y` inside function body) not in `requirements.txt` | Always smoke-test ONE end-to-end run per script type BEFORE queuing the batch — see "Pre-flight dependency smoke test" below |

## Pre-flight Dependency Smoke Test

**Before queuing N jobs via pueue or any dep-chain runner, run ONE complete invocation of each distinct script type and let it finish.** This catches late-bound imports that `requirements.txt` omits.

The failure mode: a script that does `import torch` at module top but `from scipy.optimize import curve_fit` inside `fit_oz_full_correlator()` will pass `python -c "import script"`, get queued 30 times, run 24 jobs successfully, then die on job 25 when the fit code path first fires — cascading-failing all dependents.

Recommended workflow:

```bash
# After remote_setup.sh finishes — BEFORE queuing the batch:

# Step A: Module-level import check (cheap)
cd ~/<project>
source .venv/bin/activate
python -c "$(grep -hE '^(import |from .* import )' \
    analyze_*.py evaluate_*.py main.py | sort -u)" 2>&1 \
    | grep -i 'no module' && { echo "MISSING DEPS"; exit 1; }

# Step B: Smoke-test ONE quick invocation per distinct script type
# Use minimal --batch_size / --n_T to finish in seconds-to-minutes
python evaluate_model_thermo.py --project P --group G --seed 42 \
    --batch_size 8 --n_batches 1 --device cuda:0 --output /tmp/smoke_thermo.csv
python analyze_correlation_clock.py --seed 42 --device cuda:0 \
    --models Clock_w8 --n_T 4 --n_samples 100 --output /tmp/smoke_clock.csv
# ... etc for each entry-point script

# Step C: ONLY after all smokes pass, queue the full batch via pueue
```

If any smoke fails with `ModuleNotFoundError`, install the missing dep on the remote venv (`uv pip install <dep>`) and retry the smoke before queuing.

**Cost-saving tip**: Build a `python-deps-check.sh` that runs Step A + the smoke commands, save it in your project repo, and run it as the LAST line of remote setup. Setup script exits non-zero on missing deps → instance is set up but you stop before queuing → fix and retry quickly.

## Project Data Transfer

Two typical patterns:

**Small project + model + data (< 1 GB total)**:
```bash
rsync -avz -e 'ssh -p <port>' \
  --exclude='.venv' --exclude='wandb' --exclude='__pycache__' \
  <local_dir>/ root@<host>:/workspace/<project>/
```

**Large dataset (> 10 GB)**: Use `vastai cloud copy` from S3/GCS instead of rsync — saves bandwidth.

## Cleanup

Always destroy the instance when done (storage is billed even when stopped):
```bash
vastai destroy instance <ID>
```
