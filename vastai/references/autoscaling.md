# Autoscaling & Serverless Endpoints

## Autoscalers

Autoscalers automatically manage a group of worker instances, scaling up/down based on load.

### Create Autoscaler

```bash
vastai create autoscaler [OPTIONS]
```

| Option | Description |
|---|---|
| `--min_load MIN_LOAD` | Minimum floor load (tokens/s for LLMs) |
| `--target_util TARGET_UTIL` | Target utilization fraction (max 1.0, default 0.9) |
| `--cold_mult COLD_MULT` | Cold instance capacity multiplier (default 2.5) |
| `--gpu_ram GPU_RAM` | Estimated GPU RAM requirement |
| `--search_params SEARCH_PARAMS` | Search criteria for selecting instances |
| `--launch_args LAUNCH_ARGS` | Arguments for instance creation |
| `--endpoint_name ENDPOINT_NAME` | Endpoint identifier |

### Manage Autoscalers

```bash
# List autoscalers
vastai show autoscalers

# Update configuration
vastai update autoscaler ID [OPTIONS]

# Delete (does NOT destroy associated instances)
vastai delete autoscaler ID
```

## Endpoints

Serverless endpoint groups for GPU instance allocation.

```bash
# Create endpoint
vastai create endpoint

# List endpoints
vastai show endpoints

# Update endpoint
vastai update endpoint ID

# Delete endpoint
vastai delete endpoint ID

# View endpoint logs
vastai get endpt-logs
```
