locals {
  ecr_scan_on_push       = true
  ecr_tag_mutability     = "IMMUTABLE"
  task_privileged        = false
  load_balancer_internal = false

  ecs_tasks_assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  services = {
    backend = {
      image         = var.backend_image
      port          = 8000
      cpu           = 512
      memory        = 1024
      desired_count = var.backend_desired_count
      health_path   = "/api/v1/health"
      command       = []
    }
    frontend = {
      image         = var.frontend_image
      port          = 3000
      cpu           = 512
      memory        = 1024
      desired_count = var.frontend_desired_count
      health_path   = "/"
      command       = []
    }
  }
}

resource "aws_ecr_repository" "service" {
  for_each = local.services

  name                 = "${var.name_prefix}-${each.key}"
  image_tag_mutability = local.ecr_tag_mutability

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn
  }

  image_scanning_configuration {
    scan_on_push = local.ecr_scan_on_push
  }
}

resource "aws_ecr_lifecycle_policy" "service" {
  for_each = aws_ecr_repository.service

  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Retain the 30 most recent immutable images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 30
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enhanced"
  }
}

resource "aws_cloudwatch_log_group" "service" {
  for_each = local.services

  name              = "/campaignos/${var.environment}/${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.name_prefix}-task-execution"
  assume_role_policy = local.ecs_tasks_assume_role_policy
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:${var.aws_partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name               = "${var.name_prefix}-task"
  assume_role_policy = local.ecs_tasks_assume_role_policy
}

resource "aws_security_group" "load_balancer" {
  name_prefix = "${var.name_prefix}-alb-"
  description = "Public HTTPS ingress to the CampaignOS load balancer"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_http" {
  security_group_id = aws_security_group.load_balancer.id
  description       = "HTTP redirect or fail-closed response"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_https" {
  security_group_id = aws_security_group.load_balancer.id
  description       = "HTTPS ingress"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_security_group" "application" {
  name_prefix = "${var.name_prefix}-app-"
  description = "Private Fargate application tasks"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "application" {
  for_each = local.services

  security_group_id            = aws_security_group.application.id
  referenced_security_group_id = aws_security_group.load_balancer.id
  description                  = "${each.key} traffic from ALB"
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "application_tls" {
  security_group_id = aws_security_group.application.id
  description       = "TLS to VPC endpoints"
  cidr_ipv4         = var.vpc_cidr
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "application_postgresql" {
  security_group_id = aws_security_group.application.id
  description       = "PostgreSQL within the VPC"
  cidr_ipv4         = var.vpc_cidr
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "application_dns_udp" {
  security_group_id = aws_security_group.application.id
  description       = "DNS within the VPC"
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
}

resource "aws_vpc_security_group_egress_rule" "application_dns_tcp" {
  security_group_id = aws_security_group.application.id
  description       = "DNS TCP fallback within the VPC"
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "load_balancer" {
  for_each = local.services

  security_group_id            = aws_security_group.load_balancer.id
  referenced_security_group_id = aws_security_group.application.id
  description                  = "ALB to ${each.key} tasks"
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_lb" "this" {
  name                       = substr("${var.name_prefix}-alb", 0, 32)
  internal                   = local.load_balancer_internal
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.load_balancer.id]
  subnets                    = var.public_subnet_ids
  drop_invalid_header_fields = true
  enable_deletion_protection = var.load_balancer_deletion_protection
}

resource "aws_lb_target_group" "service" {
  for_each = local.services

  name        = substr("${var.name_prefix}-${each.key}", 0, 32)
  port        = each.value.port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    protocol            = "HTTP"
    path                = each.value.health_path
    matcher             = "200-399"
  }
}

resource "aws_lb_listener" "http_redirect" {
  count = var.certificate_arn == null ? 0 : 1

  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "http_blocked" {
  count = var.certificate_arn == null ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "HTTPS certificate is not configured"
      status_code  = "503"
    }
  }
}

resource "aws_lb_listener" "https" {
  count = var.certificate_arn == null ? 0 : 1

  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service["frontend"].arn
  }
}

resource "aws_lb_listener_rule" "backend" {
  count = var.certificate_arn == null ? 0 : 1

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service["backend"].arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

resource "aws_ecs_task_definition" "service" {
  for_each = local.services

  family                   = "${var.name_prefix}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  ephemeral_storage {
    size_in_gib = 21
  }

  container_definitions = jsonencode([{
    name                   = each.key
    image                  = each.value.image
    essential              = true
    readonlyRootFilesystem = true
    privileged             = local.task_privileged
    user                   = "10001:10001"
    command                = each.value.command
    portMappings = [{
      containerPort = each.value.port
      hostPort      = each.value.port
      protocol      = "tcp"
      appProtocol   = "http"
    }]
    environment = [
      { name = "CAMPAIGNOS_ENVIRONMENT", value = var.environment },
      { name = "CAMPAIGNOS_EXTERNAL_EFFECTS", value = "NONE" },
    ]
    linuxParameters = {
      initProcessEnabled = true
      capabilities = {
        add  = []
        drop = ["ALL"]
      }
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.service[each.key].name
        awslogs-region        = data.aws_region.current.region
        awslogs-stream-prefix = each.key
      }
    }
  }])
}

resource "aws_ecs_service" "service" {
  for_each = var.enable_services ? local.services : {}

  name                               = "${var.name_prefix}-${each.key}"
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.service[each.key].arn
  launch_type                        = "FARGATE"
  desired_count                      = each.value.desired_count
  enable_execute_command             = false
  health_check_grace_period_seconds  = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.application.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.service[each.key].arn
    container_name   = each.key
    container_port   = each.value.port
  }

  lifecycle {
    precondition {
      condition     = var.certificate_arn != null
      error_message = "ECS services require a pre-approved ACM certificate ARN."
    }
  }

  depends_on = [aws_lb_listener.https]
}

data "aws_region" "current" {}
