# Application Load Balancer for 3-Tier Architecture - STARTER FILE
# ==================================================================
# TODO: Create an Application Load Balancer to distribute traffic!
#
# The ALB is the entry point for all web traffic:
#   Internet -> ALB -> Web Tier EC2 instances
#
# Key Concepts:
# - ALB sits in PUBLIC subnets (internet-facing)
# - Target Groups define where to send traffic
# - Health checks ensure only healthy instances receive traffic
# - Listeners define what ports/protocols to accept
#
# Requirements:
# - Create an internet-facing ALB in public subnets
# - Create a Target Group for web tier instances
# - Create an HTTP listener on port 80
# - Attach EC2 instances to the target group
#
# See README.md for detailed guidance!

# =============================================================================
# STEP 1: Create the Application Load Balancer
# =============================================================================
# TODO: Create an internet-facing ALB
# - Place in public subnets
# - Attach the ALB security group
#
# resource "aws_lb" "main" {
#   name               = "${var.project_name}-alb"
#   internal           = false
#   load_balancer_type = "application"
#   security_groups    = [aws_security_group.alb.id]
#   subnets            = aws_subnet.public[*].id
#
#   enable_deletion_protection = false
#
#   tags = {
#     Name = "${var.project_name}-alb"
#     Tier = "public"
#   }
# }

# =============================================================================
# STEP 2: Create Target Group for Web Tier
# =============================================================================
# TODO: Create a target group for EC2 instances
# - Configure health checks to monitor instance health
# - Set target type to "instance" for EC2
#
# resource "aws_lb_target_group" "web" {
#   count       = var.use_ecs ? 0 : 1
#   name        = "${var.project_name}-web-tg"
#   port        = 80
#   protocol    = "HTTP"
#   vpc_id      = aws_vpc.main.id
#   target_type = "instance"
#
#   health_check {
#     enabled             = true
#     healthy_threshold   = 2
#     unhealthy_threshold = 2
#     timeout             = 5
#     interval            = 30
#     path                = "/"
#     port                = "traffic-port"
#     protocol            = "HTTP"
#     matcher             = "200"
#   }
#
#   tags = {
#     Name = "${var.project_name}-web-tg"
#   }
# }

# Target Group for ECS/Fargate (optional, for advanced users)
# resource "aws_lb_target_group" "web_ecs" {
#   count       = var.use_ecs ? 1 : 0
#   name        = "${var.project_name}-web-ecs-tg"
#   port        = 80
#   protocol    = "HTTP"
#   vpc_id      = aws_vpc.main.id
#   target_type = "ip"  # Required for Fargate
#
#   health_check {
#     enabled             = true
#     healthy_threshold   = 2
#     unhealthy_threshold = 2
#     timeout             = 5
#     interval            = 30
#     path                = "/"
#     protocol            = "HTTP"
#     matcher             = "200"
#   }
#
#   tags = {
#     Name = "${var.project_name}-web-ecs-tg"
#   }
# }

# =============================================================================
# STEP 3: Create HTTP Listener
# =============================================================================
# TODO: Create a listener on port 80
# - Forward traffic to the web target group
#
# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = 80
#   protocol          = "HTTP"
#
#   default_action {
#     type             = "forward"
#     target_group_arn = var.use_ecs ? aws_lb_target_group.web_ecs[0].arn : aws_lb_target_group.web[0].arn
#   }
# }

# =============================================================================
# STEP 4: Attach EC2 Instances to Target Group
# =============================================================================
# TODO: Register web tier instances with the target group
# - Use count to attach all instances
#
# resource "aws_lb_target_group_attachment" "web" {
#   count            = var.use_ecs ? 0 : var.web_instance_count
#   target_group_arn = aws_lb_target_group.web[0].arn
#   target_id        = aws_instance.web[count.index].id
#   port             = 80
# }
