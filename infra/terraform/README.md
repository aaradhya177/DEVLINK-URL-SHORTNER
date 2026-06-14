# DEVLINK AWS Terraform

This Terraform stack is the cost-conscious AWS deployment path for DEVLINK.

It intentionally uses ECS Fargate, RDS Postgres, ElastiCache Redis, an ALB, and
a small single-broker Kafka-compatible ECS service instead of MSK. That keeps
the portfolio deployment understandable and relatively cheap. For a higher-scale
discussion architecture, replace the broker service with MSK or a managed queue
and move ECS tasks into private subnets behind NAT gateways or VPC endpoints.

Secrets are referenced from AWS Secrets Manager by ARN. Do not put secret values
in `.tfvars` files.
