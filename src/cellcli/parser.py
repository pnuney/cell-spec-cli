from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from .models import CellSpec, LayerSpec, DatabaseSpec, CacheSpec
from .errors import CellSpecError


def parse_cell_spec(path: Path) -> CellSpec: #main parser entrypoint
    """Parse a markdown Cell spec file into a CellSpec object.""" #what is happening here, generating what? then outputting what? use return keyword
    if not path.exists():
        raise CellSpecError(f"Spec file not found: {path}")

    text = path.read_text(encoding="utf8") #read file into list of lines
    lines = [line.rstrip("\n") for line in text.splitlines()]

    cell_name: str | None = None
    realm_name: str | None = None
    region: str | None = None

    layers: List[LayerSpec] = []
    db_settings: Dict[str, str] = {}
    cache_settings: Dict[str, str] = {}

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        #top level title: "icc-01 Cell"
        if line.startswith("# "):
            cell_name = _parse_cell_name_from_title(line)
            i += 1
            continue

        #simple key lines: "realm: dev-east"
        if line.lower().startswith("realm:"):
            realm_name = line.split(":", 1)[1].strip()
            i += 1
            continue
        #simple key lines: "region: us-east-1"
        if line.lower().startswith("region:"):
            region = line.split(":", 1)[1].strip()
            i += 1
            continue

        #section headers
        if line.lower().startswith("## compute layers"):
            layers, i = _parse_layers_table(lines, i + 1)
            continue

        if line.lower().startswith("## database"):
            db_settings, i = _parse_kv_table(lines, i + 1)
            continue

        if line.lower().startswith("## cache"):
            cache_settings, i = _parse_kv_table(lines, i + 1)
            continue

        i += 1

    #firstbasic validation
    if not cell_name:
        raise CellSpecError("Missing Cell title line (expected '# <name> Cell').")

    if not realm_name:
        raise CellSpecError("Missing 'Realm:' line.")

    if not region:
        raise CellSpecError("Missing 'Region:' line.")

    if not layers:
        raise CellSpecError("No compute layers found under '## Compute Layers'.")

    required_layers = {"kernel", "platform", "gateway", "apps"}
    found_layers = {layer.name.lower() for layer in layers}
    missing = required_layers - found_layers
    if missing:
        raise CellSpecError(f"Missing required compute layers: {', '.join(sorted(missing))}.")

    #db settings
    if not db_settings:
        raise CellSpecError("No database settings found under '## Database'.")

    if "instance_class" not in db_settings or "storage_gb" not in db_settings:
        raise CellSpecError("Database table must define 'instance_class' and 'storage_gb'.")

    try:
        db = DatabaseSpec(
            instance_class=db_settings["instance_class"],
            storage_gb=int(db_settings["storage_gb"]),
        )
    except ValueError as exc:
        raise CellSpecError("Database 'storage_gb' must be an integer.") from exc

    #cache settings
    if not cache_settings:
        raise CellSpecError("No cache settings found under '## Cache'.")

    if "node_type" not in cache_settings or "nodes" not in cache_settings:
        raise CellSpecError("Cache table must define 'node_type' and 'nodes'.")
    #convert numeric fields to integers
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

    cell = CellSpec(
        cell_name=cell_name,
        realm_name=realm_name,
        region=region,
        layers=layers,
        database=db,
        cache=cache,
    )

    _validate_cell_spec_numbers(cell) #second validation pass

    return cell


def _parse_cell_name_from_title(line: str) -> str:
    #expect smtg like "# icc-01 Cell"
    title = line.lstrip("#").strip()
    if title.lower().endswith(" cell"):
        title = title[:-4].strip()
    return title


def _parse_layers_table(lines: List[str], start: int) -> tuple[List[LayerSpec], int]:
    i = start
    n = len(lines)

    #skip empty lines before header
    while i < n and not lines[i].strip():
        i += 1

    #expect header and separator row
    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Compute Layers table header row is missing or malformed.")
    i += 1

    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Compute Layers table separator row is missing.")
    i += 1

    layers: List[LayerSpec] = []

    while i < n:
        line = lines[i].strip()
        if not line or not line.startswith("|"):
            break

        #skip separator style rows just in case
        if set(line.replace("|", "").strip()) <= {"-", ":"}:
            i += 1
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]#table row to column values
        if len(cells) < 4:
            raise CellSpecError("Compute Layers row must have at least 4 columns.")

        name, vcpu_str, mem_str, tasks_str = cells[:4]

        try:
            vcpu = int(vcpu_str)
            memory_mb = int(mem_str)
            tasks = int(tasks_str)
        except ValueError as exc:
            raise CellSpecError(f"Invalid numeric values in compute layer row: {line}") from exc
        
        #text to object conversion
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
    i = start
    n = len(lines)

    #skip empty lines before header
    while i < n and not lines[i].strip():
        i += 1

    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Key value table header row is missing or malformed.")
    i += 1

    if i >= n or not lines[i].strip().startswith("|"):
        raise CellSpecError("Key value table separator row is missing.")
    i += 1

    result: Dict[str, str] = {}

    while i < n:
        line = lines[i].strip()
        if not line or not line.startswith("|"):
            break

        if set(line.replace("|", "").strip()) <= {"-", ":"}:
            i += 1
            continue
        #split row on |, trim whitespace
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            raise CellSpecError(f"Key value row must have at least 2 columns: {line}")

        key, value = cells[0], cells[1]
        key = key.strip().lower()

        if key:
            result[key] = value.strip()

        i += 1

    return result, i

#numeric validation
def _validate_cell_spec_numbers(cell: CellSpec) -> None:
    for layer in cell.layers:
        if layer.vcpu <= 0:
            raise CellSpecError(f"Layer '{layer.name}' vCPU must be positive.")
        if layer.memory_mb <= 0:
            raise CellSpecError(f"Layer '{layer.name}' memory_mb must be positive.")
        if layer.tasks <= 0:
            raise CellSpecError(f"Layer '{layer.name}' tasks must be positive.")

    if cell.database.storage_gb <= 0:
        raise CellSpecError("Database 'storage_gb' must be positive.")

    if cell.cache.nodes <= 0:
        raise CellSpecError("Cache 'nodes' must be positive.")
