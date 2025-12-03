#basic identity
cell_name  = "icc-01"
realm_name = "dev-east"
region = "us-east-2"

#kernel layer
kernel_cpu    = 256
kernel_memory = 512
kernel_tasks  = 2

#platform layer
platform_cpu    = 512
platform_memory = 1024
platform_tasks  = 2

#gateway layer
gateway_cpu    = 256
gateway_memory = 512
gateway_tasks  = 2

#apps layer
apps_cpu    = 512
apps_memory = 1024
apps_tasks  = 2

#database
db_instance_class = "db.t3.small"
db_storage_gb     = 20

#cache
cache_node_type = "cache.t3.micro"
cache_nodes     = 1
