data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name       = "${var.project_name}-${var.environment}"
  azs        = slice(data.aws_availability_zones.available.names, 0, 2)
  api_image  = "ghcr.io/${var.container_image_owner}/devlink-api:${var.image_tag}"
  web_image  = "ghcr.io/${var.container_image_owner}/devlink-web:${var.image_tag}"
  work_image = "ghcr.io/${var.container_image_owner}/devlink-analytics-worker:${var.image_tag}"

  registry_credentials = var.container_registry_credentials_secret_arn == "" ? {} : {
    repositoryCredentials = {
      credentialsParameter = var.container_registry_credentials_secret_arn
    }
  }

  common_environment = [
    { name = "APP_ENV", value = "production" },
    { name = "JWT_ALGORITHM", value = "HS256" },
    { name = "REDIS_URL", value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0" },
    { name = "KAFKA_BROKERS", value = "kafka.${aws_service_discovery_private_dns_namespace.this.name}:9092" },
    { name = "CORS_ALLOWED_ORIGINS", value = "http://${aws_lb.app.dns_name}" },
    { name = "ALLOW_PRIVATE_REDIRECT_URLS", value = "false" },
    { name = "DB_POOL_SIZE", value = "5" },
    { name = "DB_MAX_OVERFLOW", value = "5" },
    { name = "REDIS_MAX_CONNECTIONS", value = "50" },
    { name = "LOG_LEVEL", value = "INFO" }
  ]

  app_secrets = [
    { name = "DATABASE_URL", valueFrom = "${var.app_secrets_arn}:DATABASE_URL::" },
    { name = "JWT_SECRET", valueFrom = "${var.app_secrets_arn}:JWT_SECRET::" }
  ]

  worker_secrets = [
    { name = "DATABASE_URL", valueFrom = "${var.app_secrets_arn}:DATABASE_URL::" },
    { name = "IP_HASH_SECRET", valueFrom = "${var.app_secrets_arn}:IP_HASH_SECRET::" }
  ]
}

resource "aws_vpc" "this" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = local.name
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = local.name
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index + 10)
  availability_zone = local.azs[count.index]

  tags = {
    Name = "${local.name}-private-${count.index + 1}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${local.name}-public"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "Public HTTP access to the application load balancer."
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "ALB to ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.this.cidr_block]
  }
}

resource "aws_security_group" "ecs" {
  name        = "${local.name}-ecs"
  description = "ECS service-to-service and ALB ingress."
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "API from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Web from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "Internal API metrics/debug access from ECS tasks"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "Internal worker metrics access from ECS tasks"
    from_port   = 9101
    to_port     = 9101
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "Kafka-compatible broker from ECS tasks"
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    self        = true
  }

  egress {
    description = "Outbound internet and private AWS services"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database" {
  name        = "${local.name}-database"
  description = "Postgres and Redis access from ECS tasks only."
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "Postgres from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_db_subnet_group" "this" {
  name       = local.name
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier                  = local.name
  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage_gb
  db_name                     = var.db_name
  username                    = var.db_username
  manage_master_user_password = true
  db_subnet_group_name        = aws_db_subnet_group.this.name
  vpc_security_group_ids      = [aws_security_group.database.id]
  publicly_accessible         = false
  multi_az                    = false
  backup_retention_period     = 1
  deletion_protection         = var.enable_deletion_protection
  skip_final_snapshot         = var.skip_final_snapshot
}

resource "aws_elasticache_subnet_group" "this" {
  name       = local.name
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = local.name
  description                = "DEVLINK Redis cache"
  engine                     = "redis"
  node_type                  = var.redis_node_type
  port                       = 6379
  num_cache_clusters         = 1
  automatic_failover_enabled = false
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.database.id]
}

resource "aws_lb" "app" {
  name               = local.name
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  deletion_protection = var.enable_deletion_protection
}

resource "aws_lb_target_group" "api" {
  name        = "${local.name}-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.this.id

  health_check {
    path                = "/health"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "web" {
  name        = "${local.name}-web"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.this.id

  health_check {
    path                = "/health"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health"]
    }
  }
}

resource "aws_lb_listener_rule" "redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/r/*"]
    }
  }
}

resource "aws_ecs_cluster" "this" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_service_discovery_private_dns_namespace" "this" {
  name        = "${local.name}.local"
  description = "Private service discovery namespace for DEVLINK ECS tasks."
  vpc         = aws_vpc.this.id
}

resource "aws_service_discovery_service" "kafka" {
  name = "kafka"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.this.id

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name}/api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.name}/analytics-worker"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${local.name}/web"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "kafka" {
  name              = "/ecs/${local.name}/kafka"
  retention_in_days = 7
}

