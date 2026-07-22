output "state_bucket_name" {
  description = "S3 bucket for partial backend configuration."
  value       = aws_s3_bucket.terraform_state.id
}

output "state_kms_key_arn" {
  description = "KMS key ARN for Terraform state encryption."
  value       = aws_kms_key.terraform_state.arn
}

output "backend_configuration" {
  description = "Non-secret values used in an authorized backend.hcl file."
  value = {
    bucket       = aws_s3_bucket.terraform_state.id
    region       = var.aws_region
    kms_key_id   = aws_kms_key.terraform_state.arn
    encrypt      = true
    use_lockfile = true
  }
}
