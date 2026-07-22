mock_provider "aws" {}

run "secure_platform_plan" {
  command = plan

  variables {
    environment          = "dev"
    environment_owner    = "platform-team"
    availability_zones   = ["us-east-1a", "us-east-1b"]
    vpc_cidr             = "10.42.0.0/16"
    artifact_bucket_name = "campaignos-test-artifacts-example"
    database_identifier  = "campaignos-test"
    backend_image        = "example.invalid/campaignos-backend@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    frontend_image       = "example.invalid/campaignos-frontend@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    certificate_arn      = null
    enable_services      = false
  }

  assert {
    condition     = output.plan_policy.nat_gateway_count == 0
    error_message = "Plan-only baseline must not create NAT gateways."
  }

  assert {
    condition     = output.plan_policy.private_endpoint_count == 6
    error_message = "Private application subnets require five interface endpoints and one S3 gateway endpoint."
  }

  assert {
    condition     = !output.plan_policy.database_publicly_accessible
    error_message = "PostgreSQL must remain private."
  }

  assert {
    condition     = output.plan_policy.database_storage_encrypted && output.plan_policy.database_deletion_protection
    error_message = "PostgreSQL encryption and deletion protection must remain enabled."
  }

  assert {
    condition     = output.plan_policy.artifact_public_access_blocked
    error_message = "Application object storage must block all public access modes."
  }

  assert {
    condition     = output.plan_policy.task_read_only_root_filesystem && output.plan_policy.task_runtime_user == "10001:10001"
    error_message = "Fargate containers must remain non-root with read-only root filesystems."
  }

  assert {
    condition     = !output.plan_policy.execute_command_enabled
    error_message = "ECS Exec must remain disabled."
  }

  assert {
    condition     = output.plan_policy.ecr_scan_on_push && output.plan_policy.ecr_tag_mutability == "IMMUTABLE"
    error_message = "ECR must scan on push and use immutable tags."
  }

  assert {
    condition     = output.plan_policy.service_count == 0
    error_message = "ECS services must remain disabled by default."
  }

  assert {
    condition     = output.plan_policy.production_status == "BLOCKED" && output.plan_policy.external_effects == "NONE"
    error_message = "Infrastructure plans must preserve blocked production and zero external effects."
  }

  assert {
    condition     = !output.plan_policy.load_balancer_internal
    error_message = "Only the hardened load balancer may be public."
  }

  assert {
    condition     = !output.plan_policy.task_privileged
    error_message = "No ECS task may be privileged."
  }
}
