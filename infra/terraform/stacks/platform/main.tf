locals {
  name_prefix = "campaignos-${var.environment}"
  required_tags = {
    Application       = "CampaignOS"
    Environment       = var.environment
    EnvironmentOwner  = var.environment_owner
    ManagedBy         = "Terraform"
    ProductionStatus  = "BLOCKED"
    ExternalEffects   = "NONE"
    CostAuthorization = "REQUIRES_EXPLICIT_HUMAN_APPROVAL"
  }
}

module "security" {
  source = "../../modules/security"

  name_prefix = local.name_prefix
}

module "network" {
  source = "../../modules/network"

  name_prefix              = local.name_prefix
  vpc_cidr                 = var.vpc_cidr
  availability_zones       = var.availability_zones
  enable_private_endpoints = true
}

module "runtime" {
  source = "../../modules/runtime"

  name_prefix        = local.name_prefix
  environment        = var.environment
  aws_partition      = var.aws_partition
  vpc_id             = module.network.vpc_id
  vpc_cidr           = module.network.vpc_cidr
  public_subnet_ids  = module.network.public_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids
  kms_key_arn        = module.security.kms_key_arn
  backend_image      = var.backend_image
  frontend_image     = var.frontend_image
  certificate_arn    = var.certificate_arn
  enable_services    = var.enable_services
  log_retention_days = var.log_retention_days

  backend_desired_count  = var.enable_services ? 2 : 0
  frontend_desired_count = var.enable_services ? 2 : 0
}

module "data" {
  source = "../../modules/data"

  name_prefix                    = local.name_prefix
  vpc_id                         = module.network.vpc_id
  private_subnet_ids             = module.network.private_subnet_ids
  application_security_group_id  = module.runtime.application_security_group_id
  kms_key_arn                    = module.security.kms_key_arn
  artifact_bucket_name           = var.artifact_bucket_name
  database_identifier            = var.database_identifier
  database_instance_class        = var.database_instance_class
  database_multi_az              = var.database_multi_az
  database_deletion_protection   = true
  database_backup_retention_days = var.environment == "production" ? 35 : 7
}
