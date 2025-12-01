from .models import CellSpec


def generate_tfvars(cell: CellSpec) -> str:
    """Return the contents of a .tfvars file for this CellSpec."""
    
    lines: list[str] = []

    #core identity
    lines.append(f'cell_name  = "{cell.cell_name}"')
    lines.append(f'realm_name = "{cell.realm_name}"')
    lines.append(f'region     = "{cell.region}"')
    lines.append("")

    #compute layers in  fixed and predictable order
    #this ordering will always be kernel, platform, gateway, apps
    layer_order = ["kernel", "platform", "gateway", "apps"]
    layers_by_name = {layer.name.lower(): layer for layer in cell.layers}

    for name in layer_order:
        layer = layers_by_name.get(name)
        if not layer:
            #parser should have guaranteed this, but we guard anyway
            continue

        prefix = layer.name.lower()
        lines.append(f"# {prefix} layer")
        lines.append(f"{prefix}_cpu    = {layer.vcpu}")
        lines.append(f"{prefix}_memory = {layer.memory_mb}")
        lines.append(f"{prefix}_tasks  = {layer.tasks}")
        lines.append("")

    #database
    lines.append("# database")
    lines.append(f'db_instance_class = "{cell.database.instance_class}"')
    lines.append(f"db_storage_gb     = {cell.database.storage_gb}")
    lines.append("")

    #cache
    lines.append("# cache")
    lines.append(f'cache_node_type = "{cell.cache.node_type}"')
    lines.append(f"cache_nodes     = {cell.cache.nodes}")

    #join with newlines and ensure a trailing newline at end of file
    return "\n".join(lines).rstrip() + "\n"


def generate_env(cell: CellSpec) -> str:
    """Return the contents of a .env file for this CellSpec."""

    lines: list[str] = []

    #core identity
    lines.append(f"CELL_NAME={cell.cell_name}")
    lines.append(f"REALM_NAME={cell.realm_name}")
    lines.append(f"REGION={cell.region}")
    lines.append("")

    #compute layers in fixed order
    layer_order = ["kernel", "platform", "gateway", "apps"]
    layers_by_name = {layer.name.lower(): layer for layer in cell.layers}

    for name in layer_order:
        layer = layers_by_name.get(name)
        if not layer:
            continue

        upper = layer.name.upper()
        lines.append(f"{upper}_CPU={layer.vcpu}")
        lines.append(f"{upper}_MEMORY_MB={layer.memory_mb}")
        lines.append(f"{upper}_TASKS={layer.tasks}")
        lines.append("")

    #database
    lines.append("DB_INSTANCE_CLASS=" + cell.database.instance_class)
    lines.append(f"DB_STORAGE_GB={cell.database.storage_gb}")
    lines.append("")

    #cache
    lines.append("CACHE_NODE_TYPE=" + cell.cache.node_type)
    lines.append(f"CACHE_NODES={cell.cache.nodes}")

    return "\n".join(lines).rstrip() + "\n"
