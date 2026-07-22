output "kms_key_arn" {
  value       = aws_kms_key.platform.arn
  description = "Customer-managed KMS key for platform data and logs."
}

output "kms_key_rotation_enabled" {
  value       = aws_kms_key.platform.enable_key_rotation
  description = "Policy evidence for KMS rotation."
}
