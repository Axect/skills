# Hosting (List Your Own Machines)

If you have GPU machines, you can list them on the Vast.ai marketplace for others to rent.

## Listing Machines

```bash
# List a single machine
vastai list machine ID [OPTIONS]

# List multiple machines
vastai list machines

# Remove from marketplace
vastai unlist machine ID
```

### Listing Options

| Option | Description |
|---|---|
| `-g`, `--price_gpu` | GPU rental rate ($/hr per GPU) |
| `-s`, `--price_disk` | Storage cost ($/GB/month, default $0.15) |
| `-u`, `--price_inetu` | Upload bandwidth rate ($/GB) |
| `-d`, `--price_inetd` | Download bandwidth rate ($/GB) |
| `-r`, `--discount_rate` | Max prepay discount fraction (default 0.4) |
| `-m`, `--min_chunk` | Minimum GPU allocation |
| `-e`, `--end_date` | Listing expiration (unix epoch timestamp) |

## Default Jobs

Background instances that run when the machine is idle (not rented).

```bash
# Set default job
vastai set defjob ID --image IMAGE [--args ...]

# Remove default job
vastai remove defjob ID
```

## Pricing

```bash
# Set minimum bid/rental price per GPU
vastai set min_bid ID --price PRICE
```

## Maintenance

```bash
# Schedule maintenance window (notifies clients)
vastai schedule maintenance ID --sdate START_EPOCH --duration HOURS

# Cancel scheduled maintenance
vastai cancel maint ID
```

## Machine Management

```bash
# View your machines
vastai show machines
vastai show machine ID

# View maintenance schedule
vastai show maints

# Run hardware validation
vastai self-test machine ID

# Clean up expired storage
vastai cleanup machine ID

# Delete unlisted machine
vastai delete machine ID
```

## Volume Hosting

```bash
# List storage volumes for rental
vastai list volume
vastai list volumes

# Remove from marketplace
vastai unlist volume ID
```

**Important**: Machine instability while hosting client instances permanently reduces your reliability rating.
