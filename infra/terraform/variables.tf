variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for AWS resources."
  type        = string
  default     = "devlink"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "container_image_owner" {
  description = "Lowercase GHCR owner or organization."
  type        = string
}

variable "image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "latest"
}

variable "app_secrets_arn" {
  description = "Secrets Manager secret ARN containing DATABASE_URL, JWT_SECRET, and IP_HASH_SECRET JSON keys."
  type        = string
}

variable "container_registry_credentials_secret_arn" {
  description = "Optional Secrets Manager ARN for private GHCR pull credentials. Leave empty for public images."
  type        = string
  default     = ""
}

variable "db_name" {
  description = "Initial Postgres database name."
  type        = string
  default     = "devlink"
}

variable "db_username" {
  description = "RDS master username. The password is managed by AWS Secrets Manager."
  type        = string
  default     = "devlink"
}

variable "db_instance_class" {
  description = "RDS instance class for the minimal deployment."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  description = "Allocated RDS storage in GiB."
  type        = number
  default     = 20
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type for the minimal deployment."
  type        = string
  default     = "cache.t4g.micro"
}

variable "api_cpu" {
  description = "API task CPU units."
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "API task memory in MiB."
  type        = number
  default     = 512
}

variable "worker_cpu" {
  description = "Analytics worker task CPU units."
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Analytics worker task memory in MiB."
  type        = number
  default     = 512
}

variable "web_cpu" {
  description = "Web task CPU units."
  type        = number
  default     = 256
}

variable "web_memory" {
  description = "Web task memory in MiB."
  type        = number
  default     = 512
}

variable "kafka_cpu" {
  description = "Minimal Kafka-compatible broker task CPU units."
  type        = number
  default     = 512
}

variable "kafka_memory" {
  description = "Minimal Kafka-compatible broker task memory in MiB."
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "API task count."
  type        = number
  default     = 1
}

variable "web_desired_count" {
  description = "Web task count."
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Worker task count."
  type        = number
  default     = 1
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection on ALB and RDS."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final RDS snapshot during destroy. Keep true for cheap ephemeral portfolio environments."
  type        = bool
  default     = true
}
