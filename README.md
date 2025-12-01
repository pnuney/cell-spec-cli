# Cell Spec CLI

Cell Spec CLI reads a Cell specification written in markdown and generates two files:

- a Terraform `.tfvars` file with variables for infrastructure provisioning  
- a `.env` file with environment variables for ECS tasks

This mirrors the pattern where engineers edit simple markdown tables and automation converts them into machine readable config.

---

## What the tool does

Given a markdown file like:

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

It produces:

icc-01.tfvars:

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



icc-01.env:

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



Project Structure:

src/
  cellcli/
    cli.py         CLI entrypoint
    parser.py      Markdown parser to CellSpec
    models.py      Dataclasses for Cell, layers, database, cache
    generators.py  Writers for .tfvars and .env
    errors.py      Custom error types

examples/
  cell-spec.md     Sample input spec

tests/
  test_parser.py       Parser tests
  test_generators.py   Generator tests



Usage

From the project root:

export PYTHONPATH=src
python -m cellcli.cli --input examples/cell-spec.md --out-prefix examples/icc-01


This generates:

examples/icc-01.tfvars

examples/icc-01.env

You can point --input at any markdown file with the same structure to generate configs for other Cells.

Validation and errors

The parser validates:

required fields: cell name, realm, region

presence of all four compute layers: kernel, platform, gateway, apps

required database fields: instance_class, storage_gb

required cache fields: node_type, nodes

all numeric fields are positive integers

Failures raise CellSpecError and the CLI exits with a clear message, for example:

[cell-spec-cli] Spec error in examples/cell-spec.md: Database 'storage_gb' must be positive.

Testing

Tests are written with the standard library unittest module.

Run all tests with:

export PYTHONPATH=src
python -m unittest discover -s tests


This exercises the parser against examples/cell-spec.md and checks that the generators produce the expected fields in .tfvars and .env.