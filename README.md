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

## Design Assumptions

### Architecture Assumptions
1. **Fixed 4-layer compute model** - every cell has exactly: kernel, platform, gateway, apps
2. **Single database per cell** - one RDS instance per cell
3. **Single cache cluster per cell** - one ElastiCache cluster per cell
4. **No layer customization** - layer names/count fixed, only resources configurable

### Input Assumptions
5. **Strict markdown format** - tables must have exact column headers
6. **Cell name in title** - extracted from `# <name> Cell` format
7. **Key-value metadata** - `Realm:` and `Region:` as plain text pairs
8. **Table structure** - compute layers table has 4+ columns, db/cache have 2 columns

### Output Assumptions
9. **Terraform variable naming** - follows `<layer>_<attribute>` convention
10. **Environment variable naming** - uppercase with underscores
11. **Deterministic output** - fixed layer order (kernel→platform→gateway→apps) for clean git diffs
12. **No comments in .env** - only KEY=VALUE pairs for ECS compatibility

### Workflow Assumptions
13. **Zero external dependencies** - pure Python stdlib for portability
14. **Single-file input** - one markdown file per cell
15. **Prefix-based output** - `--out-prefix foo` generates `foo.tfvars` + `foo.env`
16. **CI/CD integration** - exit codes designed for automation pipelines

### Validation Assumptions
17. **Positive integers only** - no zero/negative values for resources
18. **No resource limits** - doesn't validate AWS-specific instance type validity
19. **No cross-field validation** - doesn't check resource ratios/relationships
20. **Fail-fast parsing** - stops at first validation error

---

## Design Principles

- **Lightweight** - no external dependencies, simple string parsing
- **Transparent** - easy to debug, no black-box processing
- **Deterministic** - same input always produces identical output
- **Extensible** - adding new resource types straightforward
- **Testable** - pure functions enable comprehensive testing

---

## License

MIT