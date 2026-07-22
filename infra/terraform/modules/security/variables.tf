variable "name_prefix" {
  type        = string
  description = "Validated lowercase resource-name prefix."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,40}$", var.name_prefix))
    error_message = "name_prefix must be lowercase kebab-case."
  }
}
