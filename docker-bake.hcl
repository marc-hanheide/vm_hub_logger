

group "default" {
  targets = ["vm-hub-logger"]
}

target "docker-metadata-action" {}

target "vm-hub-logger" {
  inherits = ["docker-metadata-action"]
  context    = "."
  dockerfile = "Dockerfile"
  platforms  = [
    "linux/amd64",
    "linux/arm64",
    "linux/arm/v7"
  ]
}
