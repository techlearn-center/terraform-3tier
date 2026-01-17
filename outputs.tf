# Outputs for 3-Tier Architecture
# ================================

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  description = "Private app subnet IDs"
  value       = aws_subnet.private_app[*].id
}

output "private_db_subnet_ids" {
  description = "Private database subnet IDs"
  value       = aws_subnet.private_db[*].id
}

# ALB Outputs
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "alb_url" {
  description = "Application URL"
  value       = "http://${aws_lb.main.dns_name}"
}

# EC2 Outputs (when not using ECS)
output "web_instance_ids" {
  description = "Web tier instance IDs"
  value       = var.use_ecs ? [] : aws_instance.web[*].id
}

output "web_instance_private_ips" {
  description = "Web tier private IPs"
  value       = var.use_ecs ? [] : aws_instance.web[*].private_ip
}

output "app_instance_ids" {
  description = "App tier instance IDs"
  value       = var.use_ecs ? [] : aws_instance.app[*].id
}

output "app_instance_private_ips" {
  description = "App tier private IPs"
  value       = var.use_ecs ? [] : aws_instance.app[*].private_ip
}

# ECS Outputs (when using ECS)
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = var.use_ecs ? aws_ecs_cluster.main[0].name : null
}

output "ecs_web_service_name" {
  description = "ECS web service name"
  value       = var.use_ecs ? aws_ecs_service.web[0].name : null
}

output "ecs_app_service_name" {
  description = "ECS app service name"
  value       = var.use_ecs ? aws_ecs_service.app[0].name : null
}

# RDS Outputs
output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "web_security_group_id" {
  description = "Web tier security group ID"
  value       = aws_security_group.web.id
}

output "app_security_group_id" {
  description = "App tier security group ID"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}

# Summary Output
output "summary" {
  description = "Infrastructure summary"
  value = <<-EOT

    ============================================
    3-Tier Architecture Deployment Summary
    ============================================

    Mode: ${var.use_ecs ? "ECS/Fargate (Containerized)" : "EC2 (Traditional)"}

    Application URL: http://${aws_lb.main.dns_name}

    VPC: ${aws_vpc.main.id}
    - Public Subnets: ${join(", ", aws_subnet.public[*].id)}
    - App Subnets: ${join(", ", aws_subnet.private_app[*].id)}
    - DB Subnets: ${join(", ", aws_subnet.private_db[*].id)}

    ${var.use_ecs ? "ECS Cluster: ${aws_ecs_cluster.main[0].name}" : "Web Instances: ${join(", ", aws_instance.web[*].id)}"}
    ${var.use_ecs ? "Web Service: ${aws_ecs_service.web[0].name}" : "App Instances: ${join(", ", aws_instance.app[*].id)}"}

    Database: ${aws_db_instance.main.endpoint}

    ============================================
  EOT
}
