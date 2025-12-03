# Cell Spec CLI

> Configuration-as-code tool: markdown cell specs → terraform + env configs

## Overview

Cell Spec CLI converts human-readable markdown specifications into machine-readable configuration files for infrastructure provisioning.

**Input:** Markdown tables describing infrastructure
**Output:** Terraform `.tfvars` + `.env` files for ECS tasks

Workflow: engineers edit simple markdown → automation converts to machine-readable config

---

## Quick Start

```bash
# setup
export PYTHONPATH=src

# generate configs
python -m cellcli.cli --input examples/cell-spec.md --out-prefix examples/icc-01
```

**Generates:**
- `examples/icc-01.tfvars` - terraform variables
- `examples/icc-01.env` - ECS environment variables

---

## How It Works

### Input: Markdown Specification

```markdown
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

| Setting        | Value        |
|----------------|--------------|
| instance_class | db.t3.small  |
| storage_gb     | 20           |

## Cache

| Setting   | Value          |
|-----------|----------------|
| node_type | cache.t3.micro |
| nodes     | 1              |
```

### Output: Terraform Variables

**`icc-01.tfvars`**
```hcl
cell_name  = "icc-01"
realm_name = "dev-east"
region     = "us-east-2"

# kernel layer
kernel_cpu    = 256
kernel_memory = 512
kernel_tasks  = 2

# platform layer
platform_cpu    = 512
platform_memory = 1024
platform_tasks  = 2

# gateway layer
gateway_cpu    = 256
gateway_memory = 512
gateway_tasks  = 2

# apps layer
apps_cpu    = 512
apps_memory = 1024
apps_tasks  = 2

# database
db_instance_class = "db.t3.small"
db_storage_gb     = 20

# cache
cache_node_type = "cache.t3.micro"
cache_nodes     = 1
```

### Output: Environment Variables

**`icc-01.env`**
```bash
CELL_NAME=icc-01
REALM_NAME=dev-east
REGION=us-east-2

KERNEL_CPU=256
KERNEL_MEMORY_MB=512
KERNEL_TASKS=2

PLATFORM_CPU=512
PLATFORM_MEMORY_MB=1024
PLATFORM_TASKS=2

GATEWAY_CPU=256
GATEWAY_MEMORY_MB=512
GATEWAY_TASKS=2

APPS_CPU=512
APPS_MEMORY_MB=1024
APPS_TASKS=2

DB_INSTANCE_CLASS=db.t3.small
DB_STORAGE_GB=20

CACHE_NODE_TYPE=cache.t3.micro
CACHE_NODES=1
```

---

## Project Structure

```
src/cellcli/
├── cli.py         # CLI entrypoint, orchestrates workflow
├── parser.py      # markdown → CellSpec objects
├── models.py      # dataclasses: Cell, layers, database, cache
├── generators.py  # CellSpec → tfvars/env strings
└── errors.py      # custom exceptions

examples/
└── cell-spec.md   # sample input specification

tests/
├── test_parser.py     # parser validation tests
└── test_generators.py # output generation tests
```

---

## Validation

Parser enforces:

- **Required metadata:** `cell_name`, `realm`, `region`
- **Required layers:** `kernel`, `platform`, `gateway`, `apps` (fixed architecture)
- **Database settings:** `instance_class`, `storage_gb` (positive integer)
- **Cache settings:** `node_type`, `nodes` (positive integer)
- **Numeric validation:** all numbers must be positive

### Error Example

```
[cell-spec-cli] Spec error in examples/cell-spec.md: Database 'storage_gb' must be positive.
```

**Exit codes:**
- `1` - spec validation error
- `2` - unexpected error
- `3` - file write error

---

## Testing

```bash
export PYTHONPATH=src
python -m unittest discover -s tests
```

Tests cover:
- Parsing valid/invalid specs
- Generator output validation
- Error handling

---

## Assumptions

Built with a specific cell architecture in mind:

**Architecture:**
- Dvery cell has exactly 4 layers: kernel, platform, gateway, apps
- Layer names and count fixed - only resource values configurable
- One RDS instance per cell
- One ElastiCache cluster per cell

**Input format:**
- Markdown tables with exact column headers expected
- Cell name extracted from `# <name> Cell` title format
- Realm/region as simple `Key: value` lines
- Compute layers table needs 4+ columns, db/cache tables need 2

**Output:**
- Terraform vars use `<layer>_<attribute>` naming
- Env vars uppercase with underscores
- Layers always output in same order (kernel→platform→gateway→apps) for clean diffs
- .env files have no comments (ECS compatibility)

**Validation:**
- All resource numbers must be positive (no zero or negative)
- Does not validate AWS-specific limits (e.g., instance types)
- Does not check cross-field constraints (like memory-to-cpu ratios)
- Fails on first error instead of collecting all errors

**Workflow:**
- Pure Python stdlib, no external dependencies
- One markdown file → one .tfvars + one .env
- `--out-prefix foo` generates `foo.tfvars` and `foo.env`
- Exit codes for CI/CD: 1=spec error, 2=unexpected, 3=file write

---

## Why This Design

This design keeps it simple - there are no dependencies, only string parsing. Deterministic output means that git diffs stay clean. Two-pass validation catches structural issues before type issues. It is designed for automation pipelines where you want fast feedback and clear errors.