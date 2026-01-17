# ECS/Fargate for 3-Tier Architecture (Containerized Path)
# =========================================================
# Set use_ecs = true in variables to use this instead of EC2

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  count = var.use_ecs ? 1 : 0
  name  = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ECS Execution Role (allows ECS to pull images, write logs)
resource "aws_iam_role" "ecs_execution" {
  count = var.use_ecs ? 1 : 0
  name  = "${var.project_name}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ecs-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  count      = var.use_ecs ? 1 : 0
  role       = aws_iam_role.ecs_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (permissions for your application)
resource "aws_iam_role" "ecs_task" {
  count = var.use_ecs ? 1 : 0
  name  = "${var.project_name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ecs-task-role"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "web" {
  count             = var.use_ecs ? 1 : 0
  name              = "/ecs/${var.project_name}-web"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-web-logs"
    Tier = "web"
  }
}

resource "aws_cloudwatch_log_group" "app" {
  count             = var.use_ecs ? 1 : 0
  name              = "/ecs/${var.project_name}-app"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-app-logs"
    Tier = "app"
  }
}

# Web Tier Task Definition
resource "aws_ecs_task_definition" "web" {
  count                    = var.use_ecs ? 1 : 0
  family                   = "${var.project_name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution[0].arn
  task_role_arn            = aws_iam_role.ecs_task[0].arn

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = var.web_container_image
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.web[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "web"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-web-task"
    Tier = "web"
  }
}

# App Tier Task Definition
resource "aws_ecs_task_definition" "app" {
  count                    = var.use_ecs ? 1 : 0
  family                   = "${var.project_name}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution[0].arn
  task_role_arn            = aws_iam_role.ecs_task[0].arn

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = var.app_container_image
      essential = true
      command   = ["node", "-e", "require('http').createServer((req,res)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify({status:'healthy',tier:'app',message:'Hello from ECS App Tier!'}))}).listen(8080)"]
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.main.endpoint
        },
        {
          name  = "DB_NAME"
          value = var.db_name
        },
        {
          name  = "DB_USER"
          value = var.db_username
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "wget -q -O /dev/null http://localhost:8080/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-app-task"
    Tier = "app"
  }
}

# Web Tier ECS Service
resource "aws_ecs_service" "web" {
  count           = var.use_ecs ? 1 : 0
  name            = "${var.project_name}-web-service"
  cluster         = aws_ecs_cluster.main[0].id
  task_definition = aws_ecs_task_definition.web[0].arn
  desired_count   = var.web_instance_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.web.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web_ecs[0].arn
    container_name   = "web"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Name = "${var.project_name}-web-service"
    Tier = "web"
  }
}

# App Tier ECS Service
resource "aws_ecs_service" "app" {
  count           = var.use_ecs ? 1 : 0
  name            = "${var.project_name}-app-service"
  cluster         = aws_ecs_cluster.main[0].id
  task_definition = aws_ecs_task_definition.app[0].arn
  desired_count   = var.app_instance_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  tags = {
    Name = "${var.project_name}-app-service"
    Tier = "app"
  }
}
