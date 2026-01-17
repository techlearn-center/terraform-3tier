# Application Load Balancer for 3-Tier Architecture
# ==================================================

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-alb"
    Tier = "public"
  }
}

# Target Group for Web Tier (EC2)
resource "aws_lb_target_group" "web" {
  count       = var.use_ecs ? 0 : 1
  name        = "${var.project_name}-web-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-web-tg"
  }
}

# Target Group for Web Tier (ECS/Fargate)
resource "aws_lb_target_group" "web_ecs" {
  count       = var.use_ecs ? 1 : 0
  name        = "${var.project_name}-web-ecs-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # Required for Fargate

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-web-ecs-tg"
  }
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = var.use_ecs ? aws_lb_target_group.web_ecs[0].arn : aws_lb_target_group.web[0].arn
  }
}

# Attach EC2 instances to target group (only when not using ECS)
resource "aws_lb_target_group_attachment" "web" {
  count            = var.use_ecs ? 0 : var.web_instance_count
  target_group_arn = aws_lb_target_group.web[0].arn
  target_id        = aws_instance.web[count.index].id
  port             = 80
}
