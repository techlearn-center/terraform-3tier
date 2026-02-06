#!/usr/bin/env python3
"""
Terraform 3-Tier Architecture Challenge - Progress Checker
==========================================================
Validates your Terraform configuration and tracks your progress.

Usage:
    python run.py           # Check progress
    python run.py --verbose # Show detailed output
    python run.py --verify  # Verify deployed resources in LocalStack
"""

import os
import re
import sys
import glob
import json
import subprocess
import argparse

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header():
    """Print the challenge header."""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Terraform 3-Tier Architecture Challenge{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def read_file(filename):
    """Read a file and return its contents."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def check_file_exists(filename):
    """Check if a file exists."""
    return os.path.isfile(filename)


def strip_comments(content):
    """Remove commented lines from Terraform content.

    This strips:
    - Lines starting with # (after optional whitespace)
    - Lines starting with // (after optional whitespace)
    - Block comments /* ... */ (including multi-line)
    """
    if content is None:
        return None

    # Remove block comments /* ... */
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Remove single-line comments (lines starting with # or //)
    lines = content.split('\n')
    uncommented_lines = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped.startswith('#') and not stripped.startswith('//'):
            uncommented_lines.append(line)

    return '\n'.join(uncommented_lines)


def check_pattern(content, pattern, flags=0):
    """Check if a pattern exists in UNCOMMENTED content only.

    This ensures that commented-out code (starter templates) doesn't
    give students points until they actually uncomment and complete it.
    """
    if content is None:
        return False
    # Strip comments before checking pattern
    uncommented = strip_comments(content)
    return bool(re.search(pattern, uncommented, flags))


def check_provider_config():
    """Check main.tf for provider configuration."""
    content = read_file('main.tf')
    if content is None:
        return 0, ["main.tf not found"]

    checks = []
    points = 0
    max_points = 5

    # Check terraform block
    if check_pattern(content, r'terraform\s*\{'):
        checks.append(("terraform block", True))
        points += 1
    else:
        checks.append(("terraform block", False))

    # Check required_providers
    if check_pattern(content, r'required_providers\s*\{'):
        checks.append(("required_providers", True))
        points += 1
    else:
        checks.append(("required_providers", False))

    # Check AWS provider
    if check_pattern(content, r'provider\s+"aws"'):
        checks.append(("AWS provider", True))
        points += 2
    else:
        checks.append(("AWS provider", False))

    # Check default_tags
    if check_pattern(content, r'default_tags\s*\{'):
        checks.append(("default_tags", True))
        points += 1
    else:
        checks.append(("default_tags (optional)", False))

    return points, checks


def check_vpc_config():
    """Check vpc.tf for VPC and networking configuration."""
    content = read_file('vpc.tf')
    if content is None:
        return 0, ["vpc.tf not found"]

    checks = []
    points = 0
    max_points = 20

    # Check VPC
    if check_pattern(content, r'resource\s+"aws_vpc"'):
        checks.append(("aws_vpc resource", True))
        points += 3
    else:
        checks.append(("aws_vpc resource", False))

    # Check Internet Gateway
    if check_pattern(content, r'resource\s+"aws_internet_gateway"'):
        checks.append(("aws_internet_gateway", True))
        points += 2
    else:
        checks.append(("aws_internet_gateway", False))

    # Check public subnets (should have count or multiple)
    if check_pattern(content, r'resource\s+"aws_subnet"\s+"public"'):
        checks.append(("public subnets", True))
        points += 3
    else:
        checks.append(("public subnets", False))

    # Check private app subnets
    if check_pattern(content, r'resource\s+"aws_subnet"\s+"private_app"'):
        checks.append(("private app subnets", True))
        points += 3
    else:
        checks.append(("private app subnets", False))

    # Check private db subnets
    if check_pattern(content, r'resource\s+"aws_subnet"\s+"private_db"'):
        checks.append(("private database subnets", True))
        points += 3
    else:
        checks.append(("private database subnets", False))

    # Check NAT Gateway
    if check_pattern(content, r'resource\s+"aws_nat_gateway"'):
        checks.append(("aws_nat_gateway", True))
        points += 3
    else:
        checks.append(("aws_nat_gateway", False))

    # Check route tables
    if check_pattern(content, r'resource\s+"aws_route_table"'):
        checks.append(("route tables", True))
        points += 2
    else:
        checks.append(("route tables", False))

    # Check route table associations
    if check_pattern(content, r'resource\s+"aws_route_table_association"'):
        checks.append(("route table associations", True))
        points += 1
    else:
        checks.append(("route table associations", False))

    return points, checks


def check_security_config():
    """Check security.tf for security groups."""
    content = read_file('security.tf')
    if content is None:
        return 0, ["security.tf not found"]

    checks = []
    points = 0
    max_points = 10

    # Check ALB security group
    if check_pattern(content, r'resource\s+"aws_security_group"\s+"alb"'):
        checks.append(("ALB security group", True))
        points += 3
    else:
        checks.append(("ALB security group", False))

    # Check web tier security group
    if check_pattern(content, r'resource\s+"aws_security_group"\s+"web"'):
        checks.append(("Web tier security group", True))
        points += 2
    else:
        checks.append(("Web tier security group", False))

    # Check app tier security group
    if check_pattern(content, r'resource\s+"aws_security_group"\s+"app"'):
        checks.append(("App tier security group", True))
        points += 2
    else:
        checks.append(("App tier security group", False))

    # Check database security group
    if check_pattern(content, r'resource\s+"aws_security_group"\s+"db"'):
        checks.append(("Database security group", True))
        points += 3
    else:
        checks.append(("Database security group", False))

    return points, checks


def check_alb_config():
    """Check alb.tf for load balancer configuration."""
    content = read_file('alb.tf')
    if content is None:
        return 0, ["alb.tf not found"]

    checks = []
    points = 0
    max_points = 20

    # Check ALB resource
    if check_pattern(content, r'resource\s+"aws_lb"\s+"main"'):
        checks.append(("aws_lb resource", True))
        points += 6
    else:
        checks.append(("aws_lb resource", False))

    # Check target group
    if check_pattern(content, r'resource\s+"aws_lb_target_group"'):
        checks.append(("target group", True))
        points += 5
    else:
        checks.append(("target group", False))

    # Check health check
    if check_pattern(content, r'health_check\s*\{'):
        checks.append(("health check configuration", True))
        points += 4
    else:
        checks.append(("health check configuration", False))

    # Check listener
    if check_pattern(content, r'resource\s+"aws_lb_listener"'):
        checks.append(("ALB listener", True))
        points += 5
    else:
        checks.append(("ALB listener", False))

    return points, checks


def check_ec2_config():
    """Check ec2.tf for EC2 instances."""
    content = read_file('ec2.tf')
    if content is None:
        return 0, ["ec2.tf not found"]

    checks = []
    points = 0
    max_points = 25

    # Check AMI data source
    if check_pattern(content, r'data\s+"aws_ami"'):
        checks.append(("AMI data source", True))
        points += 3
    else:
        checks.append(("AMI data source", False))

    # Check web tier instances
    if check_pattern(content, r'resource\s+"aws_instance"\s+"web"'):
        checks.append(("web tier instances", True))
        points += 8
    else:
        checks.append(("web tier instances", False))

    # Check app tier instances
    if check_pattern(content, r'resource\s+"aws_instance"\s+"app"'):
        checks.append(("app tier instances", True))
        points += 8
    else:
        checks.append(("app tier instances", False))

    # Check user_data
    if check_pattern(content, r'user_data\s*='):
        checks.append(("user_data scripts", True))
        points += 4
    else:
        checks.append(("user_data scripts", False))

    # Check security group attachment
    if check_pattern(content, r'vpc_security_group_ids'):
        checks.append(("security group attachment", True))
        points += 2
    else:
        checks.append(("security group attachment", False))

    return points, checks


def check_rds_config():
    """Check rds.tf for RDS configuration."""
    content = read_file('rds.tf')
    if content is None:
        return 0, ["rds.tf not found"]

    checks = []
    points = 0
    max_points = 15

    # Check DB subnet group
    if check_pattern(content, r'resource\s+"aws_db_subnet_group"'):
        checks.append(("DB subnet group", True))
        points += 4
    else:
        checks.append(("DB subnet group", False))

    # Check RDS instance
    if check_pattern(content, r'resource\s+"aws_db_instance"'):
        checks.append(("RDS instance", True))
        points += 6
    else:
        checks.append(("RDS instance", False))

    # Check engine configuration
    if check_pattern(content, r'engine\s*=\s*"(mysql|postgres)"'):
        checks.append(("database engine", True))
        points += 2
    else:
        checks.append(("database engine", False))

    # Check security group attachment
    if check_pattern(content, r'vpc_security_group_ids'):
        checks.append(("security group attachment", True))
        points += 3
    else:
        checks.append(("security group attachment", False))

    return points, checks


def check_variables_config():
    """Check variables.tf for input variables."""
    content = read_file('variables.tf')
    if content is None:
        return 0, ["variables.tf not found"]

    checks = []
    points = 0
    max_points = 5

    # Count variables
    var_count = len(re.findall(r'variable\s+"[^"]+"', content))

    if var_count >= 10:
        checks.append((f"variables defined ({var_count})", True))
        points += 3
    elif var_count >= 5:
        checks.append((f"variables defined ({var_count})", True))
        points += 2
    else:
        checks.append((f"variables defined ({var_count}, need more)", False))

    # Check for descriptions
    desc_count = len(re.findall(r'description\s*=', content))
    if desc_count >= var_count * 0.8:
        checks.append(("variable descriptions", True))
        points += 2
    else:
        checks.append(("variable descriptions (incomplete)", False))
        points += 1

    return points, checks


def check_ecs_config():
    """Check ecs.tf for ECS configuration (bonus)."""
    content = read_file('ecs.tf')
    if content is None:
        return 0, ["ecs.tf not found (optional for ECS path)"]

    checks = []
    points = 0

    # Check ECS cluster
    if check_pattern(content, r'resource\s+"aws_ecs_cluster"'):
        checks.append(("ECS cluster", True))
        points += 5

    # Check task definitions
    if check_pattern(content, r'resource\s+"aws_ecs_task_definition"'):
        checks.append(("ECS task definitions", True))
        points += 5

    # Check ECS services
    if check_pattern(content, r'resource\s+"aws_ecs_service"'):
        checks.append(("ECS services", True))
        points += 5

    return points, checks


def aws_cli_query(service_cmd, query=None):
    """Run an AWS CLI command against LocalStack and return parsed JSON output."""
    endpoint = "http://localhost:4566"
    cmd = [
        'aws', '--endpoint-url', endpoint,
        '--region', 'us-east-1',
        '--no-cli-pager',
        '--output', 'json',
    ] + service_cmd
    if query:
        cmd += ['--query', query]

    try:
        env = os.environ.copy()
        env.setdefault('AWS_ACCESS_KEY_ID', 'test')
        env.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
        env.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return None
    except Exception:
        return None


def verify_localstack_resources():
    """Verify deployed resources in LocalStack using AWS CLI."""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  LocalStack Infrastructure Verification{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    # Check if LocalStack is reachable
    try:
        import urllib.request
        resp = urllib.request.urlopen('http://localhost:4566/_localstack/health', timeout=5)
        health = json.loads(resp.read().decode())
        print(f"  {Colors.GREEN}[OK]{Colors.END} LocalStack is running")
    except Exception:
        print(f"  {Colors.RED}[X]{Colors.END} LocalStack is not reachable at localhost:4566")
        print(f"      Run: docker-compose up -d")
        return

    # Check AWS CLI availability
    try:
        subprocess.run(['aws', '--version'], capture_output=True, timeout=5)
    except FileNotFoundError:
        print(f"  {Colors.RED}[X]{Colors.END} AWS CLI not installed (needed for --verify)")
        print(f"      Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return

    all_ok = True

    # 1. Check VPCs
    vpcs = aws_cli_query(['ec2', 'describe-vpcs'], 'Vpcs[*].{Id:VpcId,Cidr:CidrBlock}')
    if vpcs and len(vpcs) > 0:
        print(f"  {Colors.GREEN}[OK]{Colors.END} VPC created ({len(vpcs)} found)")
        for v in vpcs:
            print(f"      - {v.get('Id', 'N/A')} ({v.get('Cidr', 'N/A')})")
    else:
        print(f"  {Colors.RED}[X]{Colors.END} No VPCs found")
        all_ok = False

    # 2. Check Subnets
    subnets = aws_cli_query(['ec2', 'describe-subnets'], 'Subnets[*].{Id:SubnetId,Cidr:CidrBlock,AZ:AvailabilityZone}')
    if subnets and len(subnets) >= 6:
        print(f"  {Colors.GREEN}[OK]{Colors.END} Subnets created ({len(subnets)} found, expected 6)")
    elif subnets and len(subnets) > 0:
        print(f"  {Colors.YELLOW}[!]{Colors.END} Subnets created ({len(subnets)} found, expected 6)")
        all_ok = False
    else:
        print(f"  {Colors.RED}[X]{Colors.END} No subnets found")
        all_ok = False

    # 3. Check Security Groups (excluding default)
    sgs = aws_cli_query(['ec2', 'describe-security-groups'],
                        'SecurityGroups[?GroupName!=`default`].{Id:GroupId,Name:GroupName}')
    if sgs and len(sgs) >= 4:
        print(f"  {Colors.GREEN}[OK]{Colors.END} Security groups created ({len(sgs)} found)")
        for sg in sgs:
            print(f"      - {sg.get('Name', 'N/A')} ({sg.get('Id', 'N/A')})")
    elif sgs and len(sgs) > 0:
        print(f"  {Colors.YELLOW}[!]{Colors.END} Security groups ({len(sgs)} found, expected 4: alb, web, app, db)")
        all_ok = False
    else:
        print(f"  {Colors.RED}[X]{Colors.END} No security groups found")
        all_ok = False

    # 4. Check ALB (Pro-only service — gracefully handle 501)
    albs = aws_cli_query(['elbv2', 'describe-load-balancers'],
                         'LoadBalancers[*].{Name:LoadBalancerName,DNS:DNSName,State:State.Code}')
    if albs and len(albs) > 0:
        alb = albs[0]
        print(f"  {Colors.GREEN}[OK]{Colors.END} ALB created: {alb.get('Name', 'N/A')}")
        print(f"      DNS: {alb.get('DNS', 'N/A')}")
        print(f"      State: {alb.get('State', 'N/A')}")
    else:
        print(f"  {Colors.YELLOW}[SKIP]{Colors.END} ALB — elbv2 is a LocalStack Pro feature (not available in Community)")
        print(f"      Validate with: python run.py (checks alb.tf code)")

    # 5. Check Target Groups (Pro-only service)
    tgs = aws_cli_query(['elbv2', 'describe-target-groups'],
                        'TargetGroups[*].{Name:TargetGroupName,Port:Port,Protocol:Protocol}')
    if tgs and len(tgs) > 0:
        tg = tgs[0]
        print(f"  {Colors.GREEN}[OK]{Colors.END} Target group created: {tg.get('Name', 'N/A')} (port {tg.get('Port', 'N/A')})")
    else:
        print(f"  {Colors.YELLOW}[SKIP]{Colors.END} Target groups — elbv2 is a LocalStack Pro feature")

    # 6. Check EC2 instances
    instances = aws_cli_query(['ec2', 'describe-instances',
                               '--filters', 'Name=instance-state-name,Values=running'],
                              'Reservations[*].Instances[*].{Id:InstanceId,Type:InstanceType,IP:PrivateIpAddress}')
    # Flatten the nested list
    flat_instances = []
    if instances:
        for reservation in instances:
            if isinstance(reservation, list):
                flat_instances.extend(reservation)
            elif isinstance(reservation, dict):
                flat_instances.append(reservation)

    if flat_instances and len(flat_instances) >= 2:
        print(f"  {Colors.GREEN}[OK]{Colors.END} EC2 instances running ({len(flat_instances)} found)")
        for inst in flat_instances:
            print(f"      - {inst.get('Id', 'N/A')} ({inst.get('Type', 'N/A')}, IP: {inst.get('IP', 'N/A')})")
    elif flat_instances:
        print(f"  {Colors.YELLOW}[!]{Colors.END} EC2 instances ({len(flat_instances)} found, expected 4: 2 web + 2 app)")
        all_ok = False
    else:
        print(f"  {Colors.RED}[X]{Colors.END} No running EC2 instances found")
        all_ok = False

    # 7. Check RDS (Pro-only service — gracefully handle 501)
    dbs = aws_cli_query(['rds', 'describe-db-instances'],
                        'DBInstances[*].{Id:DBInstanceIdentifier,Engine:Engine,Status:DBInstanceStatus}')
    if dbs and len(dbs) > 0:
        db = dbs[0]
        print(f"  {Colors.GREEN}[OK]{Colors.END} RDS instance created: {db.get('Id', 'N/A')} ({db.get('Engine', 'N/A')})")
    else:
        print(f"  {Colors.YELLOW}[SKIP]{Colors.END} RDS — rds is a LocalStack Pro feature (not available in Community)")
        print(f"      Validate with: python run.py (checks rds.tf code)")

    # Summary
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    if all_ok:
        print(f"  {Colors.GREEN}{Colors.BOLD}Community-supported resources verified!{Colors.END}")
        print(f"  (ALB and RDS require LocalStack Pro — validated via code checks)")
        print(f"\n  {Colors.CYAN}Web Preview:{Colors.END} http://localhost:3000")
        print(f"\n  {Colors.CYAN}Full code check:{Colors.END} python run.py --verbose")
    else:
        print(f"  {Colors.YELLOW}Some resources are missing. Run 'terraform apply' first.{Colors.END}")
        print(f"  Note: ALB/RDS errors (501) are expected on LocalStack Community.")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def run_terraform_validate():
    """Run terraform validate to check syntax."""
    try:
        result = subprocess.run(
            ['terraform', 'validate', '-json'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, "Terraform configuration is valid"
        else:
            try:
                output = json.loads(result.stdout)
                errors = [d.get('summary', 'Unknown error') for d in output.get('diagnostics', [])]
                return False, "; ".join(errors) if errors else "Validation failed"
            except:
                return False, result.stderr or "Validation failed"
    except FileNotFoundError:
        return None, "Terraform not installed"
    except Exception as e:
        return None, str(e)


def print_section(title, points, max_points, checks, verbose=False):
    """Print a section result."""
    if points == max_points:
        status = f"{Colors.GREEN}[PASS]{Colors.END}"
    elif points > 0:
        status = f"{Colors.YELLOW}[PARTIAL]{Colors.END}"
    else:
        status = f"{Colors.RED}[FAIL]{Colors.END}"

    print(f"  {status} {title} ({points}/{max_points} points)")

    if verbose:
        for check_name, passed in checks:
            if passed:
                print(f"      {Colors.GREEN}[OK]{Colors.END} {check_name}")
            else:
                print(f"      {Colors.RED}[X]{Colors.END} {check_name}")


def main():
    parser = argparse.ArgumentParser(description='Check your Terraform 3-Tier challenge progress')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--verify', action='store_true',
                        help='Verify deployed resources in LocalStack via AWS CLI')
    args = parser.parse_args()

    print_header()

    # If --verify flag, run infrastructure verification and exit
    if args.verify:
        verify_localstack_resources()
        return 0

    # Determine which path the user is taking
    ec2_content = read_file('ec2.tf')
    ecs_content = read_file('ecs.tf')

    use_ecs = False
    if ecs_content and check_pattern(ecs_content, r'resource\s+"aws_ecs_cluster"'):
        # Check if use_ecs is set to true
        vars_content = read_file('variables.tf')
        if vars_content and check_pattern(vars_content, r'default\s*=\s*true', re.IGNORECASE):
            use_ecs = True

    path_name = "ECS (Containerized)" if use_ecs else "EC2 (Traditional)"
    print(f"  {Colors.CYAN}Path:{Colors.END} {path_name}\n")

    total_points = 0
    max_total = 100

    # Check each section
    sections = [
        ("Provider Config", check_provider_config, 5),
        ("VPC & Networking", check_vpc_config, 20),
        ("Security Groups", check_security_config, 10),
        ("Application Load Balancer", check_alb_config, 20),
        ("EC2 Instances" if not use_ecs else "ECS Configuration", check_ec2_config if not use_ecs else check_ecs_config, 25),
        ("RDS Database", check_rds_config, 15),
        ("Variables", check_variables_config, 5),
    ]

    for title, check_func, max_points in sections:
        points, checks = check_func()
        # Cap points at max_points
        points = min(points, max_points)
        total_points += points
        print_section(title, points, max_points, checks, args.verbose)

    # Run terraform validate
    print(f"\n  {Colors.CYAN}Syntax Validation:{Colors.END}")
    valid, message = run_terraform_validate()
    if valid is True:
        print(f"      {Colors.GREEN}[OK]{Colors.END} {message}")
    elif valid is False:
        print(f"      {Colors.RED}[X]{Colors.END} {message}")
    else:
        print(f"      {Colors.YELLOW}[?]{Colors.END} {message}")

    # Summary
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"  {Colors.BOLD}Total Score: {total_points}/{max_total}{Colors.END}")

    if total_points == max_total:
        print(f"  {Colors.GREEN}{Colors.BOLD}CHALLENGE COMPLETE!{Colors.END}")
    elif total_points >= 80:
        print(f"  {Colors.YELLOW}Almost there! Check the failing sections above.{Colors.END}")
    elif total_points >= 50:
        print(f"  {Colors.YELLOW}Good progress! Keep going.{Colors.END}")
    else:
        print(f"  {Colors.RED}Just getting started. Follow the README step by step.{Colors.END}")

    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    # Return exit code based on completion
    return 0 if total_points == max_total else 1


if __name__ == "__main__":
    sys.exit(main())
