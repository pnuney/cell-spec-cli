from dataclasses import dataclass
from typing import List


@dataclass
class LayerSpec: #1 compute layer with these fields
    name: str
    vcpu: int
    memory_mb: int
    tasks: int


@dataclass
class DatabaseSpec: #database instance class and storage size
    instance_class: str
    storage_gb: int


@dataclass
class CacheSpec: #define cache node type and node count
    node_type: str
    nodes: int


@dataclass
class CellSpec: #top level object
    cell_name: str
    realm_name: str
    region: str
    layers: List[LayerSpec] #all compute layers
    database: DatabaseSpec
    cache: CacheSpec
