# icc-01 Cell
Realm: dev-east
Region: us-east-2

## Compute Layers

| Layer    | vCPU | Memory MB | Tasks |
|----------|------|-----------|-------|
| kernel   | 256  | 512       | 2     |
| platform | 512  | 1024      | 2     |
| gateway  | 256  | 512       | 2     |
| apps     | 512  | 1024      | 2     |

## Database

| Setting        | Value       |
|----------------|------------|
| instance_class | db.t3.small |
| storage_gb     | 20          |

## Cache

| Setting   | Value        |
|-----------|-------------|
| node_type | cache.t3.micro |
| nodes     | 1           |
