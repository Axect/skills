---
name: vastai
description: Manage Vast.ai GPU cloud instances via the vastai CLI. Use this skill whenever the user mentions Vast.ai, GPU rentals, cloud GPU instances, searching for GPU offers, creating/destroying instances, vast.ai billing, or any task involving the vastai command-line tool. Also trigger when the user wants to rent GPUs, find cheap GPUs, deploy Docker containers on remote GPUs, manage remote training infrastructure, or transfer data to/from cloud GPU machines. Even if the user just says "spin up a GPU" or "find me an A100", this skill likely applies.
---

# Vast.ai CLI Skill

This skill helps you use the `vastai` CLI to manage GPU cloud resources on the Vast.ai marketplace. Vast.ai is an open marketplace for GPU compute — you can search for available machines, rent them, deploy Docker containers, transfer data, and manage billing, all from the command line.

## Prerequisites

- **Install**: `pip install vastai` (or `uv pip install vastai`)
- **Authenticate**: Get your API key from https://cloud.vast.ai/cli/ then run:
  ```bash
  vastai set api-key YOUR_API_KEY
  ```
  The key is stored at `~/.vast_api_key`. Never share API keys.

## Core Workflow

The typical workflow is: **Search** -> **Create** -> **Use** -> **Destroy**.

### 1. Search for GPU Offers

```bash
vastai search offers '<query>' -o '<sort_field>'
```

The query uses a simple `field operator value` syntax. Multiple conditions are space-separated (implicit AND).

**Operators**: `>`, `>=`, `<`, `<=`, `=`, `!=`

**Common examples:**

```bash
# Find RTX 4090 machines with 99%+ reliability
vastai search offers 'gpu_name=RTX_4090 reliability>0.99 num_gpus=1'

# Find multi-GPU A100 setups, sorted by price
vastai search offers 'gpu_name=A100_SXM4 num_gpus>=4 reliability>0.98' -o 'dph'

# Find any GPU with 24GB+ VRAM under $0.50/hr
vastai search offers 'gpu_ram>=24 dph<0.5 reliability>0.95' -o 'dph'

# Datacenter-only machines with fast internet
vastai search offers 'datacenter=true inet_down>500 inet_up>500'
```

**Key search fields** (see `references/search-fields.md` for full list):

| Field | Description |
|---|---|
| `gpu_name` | GPU model (use underscores: `RTX_4090`, `A100_SXM4`) |
| `num_gpus` | Number of GPUs |
| `gpu_ram` | Per-GPU VRAM in GB |
| `gpu_total_ram` | Total VRAM across all GPUs |
| `cpu_cores` | vCPU count |
| `cpu_ram` | System RAM in GB |
| `disk_space` | Available storage in GB |
| `dph` | Cost per hour ($/hr) |
| `reliability` | Machine reliability score (0-1) |
| `cuda_vers` | Max supported CUDA version |
| `compute_cap` | CUDA compute capability (e.g., 800 = 8.0) |
| `inet_down` / `inet_up` | Network speed in Mb/s |
| `datacenter` | Datacenter-only flag (true/false) |
| `dlperf` | Deep learning performance score |
| `total_flops` | Combined GPU TFLOPs |
| `rentable` | Currently available |
| `static_ip` | Has stable IP |
| `verified` | Verification status |

**Sorting**: Use `-o 'field'` for ascending, `-o 'field-'` for descending.

**Pricing type**: Add `-d` (on-demand), `-b` (bid/spot), or `-r` (reserved).

**Before renting for multi-day work, always check the `Max_Days` column** in the formatted search output (far right of the price row). This is the host's committed contract length — when it elapses, vast.ai terminates your container regardless of training state. See `references/search-fields.md` for details on reading/parsing `Max_Days` and the 1.5× duration rule.

### 2. Create an Instance

```bash
vastai create instance OFFER_ID --image IMAGE --disk DISK_GB [OPTIONS]
```

**Key options:**
- `--image IMAGE`: Docker image (e.g., `pytorch/pytorch:latest`, `vastai/tensorflow`)
- `--disk DISK_GB`: Local disk size in GB
- `--ssh`: Enable SSH access
- `--jupyter`: Enable Jupyter access
- `--direct`: Direct connection (vs proxied)
- `--onstart SCRIPT`: Startup script filename
- `--label LABEL`: Human-readable label
- `--env ENV`: Environment variables and port mappings
- `--price PRICE`: Bid price for spot instances ($/hr)

**Example:**
```bash
# Rent offer 2459368 with PyTorch, 50GB disk, SSH access
vastai create instance 2459368 --image pytorch/pytorch:latest --disk 50 --ssh --direct
```

Billing starts immediately for storage; GPU billing starts once the instance reaches "running" state.

### 3. Manage Instances

```bash
# List your instances
vastai show instances

# View specific instance details
vastai show instance ID

# Get SSH connection string
vastai ssh-url ID

# View logs
vastai logs ID --tail 100

# Stop (preserves data, stops GPU billing)
vastai stop instance ID

# Start a stopped instance
vastai start instance ID

# Reboot without losing GPU priority
vastai reboot instance ID

# Label for easy identification
vastai label instance ID "my-training-run"
```

