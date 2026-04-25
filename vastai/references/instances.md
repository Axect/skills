# Instance Management

## Lifecycle

Instance states: Image Download -> Boot -> **Running** -> Stopped -> Destroyed

- Storage charges begin at creation
- GPU charges begin when instance reaches "running" state
- Stopping an instance preserves data but stops GPU charges
- Destroying is irreversible and stops all charges

## Contract Duration (silent failure mode)

Every rental has a hard `end_date` = rental_start + host's `Max_Days`. When `end_date` elapses, vast.ai moves the container to `exited / stopped` regardless of what your training process is doing — **SSH refuses, in-container state is lost, and the `status_msg` field often still claims "success, running" for hours after**, so don't trust it alone.

```bash
# Inspect current contract duration
vastai show instance ID --raw | python3 -c "
import sys, json, time
d = json.load(sys.stdin)
h = (d['end_date'] - time.time()) / 3600
print(f'state: {d[\"actual_status\"]} / {d[\"intended_status\"]}')
print(f'hours_until_end_date: {h:.1f}')
print(f'status_msg: {(d.get(\"status_msg\") or \"\")[-200:]}')
"
```

- **Before renting** long jobs: verify `Max_Days` column in `vastai search offers` output (see `search-fields.md`). Require `Max_Days ≥ 1.5 × expected_hours / 24`.
- **During training**: periodically poll `end_date` vs current time. When `hours_until_end < remaining_training_hours`, the job will be killed — rsync checkpoints out and plan a migration.
- **After an unexpected `exited`**: check `hours_until_end_date` before assuming a bug; negative value means contract expiration, not container crash. Destroy the expired instance and rent a longer-duration offer.

## Creating Instances

```bash
vastai create instance OFFER_ID [OPTIONS]
```

| Option | Description |
|---|---|
| `--image IMAGE` | Docker container image (required) |
| `--disk DISK` | Local disk partition size in GB |
| `--price PRICE` | Bid price for spot instances ($/hr) |
| `--label LABEL` | Human-readable instance label |
| `--onstart SCRIPT` | Startup script filename |
| `--ssh` | Launch as SSH-accessible instance |
| `--jupyter` | Launch as Jupyter-accessible instance |
| `--direct` | Direct connection (vs proxied through Vast.ai) |
| `--env ENV` | Environment variables and port mappings |
| `--create-from ID` | Use existing instance as template |
| `--args ...` | Additional container arguments |

Each offer ID can only create one instance.

## Viewing Instances

```bash
# List all instances
vastai show instances
vastai show instances -q          # IDs only

# Single instance details
vastai show instance ID
```

## Start / Stop / Reboot

```bash
# Stop (preserves data, stops GPU billing)
vastai stop instance ID
vastai stop instances ID1 ID2 ID3

# Start a stopped instance
vastai start instance ID
vastai start instances ID1 ID2 ID3

# Reboot (stop/start cycle, keeps GPU priority)
vastai reboot instance ID
```

## Recycle & Update

```bash
# Destroy and immediately recreate
vastai recycle instance ID

# Recreate from new/updated template
vastai update instance ID
```

## Labels

```bash
vastai label instance ID "my-label"
```

## SSH & Connectivity

```bash
# Attach/detach SSH keys
vastai attach ssh ID
vastai detach ssh ID

# Get SSH connection URL
vastai ssh-url ID

# Get SCP URL for file transfers
vastai scp-url ID
```

## Logs & Remote Execution

```bash
# View logs (default: last 1000 lines)
vastai logs ID
vastai logs ID --tail 100

# Execute remote commands (limited to: ls, rm, du)
vastai execute ID ls /workspace
vastai execute ID du /workspace
vastai execute ID rm /workspace/tmp_file
```

## Data Transfer

```bash
# Local <-> Instance
vastai copy local_file instance_id:/remote/path
vastai copy instance_id:/remote/path ./local_path

# Cloud <-> Instance
vastai cloud copy --src SRC --dst DST --instance ID --connection CONN --transfer "Cloud To Instance"
vastai cloud copy --src SRC --dst DST --instance ID --connection CONN --transfer "Instance To Cloud"

# Cancel transfers
vastai cancel copy DST
vastai cancel sync DST
```

**Warning**: Never use `/root` or `/` as copy destination -- corrupts SSH.

## Pricing & Bidding

```bash
# Change bid on a spot instance
vastai change bid ID --price 0.35

# Prepay credits into reserved instance
vastai prepay instance ID AMOUNT
```

## Destroying Instances

```bash
# Single (irreversible!)
vastai destroy instance ID -y

# Multiple
vastai destroy instances ID1 ID2 ID3 -y
```

The CLI prompts `Are you sure...? [y/N]` on the terminal and aborts if no TTY is attached. Piping `yes` does not satisfy the prompt — it reads directly from the terminal. Use `-y` / `--yes` in any non-interactive context (Claude tool calls, scripts, CI) to skip the confirmation.

Always destroy when done to avoid ongoing storage charges.
