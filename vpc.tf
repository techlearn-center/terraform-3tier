# VPC and Networking for 3-Tier Architecture - STARTER FILE
# ==========================================================
# TODO: Build a production-ready VPC with 3 tiers!
#
# Requirements:
# - Create a VPC with CIDR 10.0.0.0/16
# - Create 2 public subnets (for ALB)
# - Create 2 private app subnets (for EC2/ECS)
# - Create 2 private database subnets (for RDS)
# - Create Internet Gateway for public access
# - Create NAT Gateway for private subnet internet access
# - Create proper route tables and associations
#
# Architecture:
#   Internet -> IGW -> Public Subnets (ALB)
#                          |
#                     NAT Gateway
#                          |
#                    Private App Subnets (EC2)
#                          |
#                    Private DB Subnets (RDS)
#
# See README.md for detailed guidance!

# Data source for Availability Zones (provided for you)
data "aws_availability_zones" "available" {
  state = "available"
}

# =============================================================================
# STEP 1: Create the VPC
# =============================================================================
# TODO: Create VPC with DNS support enabled
# resource "aws_vpc" "main" {
#   cidr_block           = var.vpc_cidr
#   enable_dns_hostnames = true
#   enable_dns_support   = true
#
#   tags = {
#     Name = "${var.project_name}-vpc"
#   }
# }

# =============================================================================
# STEP 2: Create Internet Gateway
# =============================================================================
# TODO: Create Internet Gateway attached to VPC
# resource "aws_internet_gateway" "main" {
#   vpc_id = aws_vpc.main.id
#
#   tags = {
#     Name = "${var.project_name}-igw"
#   }
# }

# =============================================================================
# STEP 3: Create Public Subnets (2 for high availability)
# =============================================================================
# TODO: Create 2 public subnets in different AZs
# Hint: Use count = 2 and cidrsubnet() function
# resource "aws_subnet" "public" {
#   count                   = 2
#   vpc_id                  = aws_vpc.main.id
#   cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
#   availability_zone       = data.aws_availability_zones.available.names[count.index]
#   map_public_ip_on_launch = true
#
#   tags = {
#     Name = "${var.project_name}-public-${count.index + 1}"
#     Tier = "public"
#   }
# }

# =============================================================================
# STEP 4: Create Private App Subnets (for Web/App servers)
# =============================================================================
# TODO: Create 2 private subnets for application tier
# resource "aws_subnet" "private_app" {
#   count             = 2
#   vpc_id            = aws_vpc.main.id
#   cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
#   availability_zone = data.aws_availability_zones.available.names[count.index]
#
#   tags = {
#     Name = "${var.project_name}-private-app-${count.index + 1}"
#     Tier = "app"
#   }
# }

# =============================================================================
# STEP 5: Create Private Database Subnets
# =============================================================================
# TODO: Create 2 private subnets for database tier
# resource "aws_subnet" "private_db" {
#   count             = 2
#   vpc_id            = aws_vpc.main.id
#   cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
#   availability_zone = data.aws_availability_zones.available.names[count.index]
#
#   tags = {
#     Name = "${var.project_name}-private-db-${count.index + 1}"
#     Tier = "database"
#   }
# }

# =============================================================================
# STEP 6: Create NAT Gateway (allows private subnets to reach internet)
# =============================================================================
# TODO: Create Elastic IP for NAT Gateway
# resource "aws_eip" "nat" {
#   domain = "vpc"
#
#   tags = {
#     Name = "${var.project_name}-nat-eip"
#   }
#
#   depends_on = [aws_internet_gateway.main]
# }

# TODO: Create NAT Gateway in public subnet
# resource "aws_nat_gateway" "main" {
#   allocation_id = aws_eip.nat.id
#   subnet_id     = aws_subnet.public[0].id
#
#   tags = {
#     Name = "${var.project_name}-nat"
#   }
#
#   depends_on = [aws_internet_gateway.main]
# }

# =============================================================================
# STEP 7: Create Route Tables
# =============================================================================
# TODO: Public route table (routes to Internet Gateway)
# resource "aws_route_table" "public" {
#   vpc_id = aws_vpc.main.id
#
#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.main.id
#   }
#
#   tags = {
#     Name = "${var.project_name}-public-rt"
#   }
# }

# TODO: Private route table (routes to NAT Gateway)
# resource "aws_route_table" "private" {
#   vpc_id = aws_vpc.main.id
#
#   route {
#     cidr_block     = "0.0.0.0/0"
#     nat_gateway_id = aws_nat_gateway.main.id
#   }
#
#   tags = {
#     Name = "${var.project_name}-private-rt"
#   }
# }

# =============================================================================
# STEP 8: Associate Route Tables with Subnets
# =============================================================================
# TODO: Associate public subnets with public route table
# resource "aws_route_table_association" "public" {
#   count          = 2
#   subnet_id      = aws_subnet.public[count.index].id
#   route_table_id = aws_route_table.public.id
# }

# TODO: Associate private app subnets with private route table
# resource "aws_route_table_association" "private_app" {
#   count          = 2
#   subnet_id      = aws_subnet.private_app[count.index].id
#   route_table_id = aws_route_table.private.id
# }

# TODO: Associate private db subnets with private route table
# resource "aws_route_table_association" "private_db" {
#   count          = 2
#   subnet_id      = aws_subnet.private_db[count.index].id
#   route_table_id = aws_route_table.private.id
# }