### 4. Transfer Data

```bash
# Copy local file to instance
vastai copy local_file instance_id:/path/on/instance

# Copy from instance to local
vastai copy instance_id:/path/on/instance local_destination

# Cloud storage transfers
vastai cloud copy --src cloud_service:path --dst instance_id:/path --transfer "Cloud To Instance"
```

**Warning**: Never copy to `/root` or `/` as destination — this corrupts SSH permissions.

### 5. Destroy When Done

```bash
# Destroy single instance (irreversible!)
vastai destroy instance ID -y

# Destroy multiple
vastai destroy instances ID1 ID2 ID3 -y
```

`vastai destroy instance` prompts `Are you sure...? [y/N]` on stdin and aborts if not attached to a TTY (piping `yes` does not work — it reads from the terminal). **Always pass `-y` (or `--yes`) from non-interactive contexts** such as Claude tool calls, scripts, or CI.

Always destroy instances when done to stop storage charges.

## Setting up Python on a Fresh Instance

For any GPU work on a rented instance, use `uv` to set up Python — it auto-resolves the CUDA-correct PyTorch wheel for the GPU architecture. **Always read `references/python-setup.md` before writing a setup script**, especially when:
- Using Blackwell GPUs (RTX 5070/5080/5090) — needs PyTorch 2.7+ with CUDA 12.8+
- Installing PyTorch — never pin `--index-url` unless you know the target sm_ version
- Switching Python versions in an existing venv

Minimal pattern:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
cd /workspace/<project>
rm -rf .venv
uv python install 3.13
uv venv --python 3.13
source .venv/bin/activate
uv pip install -U torch <other deps>   # CUDA wheel auto-picked
```

## Additional Features

For detailed documentation on these topics, read the corresponding reference file:

- **Python/uv setup on remote instances**: `references/python-setup.md`
- **Instance management** (stop/start/reboot/recycle/update, labels, SSH, logs, execute): `references/instances.md`
- **Search fields & query syntax**: `references/search-fields.md`
- **Volumes** (persistent storage): `references/volumes.md`
- **Autoscaling & Endpoints** (serverless GPU): `references/autoscaling.md`
- **Hosting** (list your own machines): `references/hosting.md`
- **Billing & Account** (invoices, credits, teams): `references/billing.md`

## Quick Reference

```bash
# Check account balance
vastai show user

# Get help on any command
vastai COMMAND --help

# Output raw JSON (for scripting)
vastai show instances --raw

# Show the equivalent curl command
vastai search offers 'gpu_name=RTX_4090' --curl
```

## Common Patterns

**Find the cheapest GPU for a given task:**
```bash
vastai search offers 'gpu_ram>=24 reliability>0.98 inet_down>200' -o 'dph'
```

**Deploy a training job:**
```bash
# 1. Find an offer — inspect Max_Days from formatted output
vastai search offers 'gpu_name=A100_SXM4 num_gpus=1 reliability>0.99' -o 'dph'

# 1a. CRITICAL for jobs > 24h: verify Max_Days >= 1.5 × expected_hours / 24
#     The formatted table shows Max_Days in the price row (far right).
#     A host with Max_Days < your training duration will kill the container mid-run.
#     For exact values, parse raw:
vastai search offers '<query>' --raw | python3 -c "
import sys, json, time
for o in json.load(sys.stdin)[:10]:
    print(o['id'], f\"{(o['end_date']-time.time())/86400:.1f} days\", o['dph_total'])
"

# 2. Create instance with your training image
vastai create instance OFFER_ID --image your-registry/training:latest \
  --disk 100 --ssh --direct --onstart setup.sh

# 3. Monitor
vastai logs INSTANCE_ID --tail 50
# Also watch end_date mid-training — set an alert when hours_until_end < training_hours_left
vastai show instance INSTANCE_ID --raw | python3 -c "
import sys, json, time
d=json.load(sys.stdin); h=(d['end_date']-time.time())/3600
print(f\"hours until contract end: {h:.1f}\")"

# 4. Copy results back
vastai copy INSTANCE_ID:/workspace/results ./local_results

# 5. Destroy
vastai destroy instance INSTANCE_ID
```

**Contract expiration is a silent failure mode.** vast.ai enforces the host's `Max_Days` strictly — when `end_date` passes, the container moves to `exited / stopped`, billing stops, and you lose any in-container state not yet rsynced out. Symptoms: SSH refuses, `vastai show instance` reports `actual_status: exited` (often with `status_msg` still saying "running" — do not trust that field alone, always compare `end_date` to current time). Mitigation: (a) filter offers by `Max_Days` before renting, (b) keep rsync of checkpoints running to local, (c) set a reminder / script to poll `end_date` vs wall time.

**Manage spot instances (cheaper but interruptible):**
```bash
# Search for bid-type offers
vastai search offers 'gpu_name=RTX_4090 reliability>0.95' -b -o 'dph'

# Create with a max bid price
vastai create instance OFFER_ID --image pytorch/pytorch:latest --disk 50 --ssh --price 0.30

# Change bid later
vastai change bid INSTANCE_ID --price 0.35
```
