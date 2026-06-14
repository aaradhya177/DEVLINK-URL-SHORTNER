output "alb_dns_name" {
  description = "Public ALB DNS name for the deployed app."
  value       = aws_lb.app.dns_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name for GitHub Actions deployment."
  value       = aws_ecs_cluster.this.name
}

output "api_service_name" {
  description = "API ECS service name for GitHub Actions deployment."
  value       = aws_ecs_service.api.name
}

output "worker_service_name" {
  description = "Analytics worker ECS service name for GitHub Actions deployment."
  value       = aws_ecs_service.worker.name
}

output "web_service_name" {
  description = "Web ECS service name for GitHub Actions deployment."
  value       = aws_ecs_service.web.name
}

output "rds_endpoint" {
  description = "RDS endpoint used when creating the app DATABASE_URL secret."
  value       = aws_db_instance.postgres.address
}

output "rds_master_user_secret_arn" {
  description = "AWS-managed RDS master-user secret ARN."
  value       = aws_db_instance.postgres.master_user_secret[0].secret_arn
  sensitive   = true
}
