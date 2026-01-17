# ECS/Fargate for 3-Tier Architecture - BONUS STARTER FILE
# ==========================================================
# This is an OPTIONAL advanced challenge!
#
# Set use_ecs = true in terraform.tfvars to use containers
# instead of EC2 instances.
#
# ECS/Fargate provides:
# - Serverless containers (no EC2 management)
# - Automatic scaling
# - Better resource utilization
# - Simplified deployments
#
# This file is more complex and is intended for students
# who want to explore containerized infrastructure.
#
# See README.md for detailed guidance!

# =============================================================================
# STEP 1: Create ECS Cluster
# =============================================================================
# TODO: Create an ECS cluster for Fargate tasks
#
# resource "aws_ecs_cluster" "main" {
#   count = var.use_ecs ? 1 : 0
#   name  = "${var.project_name}-cluster"
#
#   setting {
#     name  = "containerInsights"
#     value = "enabled"
#   }
#
#   tags = {
#     Name = "${var.project_name}-cluster"
#   }
# }

# =============================================================================
# STEP 2: Create IAM Roles for ECS
# =============================================================================
# TODO: Create execution role (for pulling images, writing logs)
#
# resource "aws_iam_role" "ecs_execution" {
#   count = var.use_ecs ? 1 : 0
#   name  = "${var.project_name}-ecs-execution"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = {
#     Name = "${var.project_name}-ecs-execution-role"
#   }
# }
#
# resource "aws_iam_role_policy_attachment" "ecs_execution" {
#   count      = var.use_ecs ? 1 : 0
#   role       = aws_iam_role.ecs_execution[0].name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
# }

# TODO: Create task role (permissions for your application)
#
# resource "aws_iam_role" "ecs_task" {
#   count = var.use_ecs ? 1 : 0
#   name  = "${var.project_name}-ecs-task"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = {
#     Name = "${var.project_name}-ecs-task-role"
#   }
# }

# =============================================================================
# STEP 3: Create CloudWatch Log Groups
# =============================================================================
# TODO: Create log groups for container logs
#
# resource "aws_cloudwatch_log_group" "web" {
#   count             = var.use_ecs ? 1 : 0
#   name              = "/ecs/${var.project_name}-web"
#   retention_in_days = 7
#
#   tags = {
#     Name = "${var.project_name}-web-logs"
#     Tier = "web"
#   }
# }
#
# resource "aws_cloudwatch_log_group" "app" {
#   count             = var.use_ecs ? 1 : 0
#   name              = "/ecs/${var.project_name}-app"
#   retention_in_days = 7
#
#   tags = {
#     Name = "${var.project_name}-app-logs"
#     Tier = "app"
#   }
# }

# =============================================================================
# STEP 4: Create Task Definitions
# =============================================================================
# TODO: Define the web tier container task
#
# resource "aws_ecs_task_definition" "web" {
#   count                    = var.use_ecs ? 1 : 0
#   family                   = "${var.project_name}-web"
#   requires_compatibilities = ["FARGATE"]
#   network_mode             = "awsvpc"
#   cpu                      = 256
#   memory                   = 512
#   execution_role_arn       = aws_iam_role.ecs_execution[0].arn
#   task_role_arn            = aws_iam_role.ecs_task[0].arn
#
#   container_definitions = jsonencode([
#     {
#       name      = "web"
#       image     = var.web_container_image
#       essential = true
#       portMappings = [
#         {
#           containerPort = 80
#           hostPort      = 80
#           protocol      = "tcp"
#         }
#       ]
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           "awslogs-group"         = aws_cloudwatch_log_group.web[0].name
#           "awslogs-region"        = var.aws_region
#           "awslogs-stream-prefix" = "web"
#         }
#       }
#     }
#   ])
#
#   tags = {
#     Name = "${var.project_name}-web-task"
#     Tier = "web"
#   }
# }

# TODO: Define the app tier container task
#
# resource "aws_ecs_task_definition" "app" {
#   count                    = var.use_ecs ? 1 : 0
#   family                   = "${var.project_name}-app"
#   requires_compatibilities = ["FARGATE"]
#   network_mode             = "awsvpc"
#   cpu                      = 256
#   memory                   = 512
#   execution_role_arn       = aws_iam_role.ecs_execution[0].arn
#   task_role_arn            = aws_iam_role.ecs_task[0].arn
#
#   container_definitions = jsonencode([
#     {
#       name      = "app"
#       image     = var.app_container_image
#       essential = true
#       portMappings = [
#         {
#           containerPort = 8080
#           hostPort      = 8080
#           protocol      = "tcp"
#         }
#       ]
#       environment = [
#         {
#           name  = "DB_HOST"
#           value = aws_db_instance.main.endpoint
#         },
#         {
#           name  = "DB_NAME"
#           value = var.db_name
#         }
#       ]
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           "awslogs-group"         = aws_cloudwatch_log_group.app[0].name
#           "awslogs-region"        = var.aws_region
#           "awslogs-stream-prefix" = "app"
#         }
#       }
#     }
#   ])
#
#   tags = {
#     Name = "${var.project_name}-app-task"
#     Tier = "app"
#   }
# }

# =============================================================================
# STEP 5: Create ECS Services
# =============================================================================
# TODO: Create the web tier service
#
# resource "aws_ecs_service" "web" {
#   count           = var.use_ecs ? 1 : 0
#   name            = "${var.project_name}-web-service"
#   cluster         = aws_ecs_cluster.main[0].id
#   task_definition = aws_ecs_task_definition.web[0].arn
#   desired_count   = var.web_instance_count
#   launch_type     = "FARGATE"
#
#   network_configuration {
#     subnets          = aws_subnet.private_app[*].id
#     security_groups  = [aws_security_group.web.id]
#     assign_public_ip = false
#   }
#
#   load_balancer {
#     target_group_arn = aws_lb_target_group.web_ecs[0].arn
#     container_name   = "web"
#     container_port   = 80
#   }
#
#   depends_on = [aws_lb_listener.http]
#
#   tags = {
#     Name = "${var.project_name}-web-service"
#     Tier = "web"
#   }
# }

# TODO: Create the app tier service
#
# resource "aws_ecs_service" "app" {
#   count           = var.use_ecs ? 1 : 0
#   name            = "${var.project_name}-app-service"
#   cluster         = aws_ecs_cluster.main[0].id
#   task_definition = aws_ecs_task_definition.app[0].arn
#   desired_count   = var.app_instance_count
#   launch_type     = "FARGATE"
#
#   network_configuration {
#     subnets          = aws_subnet.private_app[*].id
#     security_groups  = [aws_security_group.app.id]
#     assign_public_ip = false
#   }
#
#   tags = {
#     Name = "${var.project_name}-app-service"
#     Tier = "app"
#   }
# }
