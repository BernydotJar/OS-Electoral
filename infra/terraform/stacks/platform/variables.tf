variable "aws_region" {
  type        = string
  description = "Explicit target region selected by the environment owner."
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS region name."
  }
}

variable "aws_partition" {
  type        = string
  description = "AWS partition; no account discovery is performed in plan tests."
  default     = "aws"
}

variable "environment" {
  type        = string
  description = "Isolated environment name."

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "environment_owner" {
  type        = string
  description = "Accountable owner label; never a secret."

  validation {
    condition     = length(trimspace(var.environment_owner)) >= 3 && length(var.environment_owner) <= 80
    error_message = "environment_owner must contain 3-80 characters."
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "Two or three explicit AZ names."
}

variable "vpc_cidr" {
  type        = string
  description = "Environment-specific RFC1918 CIDR."
}

variable "artifact_bucket_name" {
  type        = string
  description = "Globally unique private application bucket."
}

variable "database_identifier" {
  type        = string
  description = "Environment-specific RDS identifier."
}

variable "database_instance_class" {
  type        = string
  description = "RDS class selected after cost and capacity review."
  default     = "db.t4g.small"
}

variable "database_multi_az" {
  type        = bool
  description = "Enable only after environment approval."
  default     = false
}

variable "backend_image" {
  type        = string
  description = "Immutable backend image digest."
}

variable "frontend_image" {
  type        = string
  description = "Immutable frontend image digest."
}

variable "certificate_arn" {
  type        = string
  description = "Pre-existing approved ACM certificate ARN; this stack never requests one."
  default     = null
  nullable    = true
}

variable "enable_services" {
  type        = bool
  description = "Services remain disabled until an environment and certificate are approved."
  default     = false
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention."
  default     = 30
}
