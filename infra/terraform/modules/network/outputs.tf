output "vpc_id" {
  value       = aws_vpc.this.id
  description = "Platform VPC identifier."
}

output "vpc_cidr" {
  value       = aws_vpc.this.cidr_block
  description = "Platform VPC CIDR."
}

output "public_subnet_ids" {
  value       = [for zone in var.availability_zones : aws_subnet.public[zone].id]
  description = "Public load-balancer subnet identifiers."
}

output "private_subnet_ids" {
  value       = [for zone in var.availability_zones : aws_subnet.private[zone].id]
  description = "Isolated application/data subnet identifiers."
}

output "nat_gateway_count" {
  value       = 0
  description = "Policy evidence: this baseline never creates NAT gateways."
}

output "private_endpoint_count" {
  value       = var.enable_private_endpoints ? length(local.interface_services) + 1 : 0
  description = "Interface plus S3 gateway endpoint count."
}
