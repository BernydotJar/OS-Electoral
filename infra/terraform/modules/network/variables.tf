variable "name_prefix" {
  type        = string
  description = "Validated lowercase resource-name prefix."
}

variable "vpc_cidr" {
  type        = string
  description = "RFC1918 VPC CIDR."

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be valid CIDR notation."
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "At least two explicit AZ names; no account discovery is performed during tests."

  validation {
    condition     = length(var.availability_zones) >= 2 && length(var.availability_zones) <= 3 && length(distinct(var.availability_zones)) == length(var.availability_zones)
    error_message = "availability_zones must contain two or three unique zones."
  }
}

variable "enable_private_endpoints" {
  type        = bool
  description = "Create private endpoints required by isolated ECS tasks."
  default     = true
}
