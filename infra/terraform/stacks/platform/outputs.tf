output "plan_policy" {
  description = "Non-secret policy evidence consumed by Terraform tests."
  value = {
    environment                    = var.environment
    nat_gateway_count              = module.network.nat_gateway_count
    private_endpoint_count         = module.network.private_endpoint_count
    kms_key_rotation_enabled       = module.security.kms_key_rotation_enabled
    database_publicly_accessible   = module.data.database_publicly_accessible
    database_storage_encrypted     = module.data.database_storage_encrypted
    database_deletion_protection   = module.data.database_deletion_protection
    artifact_public_access_blocked = module.data.artifact_public_access_blocked
    task_read_only_root_filesystem = module.runtime.task_read_only_root_filesystem
    task_runtime_user              = module.runtime.task_runtime_user
    execute_command_enabled        = module.runtime.execute_command_enabled
    ecr_scan_on_push               = module.runtime.ecr_scan_on_push
    ecr_tag_mutability             = module.runtime.ecr_tag_mutability
    task_privileged                = module.runtime.task_privileged
    load_balancer_internal         = module.runtime.load_balancer_internal
    service_count                  = module.runtime.service_count
    production_status              = "BLOCKED"
    external_effects               = "NONE"
  }
}

output "load_balancer_dns_name" {
  value       = module.runtime.load_balancer_dns_name
  description = "Non-authoritative ALB DNS output; no Route53 record is created."
}

output "database_endpoint" {
  value       = module.data.database_endpoint
  description = "Private database endpoint."
}

output "database_secret_arn" {
  value       = module.data.database_secret_arn
  description = "AWS-managed RDS credential secret ARN."
  sensitive   = true
}
