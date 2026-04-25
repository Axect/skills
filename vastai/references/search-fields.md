# Search Fields & Query Syntax

## Query Syntax

```bash
vastai search offers '<field> <operator> <value> [field operator value ...]'
```

Multiple conditions are space-separated (implicit AND). Operators: `>`, `>=`, `<`, `<=`, `=`, `!=`.

GPU names use underscores for spaces (e.g., `RTX_4090`, `A100_SXM4`, `RTX_3090`, `Tesla_V100`).

## All Searchable Fields

| Field | Type | Description |
|---|---|---|
| `bw_nvlink` | float | NVLink bandwidth (GB/s) |
| `compute_cap` | int | CUDA compute capability (e.g., 800 = 8.0, 890 = 8.9) |
| `cpu_cores` | int | Virtual CPU count |
| `cpu_ram` | float | System RAM in GB |
| `cuda_vers` | float | Maximum supported CUDA version |
| `datacenter` | bool | true = datacenter-only machines |
| `disk_space` | float | Available storage in GB |
| `dlperf` | float | Deep learning performance score |
| `dlperf_usd` | float | DL performance per dollar |
| `dph` | float | Cost per hour in USD |
| `external` | bool | Include external (non-verified) offers |
| `flops_usd` | float | TFLOPs per dollar |
| `gpu_name` | string | GPU model name (underscores for spaces) |
| `gpu_ram` | float | Per-GPU VRAM in GB |
| `gpu_total_ram` | float | Total VRAM across all GPUs in GB |
| `inet_down` | float | Download speed in Mb/s |
| `inet_up` | float | Upload speed in Mb/s |
| `num_gpus` | int | Number of GPUs |
| `pci_gen` | int | PCIe generation |
| `reliability` | float | Machine reliability score (0.0 - 1.0) |
| `rentable` | bool | Currently available for rent |
| `rented` | bool | Include machines with existing contracts |
| `static_ip` | bool | Has stable IP address |
| `total_flops` | float | Combined GPU TFLOPs |
| `verified` | bool | Machine verification status |

## Contract Duration (`Max_Days`)

The formatted output of `vastai search offers` shows a **`Max_Days`** column (far right of the price row). This is the maximum contract length the host commits to — **the host may terminate the rental at `end_date = start_time + Max_Days`**, killing your container regardless of training state. Filter is NOT exposed as a query field; read from the formatted table or from raw JSON (`.end_date - now`).

**Rule of thumb**: require `Max_Days ≥ 1.5 × expected_training_hours / 24` before renting. Short Max_Days (e.g. 0.5 day, 13h) is the silent killer of long training jobs — not all offers advertise sufficient committed duration.

```bash
# Parse Max_Days from formatted output (column position varies, use raw for robustness)
vastai search offers 'gpu_name=RTX_5080 reliability>0.98 verified=true' -o 'dph' --raw \
  | python3 -c "
import sys, json, time
offers = json.load(sys.stdin)
now = time.time()
for o in offers[:10]:
    days_remaining = (o['end_date'] - now) / 86400
    print(f\"id={o['id']} dph={o['dph_total']:.4f} days_left={days_remaining:.1f} mach={o['machine_id']}\")
"
```

## Search Command Options

| Flag | Description |
|---|---|
| `-t TYPE`, `--type TYPE` | Pricing type: `on-demand`, `reserved`, `bid` |
| `-d`, `--on-demand` | On-demand instances only |
| `-b`, `--bid` | Bid/spot instances (interruptible) |
| `-i`, `--interruptible` | Same as `--bid` |
| `-r`, `--reserved` | Reserved instances |
| `-n`, `--no-default` | Disable default query filters |
| `--disable-bundling` | Show duplicate offers (rate-limited) |
| `--storage STORAGE` | Storage amount for pricing calculation (default 5.0 GiB) |
| `-o ORDER`, `--order ORDER` | Sort field. Append `-` for descending (e.g., `-o 'dph'` or `-o 'num_gpus-'`) |

## Examples

```bash
# Cheapest single RTX 4090
vastai search offers 'gpu_name=RTX_4090 num_gpus=1 reliability>0.95' -o 'dph'

# Multi-GPU A100 setups for large model training
vastai search offers 'gpu_name=A100_SXM4 num_gpus>=4 reliability>0.98 inet_down>500' -o 'dph'

# Budget GPU with decent VRAM
vastai search offers 'gpu_ram>=16 dph<0.30 reliability>0.90' -o 'dph'

# High-performance datacenter machines
vastai search offers 'datacenter=true dlperf>20 reliability>0.99' -o 'dlperf_usd-'

# NVLink-connected multi-GPU
vastai search offers 'bw_nvlink>50 num_gpus>=2' -o 'dph'

# CUDA 12+ compatible
vastai search offers 'cuda_vers>=12.0 gpu_ram>=24' -o 'dph'

# Spot/bid instances (cheaper, interruptible)
vastai search offers 'gpu_name=RTX_4090 reliability>0.95' -b -o 'dph'
```
