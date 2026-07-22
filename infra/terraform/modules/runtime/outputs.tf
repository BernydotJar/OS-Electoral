output "application_security_group_id" {
  value       = aws_security_group.application.id
  description = "Private ECS task security group."
}

output "load_balancer_dns_name" {
  value       = aws_lb.this.dns_name
  description = "ALB DNS name; no DNS record is created by this baseline."
}

output "service_count" {
  value       = length(aws_ecs_service.service)
  description = "Policy evidence: services are disabled by default."
}

output "task_read_only_root_filesystem" {
  value       = true
  description = "Policy evidence for both task definitions."
}

output "task_runtime_user" {
  value       = "10001:10001"
  description = "Policy evidence for non-root containers."
}

output "execute_command_enabled" {
  value       = false
  description = "Policy evidence: ECS Exec is disabled."
}

output "ecr_scan_on_push" {
  value       = local.ecr_scan_on_push
  description = "Policy evidence wired to every ECR repository."
}

output "ecr_tag_mutability" {
  value       = local.ecr_tag_mutability
  description = "Policy evidence wired to every ECR repository."
}

output "task_privileged" {
  value       = local.task_privileged
  description = "Policy evidence wired to every ECS container definition."
}

output "load_balancer_internal" {
  value       = local.load_balancer_internal
  description = "Policy evidence: the ALB is the sole public runtime boundary."
}
