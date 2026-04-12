# Billing, Account & Teams

## Account

```bash
# View account info and balance
vastai show user
vastai show user -q    # condensed

# Update user data from JSON
vastai set user

# View IP address history
vastai show ipaddrs
```

## API Keys

```bash
# Set API key
vastai set api-key YOUR_KEY

# Create restricted API key
vastai create api-key --permissions permissions.json

# View keys
vastai show api-key ID
vastai show api-keys

# Reset (requires website)
vastai reset api-key

# Delete
vastai delete api-key ID
```

## SSH Keys

```bash
vastai create ssh-key
vastai show ssh-keys
vastai update ssh-key ID
vastai delete ssh-key ID
```

## Environment Variables

```bash
vastai create env-var
vastai show env-vars
vastai update env-var ID
vastai delete env-var ID
```

## Invoices & Billing

```bash
# Basic invoice view
vastai show invoices [OPTIONS]
  -s START_DATE    # range start
  -e END_DATE      # range end
  -c               # charges only
  -p               # credits only
  --instance_label # filter by label

# Advanced invoicing (v1) with pagination
vastai show invoices-v1 [OPTIONS]
  -i               # show invoices (default: charges)
  -it TYPE         # filter invoice type
  -c               # show charges
  -ct TYPE         # filter charge type
  -s START_DATE    # YYYY-MM-DD or timestamp
  -e END_DATE      # YYYY-MM-DD or timestamp
  -l LIMIT         # results per page (default 20, max 100)
  -t TOKEN         # pagination token
  -f FORMAT        # table or tree
  -v               # verbose details
  --latest-first   # reverse sort

# Search invoices
vastai search invoices

# Generate PDF invoices
vastai generate pdf-invoices [OPTIONS]

# View earnings (for hosts)
vastai show earnings [OPTIONS]
  -s START_DATE
  -e END_DATE
  -m MACHINE_ID
```

## Credit Transfer

```bash
vastai transfer credit RECIPIENT_EMAIL AMOUNT
```

## Audit Logs

```bash
vastai show audit-logs
```

## Teams

```bash
# Create team
vastai create-team --team_name NAME

# Invite member
vastai invite team-member --email EMAIL --role ROLE

# View members
vastai show team-members

# Remove member
vastai remove team-member ID

# Destroy team (irreversible)
vastai destroy team
```

### Team Roles

```bash
vastai create team-role NAME --permissions PERMISSIONS
vastai show team-role NAME
vastai show team-roles
vastai update team-role ID --name NAME --permissions PERMISSIONS
vastai remove team-role NAME
```

## Subaccounts

```bash
# Create child account
vastai create subaccount --email EMAIL --username USER --password PASS --type TYPE
# TYPE: host or client

# View subaccounts
vastai show subaccounts
```

## Cloud Connections

```bash
vastai show connections
```

## Networking (Clusters & Overlays)

```bash
# Clusters (locally-networked machines)
vastai create cluster SUBNET MANAGER_ID
vastai join cluster CLUSTER_ID MACHINE_IDS
vastai show clusters
vastai delete cluster CLUSTER_ID
vastai remove-machine-from-cluster CLUSTER_ID MACHINE_ID NEW_MANAGER_ID

# Overlays (virtual networks within clusters)
vastai create overlay CLUSTER_ID OVERLAY_NAME
vastai join overlay OVERLAY_NAME INSTANCE_ID
vastai show overlays
vastai delete overlay OVERLAY_ID
```
