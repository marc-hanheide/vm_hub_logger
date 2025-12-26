variable "DEFAULT_TAG" {
  default = "ghcr.io/marc-hanheide/vm_hub_logger:latest"
}

group "default" {
  targets = ["vm-hub-logger"]
}

target "vm-hub-logger" {
  context    = "."
  dockerfile = "Dockerfile"
  tags       = [DEFAULT_TAG]
  platforms  = [
    "linux/amd64",
    "linux/arm64",
    "linux/arm/v7"
  ]
}
