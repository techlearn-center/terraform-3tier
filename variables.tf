# Variables for 3-Tier Architecture
# ==================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "terraform-3tier"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

# VPC Variables
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# EC2 Variables
variable "web_instance_count" {
  description = "Number of web tier instances"
  type        = number
  default     = 2
}

variable "web_instance_type" {
  description = "Web tier instance type"
  type        = string
  default     = "t2.micro"
}

variable "app_instance_count" {
  description = "Number of app tier instances"
  type        = number
  default     = 2
}

variable "app_instance_type" {
  description = "App tier instance type"
  type        = string
  default     = "t2.micro"
}

# RDS Variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = "changeme123!"
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

# Security Variables
variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

# ECS Variables (for containerized path)
variable "use_ecs" {
  description = "Use ECS instead of EC2 for web/app tiers"
  type        = bool
  default     = false
}

variable "web_container_image" {
  description = "Docker image for web tier"
  type        = string
  default     = "nginx:latest"
}

variable "app_container_image" {
  description = "Docker image for app tier"
  type        = string
  default     = "node:18-alpine"
}
