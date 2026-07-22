variable "name_prefix" {
  type        = string
  description = "Validated lowercase resource-name prefix."
}

variable "environment" {
  type        = string
  description = "Environment label exposed to containers."
}

variable "aws_partition" {
  type        = string
  description = "AWS partition used to construct managed-policy ARNs without account discovery."
  default     = "aws"

  validation {
    condition     = contains(["aws", "aws-us-gov", "aws-cn"], var.aws_partition)
    error_message = "aws_partition must be aws, aws-us-gov, or aws-cn."
  }
}

variable "vpc_id" {
  type        = string
  description = "Platform VPC identifier."
}

variable "vpc_cidr" {
  type        = string
  description = "Platform VPC CIDR for bounded egress."
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnets for the ALB."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnets for Fargate services."
}

variable "kms_key_arn" {
  type        = string
  description = "Customer-managed KMS key for logs and ECR."
}

variable "backend_image" {
  type        = string
  description = "Immutable backend OCI image reference by sha256 digest."

  validation {
    condition     = can(regex("^[^[:space:]]+@sha256:[0-9a-f]{64}$", var.backend_image))
    error_message = "backend_image must be an immutable OCI image digest."
  }
}

variable "frontend_image" {
  type        = string
  description = "Immutable frontend OCI image reference by sha256 digest."

  validation {
    condition     = can(regex("^[^[:space:]]+@sha256:[0-9a-f]{64}$", var.frontend_image))
    error_message = "frontend_image must be an immutable OCI image digest."
  }
}

variable "certificate_arn" {
  type        = string
  description = "Optional pre-approved ACM certificate ARN. No certificate is requested by this baseline."
  default     = null
  nullable    = true
}

variable "enable_services" {
  type        = bool
  description = "Create ECS services only after an approved certificate and environment exist."
  default     = false
}

variable "backend_desired_count" {
  type        = number
  description = "Desired backend tasks when services are explicitly enabled."
  default     = 0
}

variable "frontend_desired_count" {
  type        = number
  description = "Desired frontend tasks when services are explicitly enabled."
  default     = 0
}

variable "load_balancer_deletion_protection" {
  type        = bool
  description = "Protect an approved load balancer from accidental deletion."
  default     = true
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention."
  default     = 30

  validation {
    condition     = contains([30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "log_retention_days must be a supported CloudWatch retention value of at least 30 days."
  }
}
