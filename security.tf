# Security Groups for 3-Tier Architecture - STARTER FILE
# ========================================================
# TODO: Create security groups that control traffic flow!
#
# Security groups are configured in a chain:
#   Internet -> ALB -> Web Tier -> App Tier -> Database
#
# Key Concepts:
# - Each tier only accepts traffic from the tier above it
# - This creates "defense in depth" - multiple layers of security
# - Database is only accessible from App tier (never from internet!)
#
# Requirements:
# - ALB: Accept HTTP/HTTPS from internet
# - Web: Accept HTTP only from ALB
# - App: Accept port 8080 only from Web tier
# - DB: Accept MySQL (3306) only from App tier
#
# See README.md for detailed guidance!

# =============================================================================
# STEP 1: ALB Security Group (Public facing)
# =============================================================================
# TODO: Create security group for Application Load Balancer
# - Allow HTTP (80) from anywhere
# - Allow HTTPS (443) from anywhere
# - Allow all outbound traffic
#
# resource "aws_security_group" "alb" {
#   name        = "${var.project_name}-alb-sg"
#   description = "Security group for Application Load Balancer"
#   vpc_id      = aws_vpc.main.id
#
#   # HTTP from Internet
#   ingress {
#     description = "HTTP from Internet"
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   # HTTPS from Internet
#   ingress {
#     description = "HTTPS from Internet"
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   # All outbound
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-alb-sg"
#     Tier = "public"
#   }
# }

# =============================================================================
# STEP 2: Web Tier Security Group
# =============================================================================
# TODO: Create security group for Web tier
# - Allow HTTP only from ALB (use security_groups reference!)
# - Allow SSH from VPC for management
# - Allow all outbound
#
# resource "aws_security_group" "web" {
#   name        = "${var.project_name}-web-sg"
#   description = "Security group for Web tier"
#   vpc_id      = aws_vpc.main.id
#
#   # HTTP only from ALB (notice: security_groups, not cidr_blocks!)
#   ingress {
#     description     = "HTTP from ALB"
#     from_port       = 80
#     to_port         = 80
#     protocol        = "tcp"
#     security_groups = [aws_security_group.alb.id]
#   }
#
#   # SSH for management (from within VPC only)
#   ingress {
#     description = "SSH from VPC"
#     from_port   = 22
#     to_port     = 22
#     protocol    = "tcp"
#     cidr_blocks = var.allowed_ssh_cidr
#   }
#
#   # All outbound
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-web-sg"
#     Tier = "web"
#   }
# }

# =============================================================================
# STEP 3: App Tier Security Group
# =============================================================================
# TODO: Create security group for App tier
# - Allow port 8080 only from Web tier
# - Allow SSH from VPC for management
# - Allow all outbound
#
# resource "aws_security_group" "app" {
#   name        = "${var.project_name}-app-sg"
#   description = "Security group for App tier"
#   vpc_id      = aws_vpc.main.id
#
#   # App port only from Web tier
#   ingress {
#     description     = "App port from Web tier"
#     from_port       = 8080
#     to_port         = 8080
#     protocol        = "tcp"
#     security_groups = [aws_security_group.web.id]
#   }
#
#   # SSH for management (from within VPC only)
#   ingress {
#     description = "SSH from VPC"
#     from_port   = 22
#     to_port     = 22
#     protocol    = "tcp"
#     cidr_blocks = var.allowed_ssh_cidr
#   }
#
#   # All outbound
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-app-sg"
#     Tier = "app"
#   }
# }

# =============================================================================
# STEP 4: Database Tier Security Group
# =============================================================================
# TODO: Create security group for Database tier
# - Allow MySQL (3306) only from App tier
# - Allow PostgreSQL (5432) only from App tier (optional)
# - Allow all outbound
#
# resource "aws_security_group" "db" {
#   name        = "${var.project_name}-db-sg"
#   description = "Security group for Database tier"
#   vpc_id      = aws_vpc.main.id
#
#   # MySQL only from App tier
#   ingress {
#     description     = "MySQL from App tier"
#     from_port       = 3306
#     to_port         = 3306
#     protocol        = "tcp"
#     security_groups = [aws_security_group.app.id]
#   }
#
#   # PostgreSQL only from App tier (alternative)
#   ingress {
#     description     = "PostgreSQL from App tier"
#     from_port       = 5432
#     to_port         = 5432
#     protocol        = "tcp"
#     security_groups = [aws_security_group.app.id]
#   }
#
#   # All outbound
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-db-sg"
#     Tier = "database"
#   }
# }
