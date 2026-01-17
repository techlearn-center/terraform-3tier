# RDS Database for 3-Tier Architecture - STARTER FILE
# =====================================================
# TODO: Create a managed database for the application!
#
# The Database tier stores application data:
#   App Tier -> RDS MySQL Database
#
# Key Concepts:
# - RDS is placed in PRIVATE subnets (no internet access)
# - DB Subnet Group defines which subnets RDS can use
# - Only App tier can connect (via security group)
# - Multi-AZ provides high availability
#
# Requirements:
# - Create a DB subnet group with private DB subnets
# - Create an RDS MySQL instance
# - Configure encryption and backups
# - Place in private subnets with DB security group
#
# See README.md for detailed guidance!

# =============================================================================
# STEP 1: Create DB Subnet Group
# =============================================================================
# TODO: Create a subnet group for RDS
# - Include both private DB subnets for multi-AZ
#
# resource "aws_db_subnet_group" "main" {
#   name        = "${var.project_name}-db-subnet-group"
#   description = "Database subnet group for ${var.project_name}"
#   subnet_ids  = aws_subnet.private_db[*].id
#
#   tags = {
#     Name = "${var.project_name}-db-subnet-group"
#   }
# }

# =============================================================================
# STEP 2: Create RDS MySQL Instance
# =============================================================================
# TODO: Create the RDS database instance
# - Use MySQL 8.0 engine
# - Enable encryption
# - Configure backups
# - Place in private subnets
#
# resource "aws_db_instance" "main" {
#   identifier     = "${var.project_name}-db"
#   engine         = "mysql"
#   engine_version = "8.0"
#   instance_class = var.db_instance_class
#
#   allocated_storage     = 20
#   max_allocated_storage = 100
#   storage_type          = "gp2"
#   storage_encrypted     = true
#
#   db_name  = var.db_name
#   username = var.db_username
#   password = var.db_password
#
#   db_subnet_group_name   = aws_db_subnet_group.main.name
#   vpc_security_group_ids = [aws_security_group.db.id]
#
#   multi_az            = var.db_multi_az
#   publicly_accessible = false
#
#   # Backup configuration
#   backup_retention_period = 7
#   backup_window           = "03:00-04:00"
#   maintenance_window      = "Mon:04:00-Mon:05:00"
#
#   # For development/testing - disable in production
#   skip_final_snapshot = true
#   deletion_protection = false
#
#   # Enable Performance Insights (free tier available)
#   performance_insights_enabled = false
#
#   tags = {
#     Name = "${var.project_name}-db"
#     Tier = "database"
#   }
# }
