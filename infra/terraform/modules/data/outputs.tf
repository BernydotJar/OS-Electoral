output "artifact_bucket_name" {
  value       = aws_s3_bucket.artifacts.id
  description = "Private encrypted application artifact bucket."
}

output "database_endpoint" {
  value       = aws_db_instance.postgresql.address
  description = "Private PostgreSQL endpoint."
}

output "database_secret_arn" {
  value       = try(aws_db_instance.postgresql.master_user_secret[0].secret_arn, null)
  description = "AWS-managed RDS master credential secret ARN."
  sensitive   = true
}

output "database_publicly_accessible" {
  value       = aws_db_instance.postgresql.publicly_accessible
  description = "Policy evidence: database must remain private."
}

output "database_storage_encrypted" {
  value       = aws_db_instance.postgresql.storage_encrypted
  description = "Policy evidence: database storage encryption."
}

output "database_deletion_protection" {
  value       = aws_db_instance.postgresql.deletion_protection
  description = "Policy evidence: database deletion protection."
}

output "artifact_public_access_blocked" {
  value = (
    aws_s3_bucket_public_access_block.artifacts.block_public_acls &&
    aws_s3_bucket_public_access_block.artifacts.block_public_policy &&
    aws_s3_bucket_public_access_block.artifacts.ignore_public_acls &&
    aws_s3_bucket_public_access_block.artifacts.restrict_public_buckets
  )
  description = "Policy evidence: application bucket public access is fully blocked."
}
