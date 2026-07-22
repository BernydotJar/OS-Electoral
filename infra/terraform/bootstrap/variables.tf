variable "aws_region" {
  description = "AWS region used only when an authorized human applies the bootstrap separately."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS region name."
  }
}

variable "project_name" {
  description = "Lowercase project identifier used in state resource names."
  type        = string
  default     = "campaignos"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "project_name must be lowercase kebab-case and 3-31 characters."
  }
}

variable "state_bucket_name" {
  description = "Globally unique S3 bucket name supplied by the authorized environment owner."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "state_bucket_name must be a valid explicit S3 bucket name."
  }
}

variable "environment_owner" {
  description = "Accountable owner label; not an email address or secret."
  type        = string

  validation {
    condition     = length(trimspace(var.environment_owner)) >= 3 && length(var.environment_owner) <= 80
    error_message = "environment_owner must contain 3-80 characters."
  }
}
