# Terraform 3-Tier Architecture - STARTER FILE
# =============================================
# TODO: Configure the Terraform and AWS provider!
#
# This file sets up:
# - Terraform version requirements
# - AWS provider configuration
# - Default tags for all resources
#
# Requirements:
# - Use Terraform version >= 1.0.0
# - Configure AWS provider with hashicorp/aws ~> 5.0
# - Set region using var.aws_region
# - Add default tags (Project, Environment, ManagedBy)
#
# See README.md for detailed guidance!

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    # TODO: Uncomment and configure the AWS provider
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }
  }
}

# TODO: Configure the AWS provider
# provider "aws" {
#   region = var.aws_region
#
#   default_tags {
#     tags = {
#       Project     = var.project_name
#       Environment = var.environment
#       ManagedBy   = "terraform"
#     }
#   }
# }