resource "aws_iam_role" "task_execution" {
  name = "${local.name}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "secrets" {
  name = "${local.name}-ecs-secrets"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = compact([
        var.app_secrets_arn,
        "${var.app_secrets_arn}*",
        var.container_registry_credentials_secret_arn,
        var.container_registry_credentials_secret_arn == "" ? "" : "${var.container_registry_credentials_secret_arn}*"
      ])
    }]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name}-ecs-task"

  assume_role_policy = aws_iam_role.task_execution.assume_role_policy
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    merge(local.registry_credentials, {
      name      = "api"
      image     = local.api_image
      essential = true
      command = [
        "sh",
        "-c",
        "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"
      ]
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      environment  = local.common_environment
      secrets      = local.app_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    })
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name}-analytics-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    merge(local.registry_credentials, {
      name        = "analytics-worker"
      image       = local.work_image
      essential   = true
      environment = concat(local.common_environment, [
        { name = "CLICK_EVENTS_TOPIC", value = "click-events" },
        { name = "METRICS_PORT", value = "9101" }
      ])
      secrets     = local.worker_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "worker"
        }
      }
    })
  ])
}

resource "aws_ecs_task_definition" "web" {
  family                   = "${local.name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.web_cpu
  memory                   = var.web_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    merge(local.registry_credentials, {
      name      = "web"
      image     = local.web_image
      essential = true
      portMappings = [{ containerPort = 80, protocol = "tcp" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.web.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "web"
        }
      }
    })
  ])
}

resource "aws_ecs_task_definition" "kafka" {
  family                   = "${local.name}-kafka"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.kafka_cpu
  memory                   = var.kafka_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "kafka"
      image     = "bitnami/kafka:3.7"
      essential = true
      portMappings = [{ containerPort = 9092, protocol = "tcp" }]
      environment = [
        { name = "KAFKA_CFG_NODE_ID", value = "1" },
        { name = "KAFKA_CFG_PROCESS_ROLES", value = "controller,broker" },
        { name = "KAFKA_CFG_CONTROLLER_QUORUM_VOTERS", value = "1@localhost:9093" },
        { name = "KAFKA_CFG_LISTENERS", value = "PLAINTEXT://:9092,CONTROLLER://:9093" },
        { name = "KAFKA_CFG_ADVERTISED_LISTENERS", value = "PLAINTEXT://kafka.${aws_service_discovery_private_dns_namespace.this.name}:9092" },
        { name = "KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP", value = "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT" },
        { name = "KAFKA_CFG_CONTROLLER_LISTENER_NAMES", value = "CONTROLLER" },
        { name = "KAFKA_CFG_INTER_BROKER_LISTENER_NAME", value = "PLAINTEXT" },
        { name = "KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE", value = "true" },
        { name = "ALLOW_PLAINTEXT_LISTENER", value = "yes" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.kafka.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "kafka"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "kafka" {
  name            = "${local.name}-kafka"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.kafka.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.kafka.arn
  }
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http, aws_ecs_service.kafka]
}

resource "aws_ecs_service" "worker" {
  name            = "${local.name}-analytics-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  depends_on = [aws_ecs_service.kafka, aws_ecs_service.api]
}

resource "aws_ecs_service" "web" {
  name            = "${local.name}-web"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${local.name}-api-5xx"
  alarm_description   = "API target group returned too many 5xx responses."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "api_unhealthy_hosts" {
  alarm_name          = "${local.name}-api-unhealthy-hosts"
  alarm_description   = "At least one API target is unhealthy behind the ALB."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "web_unhealthy_hosts" {
  alarm_name          = "${local.name}-web-unhealthy-hosts"
  alarm_description   = "At least one web target is unhealthy behind the ALB."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
    TargetGroup  = aws_lb_target_group.web.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name}-rds-cpu-high"
  alarm_description   = "RDS CPU is high for the minimal Postgres instance."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${local.name}-rds-connections-high"
  alarm_description   = "RDS connection count is high for a small instance."
  namespace           = "AWS/RDS"
  metric_name         = "DatabaseConnections"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "${local.name}-api-cpu-high"
  alarm_description   = "API ECS service CPU utilization is high."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.this.name
    ServiceName = aws_ecs_service.api.name
  }
}

resource "aws_cloudwatch_metric_alarm" "worker_cpu_high" {
  alarm_name          = "${local.name}-worker-cpu-high"
  alarm_description   = "Analytics worker ECS service CPU utilization is high."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.this.name
    ServiceName = aws_ecs_service.worker.name
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = local.name

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title   = "ALB API 5xx and Target Health"
          region  = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.app.arn_suffix, "TargetGroup", aws_lb_target_group.api.arn_suffix, { stat = "Sum" }],
            [".", "UnHealthyHostCount", ".", ".", ".", ".", { stat = "Maximum" }]
          ]
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title   = "ECS CPU"
          region  = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.this.name, "ServiceName", aws_ecs_service.api.name],
            [".", ".", ".", ".", "ServiceName", aws_ecs_service.worker.name],
            [".", ".", ".", ".", "ServiceName", aws_ecs_service.web.name]
          ]
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title   = "RDS CPU and Connections"
          region  = var.aws_region
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.postgres.identifier],
            [".", "DatabaseConnections", ".", "."]
          ]
        }
      }
    ]
  })
}
