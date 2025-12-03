from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from .models import CellSpec, LayerSpec, DatabaseSpec, CacheSpec
from .errors import CellSpecError


def parse_cell_spec(path: Path) -> CellSpec:
    """
    Main parser entrypoint. Reads markdown file and converts to CellSpec object.

    Strategy: single-pass line-by-line scan, extracting metadata and delegating
    table parsing to helper functions. Two-pass validation (structural then numeric).

    Returns: fully validated CellSpec object ready for generation
    Raises: CellSpecError if file missing, malformed, or validation fails
    """
    # verify file exists before attempting read
    if not path.exists():
        raise CellSpecError(f"Spec file not found: {path}")

    # read entire file into memory, normalize line endings
    text = path.read_text(encoding="utf8")
    lines = [line.rstrip("\n") for line in text.splitlines()]

    # accumulators for parsed data - metadata as optionals, collections as empties
    cell_name: str | None = None
    realm_name: str | None = None
    region: str | None = None

    layers: List[LayerSpec] = []
    db_settings: Dict[str, str] = {}
    cache_settings: Dict[str, str] = {}

    # manual line iteration - helpers update index to skip consumed lines
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        # extract cell name from title line: "# icc-01 Cell" → "icc-01"
        if line.startswith("# "):
            cell_name = _parse_cell_name_from_title(line)
            i += 1
            continue

        # extract metadata from simple key-value lines
        # split on first colon, take everything after as value
        if line.lower().startswith("realm:"):
            realm_name = line.split(":", 1)[1].strip()
            i += 1
            continue

        if line.lower().startswith("region:"):
            region = line.split(":", 1)[1].strip()
            i += 1
            continue

        # section headers trigger table parsing
        # helpers return (parsed_data, updated_index) tuples
        if line.lower().startswith("## compute layers"):
            layers, i = _parse_layers_table(lines, i + 1)
            continue

        if line.lower().startswith("## database"):
            db_settings, i = _parse_kv_table(lines, i + 1)
            continue

        if line.lower().startswith("## cache"):
            cache_settings, i = _parse_kv_table(lines, i + 1)
            continue

        # unrecognized line - skip and continue
        i += 1

    # validation pass 1: structural completeness

    # ensure all required metadata present
    if not cell_name:
        raise CellSpecError("Missing Cell title line (expected '# <name> Cell').")

    if not realm_name:
        raise CellSpecError("Missing 'Realm:' line.")

    if not region:
        raise CellSpecError("Missing 'Region:' line.")

    # ensure compute layers table was found and parsed
    if not layers:
        raise CellSpecError("No compute layers found under '## Compute Layers'.")

    # enforce fixed 4-layer architecture: kernel, platform, gateway, apps
    required_layers = {"kernel", "platform", "gateway", "apps"}
    found_layers = {layer.name.lower() for layer in layers}
    missing = required_layers - found_layers
    if missing:
        raise CellSpecError(f"Missing required compute layers: {', '.join(sorted(missing))}.")

    # validate database section exists and has required keys
    if not db_settings:
        raise CellSpecError("No database settings found under '## Database'.")

    if "instance_class" not in db_settings or "storage_gb" not in db_settings:
        raise CellSpecError("Database table must define 'instance_class' and 'storage_gb'.")

    # attempt conversion to DatabaseSpec - validates storage_gb is integer
    try:
        db = DatabaseSpec(
            instance_class=db_settings["instance_class"],
            storage_gb=int(db_settings["storage_gb"]),
        )
    except ValueError as exc:
        raise CellSpecError("Database 'storage_gb' must be an integer.") from exc

    # validate cache section exists and has required keys
    if not cache_settings:
        raise CellSpecError("No cache settings found under '## Cache'.")

    if "node_type" not in cache_settings or "nodes" not in cache_settings:
        raise CellSpecError("Cache table must define 'node_type' and 'nodes'.")

    # attempt conversion to CacheSpec - validates nodes is integer
    try:
        cache = CacheSpec(
            node_type=cache_settings["node_type"],
            nodes=int(cache_settings["nodes"]),
        )
    except ValueError as exc:
        raise CellSpecError("Cache 'nodes' must be an integer.") from exc

    cache = CacheSpec(
        node_type=cache_settings["node_type"],
        nodes=int(cache_settings["nodes"]),
    )

    # assemble final CellSpec object with all parsed components
    cell = CellSpec(
        cell_name=cell_name,
        realm_name=realm_name,
        region=region,
        layers=layers,
        database=db,
        cache=cache,
    )

    # validation pass 2: numeric constraints
    # ensures all numbers positive (no zero/negative resources)
    _validate_cell_spec_numbers(cell)

    return cell


def _parse_cell_name_from_title(line: str) -> str:
    """
    Extract cell name from markdown title line.

    Input: "# icc-01 Cell" → Output: "icc-01"
    Strips "# " prefix and optional " Cell" suffix
    """
    # remove markdown header prefix and whitespace
    title = line.lstrip("#").strip()

    # strip optional " Cell" suffix (case insensitive)
    if title.lower().endswith(" cell"):
        title = title[:-4].strip()

    return title


