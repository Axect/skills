# Remote Python Environment Setup with uv

This reference describes how to set up a Python environment on a Vast.ai instance using `uv` so that PyTorch automatically resolves to a CUDA build compatible with the rented GPU.

## Why uv (not pip or conda)

- **Automatic CUDA matching**: `uv pip install -U torch` queries your detected CUDA runtime and installs the correct PyTorch wheel (e.g., `2.11.0+cu130` for Blackwell sm_120 GPUs).
- **Isolated venvs per Python version**: `uv python install 3.13` provisions interpreters without touching system Python.
- **Fast**: ~10× faster than `pip` for large dependency trees.

## Standard Setup Pattern

Always do these five things, in order:

```bash
# 1. Install uv (once per instance)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

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
| Broken symlinks after rsync | Local repo has symlinks pointing at host paths | Use `rsync --copy-links` or strip symlinks via `--exclude` |
| `rsync: mkdir failed: File exists` | Destination is a broken symlink | `ssh ... 'rm <path> && mkdir -p <path>'` first |

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
