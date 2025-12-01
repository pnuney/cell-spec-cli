from dataclasses import dataclass
from typing import List


@dataclass
class LayerSpec:
    name: str
    vcpu: int
    memory_mb: int
    tasks: int


@dataclass
class DatabaseSpec:
    instance_class: str
    storage_gb: int


@dataclass
class CacheSpec:
    node_type: str
    nodes: int


@dataclass
class CellSpec:
    cell_name: str
    realm_name: str
    region: str
    layers: List[LayerSpec]
    database: DatabaseSpec
    cache: CacheSpec