def _parse_layers_table(lines: List[str], start: int) -> tuple[List[LayerSpec], int]:
    """
    Parse compute layers markdown table into LayerSpec objects.

    Expected format:
        | Layer    | vCPU | Memory MB | Tasks |
        |----------|------|-----------|-------|
        | kernel   | 256  | 512       | 2     |
        | platform | 512  | 1024      | 2     |

    Returns: (list of LayerSpec objects, updated line index)
    Raises: CellSpecError if table malformed or data invalid
    """
    i = start
    n = len(lines)

    # skip blank lines between section header and table
    while i < n and not lines[i].strip():
        i += 1

    # verify header row present (must start with |)
    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Compute Layers table header row is missing or malformed.")
    i += 1

    # verify separator row present (markdown table format)
    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Compute Layers table separator row is missing.")
    i += 1

    layers: List[LayerSpec] = []

    # parse data rows until non-table line encountered
    while i < n:
        line = lines[i].strip()

        # stop at first non-table line (no pipe or empty)
        if not line or not line.startswith("|"):
            break

        # skip additional separator rows (shouldn't happen but defensive)
        if set(line.replace("|", "").strip()) <= {"-", ":"}:
            i += 1
            continue

        # split row on pipes, remove outer pipes and whitespace
        # example: "| kernel | 256 | 512 | 2 |" → ["kernel", "256", "512", "2"]
        cells = [c.strip() for c in line.strip("|").split("|")]

        # enforce minimum 4 columns: Layer, vCPU, Memory MB, Tasks
        if len(cells) < 4:
            raise CellSpecError("Compute Layers row must have at least 4 columns.")

        # extract first 4 columns (ignore extra columns if present)
        name, vcpu_str, mem_str, tasks_str = cells[:4]

        # convert numeric strings to integers, fail-fast on invalid input
        try:
            vcpu = int(vcpu_str)
            memory_mb = int(mem_str)
            tasks = int(tasks_str)
        except ValueError as exc:
            raise CellSpecError(f"Invalid numeric values in compute layer row: {line}") from exc

        # create LayerSpec object, normalize layer name to lowercase
        layers.append(
            LayerSpec(
                name=name.lower(),
                vcpu=vcpu,
                memory_mb=memory_mb,
                tasks=tasks,
            )
        )

        i += 1

    return layers, i


def _parse_kv_table(lines: List[str], start: int) -> tuple[Dict[str, str], int]:
    """
    Parse generic key-value markdown table into dictionary.

    Used for Database and Cache sections which have format:
        | Setting        | Value        |
        |----------------|--------------|
        | instance_class | db.t3.small  |
        | storage_gb     | 20           |

    Returns: (dict mapping lowercase keys to values, updated line index)
    Raises: CellSpecError if table structure invalid
    """
    i = start
    n = len(lines)

    # skip blank lines between section header and table
    while i < n and not lines[i].strip():
        i += 1

    # verify header row present
    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Key value table header row is missing or malformed.")
    i += 1

    # verify separator row present
    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Key value table separator row is missing.")
    i += 1

    result: Dict[str, str] = {}

    # parse data rows until non-table line encountered
    while i < n:
        line = lines[i].strip()

        # stop at first non-table line
        if not line or not line.startswith("|"):
            break

        # skip separator rows (defensive, shouldn't occur in data section)
        if set(line.replace("|", "").strip()) <= {"-", ":"}:
            i += 1
            continue

        # split row on pipes: "| instance_class | db.t3.small |" → ["instance_class", "db.t3.small"]
        cells = [c.strip() for c in line.strip("|").split("|")]

        # enforce minimum 2 columns for key-value pairs
        if len(cells) < 2:
            raise CellSpecError(f"Key value row must have at least 2 columns: {line}")

        # extract key and value from first two columns
        key, value = cells[0], cells[1]

        # normalize key to lowercase for case-insensitive lookups
        key = key.strip().lower()

        # only add non-empty keys (skip malformed rows)
        if key:
            result[key] = value.strip()

        i += 1

    return result, i

def _validate_cell_spec_numbers(cell: CellSpec) -> None:
    """
    Second validation pass: ensure all numeric resource values are positive.

    Zero or negative values disallowed - no sense provisioning 0 CPU or -1 tasks.
    Validates all layers, database, and cache numeric fields.

    Raises: CellSpecError with specific field name if any value <= 0
    """
    # validate each compute layer's resource values
    for layer in cell.layers:
        # vCPU must be positive (e.g., 256, 512)
        if layer.vcpu <= 0:
            raise CellSpecError(f"Layer '{layer.name}' vCPU must be positive.")

        # memory_mb must be positive (e.g., 512, 1024)
        if layer.memory_mb <= 0:
            raise CellSpecError(f"Layer '{layer.name}' memory_mb must be positive.")

        # tasks must be positive (e.g., 1, 2, 4)
        if layer.tasks <= 0:
            raise CellSpecError(f"Layer '{layer.name}' tasks must be positive.")

    # validate database storage (must provision some storage)
    if cell.database.storage_gb <= 0:
        raise CellSpecError("Database 'storage_gb' must be positive.")

    # validate cache node count (need at least 1 node)
    if cell.cache.nodes <= 0:
        raise CellSpecError("Cache 'nodes' must be positive.")
