mock_provider "aws" {}

run "secure_state_plan" {
  command = plan

  variables {
    state_bucket_name = "campaignos-test-state-example"
    environment_owner = "platform-team"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.terraform_state.block_public_policy
    error_message = "Terraform state bucket must block public policy."
  }

  assert {
    condition     = aws_s3_bucket_versioning.terraform_state.versioning_configuration[0].status == "Enabled"
    error_message = "Terraform state versioning must remain enabled."
  }

  assert {
    condition     = aws_kms_key.terraform_state.enable_key_rotation
    error_message = "Terraform state KMS rotation must remain enabled."
  }

  assert {
    condition     = output.backend_configuration.use_lockfile && output.backend_configuration.encrypt
    error_message = "Backend configuration must use S3 locking and encryption."
  }
}
