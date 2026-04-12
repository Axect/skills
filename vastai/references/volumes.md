# Volumes (Persistent Storage)

Volumes provide persistent storage that survives instance destruction. Use them for datasets, model weights, or any data you want to reuse across instances.

## Commands

```bash
# Create a new volume
vastai create volume

# Clone an existing volume
vastai clone volume ID

# List your volumes
vastai show volumes

# Search volume offerings
vastai search volumes

# Delete a volume
vastai delete volume ID
```

## Usage Pattern

1. Create a volume for your dataset/models
2. Attach the volume when creating instances
3. Destroy instances freely -- volume data persists
4. Delete the volume when truly done
