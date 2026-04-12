# Instance Management

## Lifecycle

Instance states: Image Download -> Boot -> **Running** -> Stopped -> Destroyed

- Storage charges begin at creation
- GPU charges begin when instance reaches "running" state
- Stopping an instance preserves data but stops GPU charges
- Destroying is irreversible and stops all charges

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
vastai destroy instance ID

# Multiple
vastai destroy instances ID1 ID2 ID3
```

Always destroy when done to avoid ongoing storage charges.
