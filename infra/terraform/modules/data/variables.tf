variable "name_prefix" {
  type        = string
  description = "Validated lowercase resource-name prefix."
}

variable "vpc_id" {
  type        = string
  description = "VPC containing the private data tier."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "At least two isolated subnet identifiers."

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "private_subnet_ids must contain at least two subnets."
  }
}

variable "application_security_group_id" {
  type        = string
  description = "Only security group permitted to connect to PostgreSQL."
}

variable "kms_key_arn" {
  type        = string
  description = "Customer-managed key for database, secret and S3 encryption."
}

variable "artifact_bucket_name" {
  type        = string
  description = "Globally unique application artifact bucket name."
}

variable "database_identifier" {
  type        = string
  description = "Explicit RDS identifier."
}

variable "database_instance_class" {
  type        = string
  description = "RDS instance class selected by the environment owner."
  default     = "db.t4g.small"
}

variable "database_allocated_storage_gib" {
  type        = number
  description = "Initial encrypted gp3 storage."
  default     = 20

  validation {
    condition     = var.database_allocated_storage_gib >= 20 && var.database_allocated_storage_gib <= 65536
    error_message = "database_allocated_storage_gib must be between 20 and 65536."
  }
}

variable "database_max_storage_gib" {
  type        = number
  description = "Autoscaling ceiling."
  default     = 100
}

variable "database_backup_retention_days" {
  type        = number
  description = "Automated backup retention."
  default     = 7

  validation {
    condition     = var.database_backup_retention_days >= 7 && var.database_backup_retention_days <= 35
    error_message = "database_backup_retention_days must be between 7 and 35."
  }
}

variable "database_multi_az" {
  type        = bool
  description = "Enable Multi-AZ for approved staging/production environments."
  default     = false
}

variable "database_deletion_protection" {
  type        = bool
  description = "Deletion protection must remain enabled outside disposable test plans."
  default     = true
}
