#!/usr/bin/env python3
"""
Terraform 3-Tier Architecture Dashboard
========================================
A visual web dashboard to see your 3-tier AWS infrastructure in LocalStack or real AWS.

Usage:
    python dashboard.py              # Open dashboard (LocalStack)
    python dashboard.py --aws        # Use real AWS credentials
    python dashboard.py --no-browser # Just start server
"""

import json
import subprocess
import sys
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import argparse

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOCALSTACK_ENDPOINT = "http://localhost:4566"
USE_AWS = False

# Colors for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_aws_command(service, action, extra_args=None):
    """Run an AWS CLI command against LocalStack or real AWS."""
    cmd = ["aws"]
    if not USE_AWS:
        cmd.extend(["--endpoint-url", LOCALSTACK_ENDPOINT])
    cmd.extend([service, action, "--output", "json"])
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        return None
    except Exception as e:
        return None


def get_vpcs():
    """Get VPCs created by Terraform (filter out default VPC)."""
    data = run_aws_command("ec2", "describe-vpcs")
    if not data:
        return []

    vpcs = []
    for vpc in data.get("Vpcs", []):
        if vpc.get("IsDefault", False):
            continue

        name = ""
        is_terraform = False
        for tag in vpc.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
            if tag["Key"] == "ManagedBy" and tag["Value"] == "terraform":
                is_terraform = True

        if is_terraform or "terraform" in name.lower() or name:
            vpcs.append({
                "id": vpc["VpcId"],
                "cidr": vpc["CidrBlock"],
                "name": name or "(unnamed)",
                "state": vpc.get("State", "available")
            })
    return vpcs


def get_subnets(vpc_ids=None):
    """Get subnets grouped by tier."""
    data = run_aws_command("ec2", "describe-subnets")
    if not data:
        return {"public": [], "app": [], "database": []}

    subnets = {"public": [], "app": [], "database": []}
    for subnet in data.get("Subnets", []):
        if vpc_ids and subnet["VpcId"] not in vpc_ids:
            continue

        name = ""
        tier = "app"  # default
        for tag in subnet.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
            if tag["Key"] == "Tier":
                tier = tag["Value"]

        if not name:
            continue

        # Determine tier from name if not tagged
        if "public" in name.lower():
            tier = "public"
        elif "db" in name.lower() or "database" in name.lower():
            tier = "database"
        elif "app" in name.lower() or "private" in name.lower():
            tier = "app"

        subnet_info = {
            "id": subnet["SubnetId"],
            "vpc_id": subnet["VpcId"],
            "cidr": subnet["CidrBlock"],
            "az": subnet.get("AvailabilityZone", ""),
            "name": name
        }

        if tier in subnets:
            subnets[tier].append(subnet_info)

    return subnets


def get_load_balancers(vpc_ids=None):
    """Get Application Load Balancers."""
    data = run_aws_command("elbv2", "describe-load-balancers")
    if not data:
        return []

    albs = []
    for lb in data.get("LoadBalancers", []):
        if vpc_ids and lb.get("VpcId") not in vpc_ids:
            continue

        albs.append({
            "name": lb.get("LoadBalancerName", ""),
            "dns": lb.get("DNSName", ""),
            "arn": lb.get("LoadBalancerArn", ""),
            "state": lb.get("State", {}).get("Code", "unknown"),
            "type": lb.get("Type", "application"),
            "scheme": lb.get("Scheme", "internet-facing")
        })
    return albs


def get_target_groups():
    """Get target groups."""
    data = run_aws_command("elbv2", "describe-target-groups")
    if not data:
        return []

    tgs = []
    for tg in data.get("TargetGroups", []):
        tgs.append({
            "name": tg.get("TargetGroupName", ""),
            "arn": tg.get("TargetGroupArn", ""),
            "port": tg.get("Port", 80),
            "protocol": tg.get("Protocol", "HTTP"),
            "target_type": tg.get("TargetType", "instance")
        })
    return tgs


def get_instances(vpc_ids=None):
    """Get EC2 instances grouped by tier."""
    data = run_aws_command("ec2", "describe-instances")
    if not data:
        return {"web": [], "app": []}

    instances = {"web": [], "app": []}
    for reservation in data.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            if vpc_ids and instance.get("VpcId") not in vpc_ids:
                continue

            name = ""
            tier = "web"  # default
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                if tag["Key"] == "Tier":
                    tier = tag["Value"]

            # Determine tier from name
            if "app" in name.lower():
                tier = "app"
            elif "web" in name.lower():
                tier = "web"

            instance_info = {
                "id": instance["InstanceId"],
                "type": instance.get("InstanceType", ""),
                "state": instance.get("State", {}).get("Name", "unknown"),
                "public_ip": instance.get("PublicIpAddress", ""),
                "private_ip": instance.get("PrivateIpAddress", ""),
                "name": name or "(unnamed)"
            }

            if tier in instances:
                instances[tier].append(instance_info)

    return instances


def get_rds_instances(vpc_ids=None):
    """Get RDS database instances."""
    data = run_aws_command("rds", "describe-db-instances")
    if not data:
        return []

    dbs = []
    for db in data.get("DBInstances", []):
        dbs.append({
            "id": db.get("DBInstanceIdentifier", ""),
            "engine": db.get("Engine", ""),
            "version": db.get("EngineVersion", ""),
            "class": db.get("DBInstanceClass", ""),
            "status": db.get("DBInstanceStatus", ""),
            "endpoint": db.get("Endpoint", {}).get("Address", ""),
            "port": db.get("Endpoint", {}).get("Port", 3306),
            "multi_az": db.get("MultiAZ", False)
        })
    return dbs


def get_security_groups(vpc_ids=None):
    """Get security groups grouped by tier."""
    data = run_aws_command("ec2", "describe-security-groups")
    if not data:
        return {}

    sgs = {"alb": [], "web": [], "app": [], "db": []}
    for sg in data.get("SecurityGroups", []):
        if vpc_ids and sg.get("VpcId") not in vpc_ids:
            continue

        if sg.get("GroupName") == "default":
            continue

        name = sg.get("GroupName", "")
        tier = "web"  # default

        if "alb" in name.lower():
            tier = "alb"
        elif "db" in name.lower():
            tier = "db"
        elif "app" in name.lower():
            tier = "app"
        elif "web" in name.lower():
            tier = "web"

        ingress_ports = []
        for rule in sg.get("IpPermissions", []):
            port = rule.get("FromPort", "all")
            if port != "all":
                ingress_ports.append(str(port))

        sg_info = {
            "id": sg["GroupId"],
            "name": name,
            "description": sg.get("Description", ""),
            "ingress_ports": ingress_ports
        }

        if tier in sgs:
            sgs[tier].append(sg_info)

    return sgs


def generate_html():
    """Generate the dashboard HTML."""
    # Get VPCs first
    vpcs = get_vpcs()
    vpc_ids = [v["id"] for v in vpcs] if vpcs else None

    # Get all resources
    subnets = get_subnets(vpc_ids)
    load_balancers = get_load_balancers(vpc_ids)
    target_groups = get_target_groups()
    instances = get_instances(vpc_ids)
    rds_instances = get_rds_instances(vpc_ids)
    security_groups = get_security_groups(vpc_ids)

    mode = "Real AWS" if USE_AWS else "LocalStack"

    # Count totals
    total_subnets = len(subnets["public"]) + len(subnets["app"]) + len(subnets["database"])
    total_instances = len(instances["web"]) + len(instances["app"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3-Tier Architecture Dashboard - {mode}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #ff9900, #ff6600);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header p {{ color: #888; font-size: 1.1em; }}
        .header .mode {{
            display: inline-block;
            background: {"#ff6b6b" if USE_AWS else "#00d9ff"};
            color: #1a1a2e;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px 30px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            min-width: 120px;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .stat-card .label {{ color: #888; margin-top: 5px; font-size: 0.9em; }}
        .stat-card.vpc .number {{ color: #ff6b6b; }}
        .stat-card.subnet .number {{ color: #4ecdc4; }}
        .stat-card.alb .number {{ color: #ff9900; }}
        .stat-card.ec2 .number {{ color: #45b7d1; }}
        .stat-card.rds .number {{ color: #96ceb4; }}
        .architecture {{
            background: rgba(0,0,0,0.4);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            font-family: monospace;
            white-space: pre;
            overflow-x: auto;
            line-height: 1.6;
            font-size: 13px;
        }}
        .tier-section {{
            margin-bottom: 30px;
        }}
        .tier-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }}
        .tier-header .icon {{ font-size: 1.5em; }}
        .tier-header h2 {{ font-size: 1.3em; }}
        .tier-header .badge {{
            background: rgba(255,255,255,0.2);
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.8em;
        }}
        .resource-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }}
        .resource-card {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #00d9ff;
        }}
        .resource-card.public {{ border-left-color: #ff9900; }}
        .resource-card.web {{ border-left-color: #45b7d1; }}
        .resource-card.app {{ border-left-color: #96ceb4; }}
        .resource-card.database {{ border-left-color: #ff6b6b; }}
        .resource-card.alb {{ border-left-color: #ff9900; }}
        .resource-card h3 {{ color: #fff; margin-bottom: 8px; font-size: 1em; }}
        .resource-card .id {{
            font-family: monospace;
            color: #888;
            font-size: 0.8em;
            word-break: break-all;
        }}
        .resource-card .details {{
            margin-top: 10px;
            font-size: 0.85em;
        }}
        .resource-card .details span {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 2px 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        .status-running, .status-available, .status-active {{ color: #00ff88; }}
        .status-stopped, .status-inactive {{ color: #ff6b6b; }}
        .status-pending {{ color: #feca57; }}
        .empty-state {{
            text-align: center;
            color: #666;
            padding: 30px;
            font-style: italic;
        }}
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #ff9900;
            color: #1a1a2e;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255,153,0,0.3);
        }}
        .refresh-btn:hover {{ background: #ffb347; }}
        .color-internet {{ color: #ff9900; }}
        .color-alb {{ color: #ff9900; }}
        .color-web {{ color: #45b7d1; }}
        .color-app {{ color: #96ceb4; }}
        .color-db {{ color: #ff6b6b; }}
        .color-vpc {{ color: #4ecdc4; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>3-Tier Architecture Dashboard</h1>
        <p>AWS Infrastructure Visualization</p>
        <span class="mode">{mode}</span>
    </div>

    <div class="stats">
        <div class="stat-card vpc">
            <div class="number">{len(vpcs)}</div>
            <div class="label">VPCs</div>
        </div>
        <div class="stat-card subnet">
            <div class="number">{total_subnets}</div>
            <div class="label">Subnets</div>
        </div>
        <div class="stat-card alb">
            <div class="number">{len(load_balancers)}</div>
            <div class="label">Load Balancers</div>
        </div>
        <div class="stat-card ec2">
            <div class="number">{total_instances}</div>
            <div class="label">EC2 Instances</div>
        </div>
        <div class="stat-card rds">
            <div class="number">{len(rds_instances)}</div>
            <div class="label">Databases</div>
        </div>
    </div>
"""

    # Architecture Diagram
    if vpcs:
        vpc = vpcs[0]
        alb = load_balancers[0] if load_balancers else {"name": "ALB", "dns": "pending..."}
        web_count = len(instances["web"])
        app_count = len(instances["app"])
        db = rds_instances[0] if rds_instances else {"id": "RDS", "engine": "mysql", "endpoint": "pending..."}

        alb_sg = security_groups.get("alb", [{}])[0] if security_groups.get("alb") else {"ingress_ports": ["80", "443"]}
        web_sg = security_groups.get("web", [{}])[0] if security_groups.get("web") else {"ingress_ports": ["80"]}
        app_sg = security_groups.get("app", [{}])[0] if security_groups.get("app") else {"ingress_ports": ["8080"]}
        db_sg = security_groups.get("db", [{}])[0] if security_groups.get("db") else {"ingress_ports": ["3306"]}

        html += f"""
    <div class="architecture">
<span class="color-internet">                                    INTERNET
                                       |
                              +--------v--------+
                              |  Internet GW    |
                              +--------+--------+</span>
                                       |
<span class="color-vpc">    +--------------------------------------+--------------------------------------+
    |                              VPC: {vpc['name'][:30]:<30}                           |
    |                              CIDR: {vpc['cidr']:<18}                                    |
    |                                                                                        |</span>
    |  <span class="color-alb">PUBLIC SUBNETS</span>                                                                       |
    |  +-----------------------------------------------------------------------------------+ |
    |  |                                                                                   | |
    |  |   <span class="color-alb">+-------------------+</span>                                                        | |
    |  |   <span class="color-alb">|  Load Balancer    |</span>  <-- Ports: {", ".join(alb_sg.get("ingress_ports", ["80", "443"]))[:15]:<15}                       | |
    |  |   <span class="color-alb">|  {alb['name'][:17]:<17} |</span>                                                        | |
    |  |   <span class="color-alb">+-------------------+</span>                                                        | |
    |  |                  |                                                                | |
    |  +------------------+----------------------------------------------------------------+ |
    |                     |                                                                  |
    |  <span class="color-web">PRIVATE SUBNETS (App Tier)</span>                                                            |
    |  +------------------v----------------------------------------------------------------+ |
    |  |                  |                                                                | |
    |  |   <span class="color-web">+-------------+-------------+</span>                                                 | |
    |  |   <span class="color-web">|   Web Tier ({web_count} instances)   |</span>  <-- Port: {", ".join(web_sg.get("ingress_ports", ["80"]))[:10]:<10}                       | |
    |  |   <span class="color-web">+-------------+-------------+</span>                                                 | |
    |  |                  |                                                                | |
    |  |   <span class="color-app">+-------------v-------------+</span>                                                 | |
    |  |   <span class="color-app">|   App Tier ({app_count} instances)   |</span>  <-- Port: {", ".join(app_sg.get("ingress_ports", ["8080"]))[:10]:<10}                      | |
    |  |   <span class="color-app">+-------------+-------------+</span>                                                 | |
    |  |                  |                                                                | |
    |  +------------------+----------------------------------------------------------------+ |
    |                     |                                                                  |
    |  <span class="color-db">PRIVATE SUBNETS (Database)</span>                                                             |
    |  +------------------v----------------------------------------------------------------+ |
    |  |                  |                                                                | |
    |  |   <span class="color-db">+-------------v-------------+</span>                                                 | |
    |  |   <span class="color-db">|   Database (RDS)          |</span>  <-- Port: {", ".join(db_sg.get("ingress_ports", ["3306"]))[:10]:<10}                      | |
    |  |   <span class="color-db">|   {db['engine'][:10]:<10} {db['id'][:15]:<15}   |</span>                                                 | |
    |  |   <span class="color-db">+---------------------------+</span>                                                 | |
    |  |                                                                                   | |
    |  +-----------------------------------------------------------------------------------+ |
    |                                                                                        |
<span class="color-vpc">    +----------------------------------------------------------------------------------------+</span>
    </div>
"""

    # Load Balancers Section
    html += """
    <div class="tier-section">
        <div class="tier-header">
            <span class="icon">🌐</span>
            <h2>Load Balancers</h2>
            <span class="badge">Public Tier</span>
        </div>
        <div class="resource-grid">
"""
    if load_balancers:
        for alb in load_balancers:
            html += f"""
            <div class="resource-card alb">
                <h3>{alb['name']}</h3>
                <div class="id">{alb['dns']}</div>
                <div class="details">
                    <span>{alb['type']}</span>
                    <span>{alb['scheme']}</span>
                    <span class="status-{alb['state']}">{alb['state']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No load balancers found</div>'
    html += """
        </div>
    </div>
"""

    # Web Tier Section
    html += """
    <div class="tier-section">
        <div class="tier-header">
            <span class="icon">🖥️</span>
            <h2>Web Tier</h2>
            <span class="badge">EC2 Instances</span>
        </div>
        <div class="resource-grid">
"""
    if instances["web"]:
        for inst in instances["web"]:
            html += f"""
            <div class="resource-card web">
                <h3>{inst['name']}</h3>
                <div class="id">{inst['id']}</div>
                <div class="details">
                    <span>{inst['type']}</span>
                    <span class="status-{inst['state']}">{inst['state']}</span>
                    <span>IP: {inst['private_ip'] or 'N/A'}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No web tier instances found</div>'
    html += """
        </div>
    </div>
"""

    # App Tier Section
    html += """
    <div class="tier-section">
        <div class="tier-header">
            <span class="icon">⚙️</span>
            <h2>App Tier</h2>
            <span class="badge">EC2 Instances</span>
        </div>
        <div class="resource-grid">
"""
    if instances["app"]:
        for inst in instances["app"]:
            html += f"""
            <div class="resource-card app">
                <h3>{inst['name']}</h3>
                <div class="id">{inst['id']}</div>
                <div class="details">
                    <span>{inst['type']}</span>
                    <span class="status-{inst['state']}">{inst['state']}</span>
                    <span>IP: {inst['private_ip'] or 'N/A'}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No app tier instances found</div>'
    html += """
        </div>
    </div>
"""

    # Database Tier Section
    html += """
    <div class="tier-section">
        <div class="tier-header">
            <span class="icon">🗄️</span>
            <h2>Database Tier</h2>
            <span class="badge">RDS</span>
        </div>
        <div class="resource-grid">
"""
    if rds_instances:
        for db in rds_instances:
            html += f"""
            <div class="resource-card database">
                <h3>{db['id']}</h3>
                <div class="id">{db['endpoint']}:{db['port']}</div>
                <div class="details">
                    <span>{db['engine']} {db['version']}</span>
                    <span>{db['class']}</span>
                    <span class="status-{db['status']}">{db['status']}</span>
                    <span>{'Multi-AZ' if db['multi_az'] else 'Single-AZ'}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No databases found</div>'
    html += """
        </div>
    </div>
"""

    # Subnets Section
    html += """
    <div class="tier-section">
        <div class="tier-header">
            <span class="icon">🔲</span>
            <h2>Subnets</h2>
        </div>
        <div class="resource-grid">
"""
    for tier, subnet_list in subnets.items():
        for subnet in subnet_list:
            html += f"""
            <div class="resource-card {tier}">
                <h3>{subnet['name']}</h3>
                <div class="id">{subnet['id']}</div>
                <div class="details">
                    <span>CIDR: {subnet['cidr']}</span>
                    <span>AZ: {subnet['az']}</span>
                    <span>{tier.upper()}</span>
                </div>
            </div>
"""
    if total_subnets == 0:
        html += '<div class="empty-state">No subnets found</div>'
    html += """
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
</body>
</html>
"""
    return html


def check_localstack():
    """Check if LocalStack is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", f"{LOCALSTACK_ENDPOINT}/_localstack/health"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except:
        return False


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = generate_html()
            self.wfile.write(html.encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass


def main():
    global USE_AWS

    parser = argparse.ArgumentParser(description="3-Tier Architecture Dashboard")
    parser.add_argument("--aws", action="store_true", help="Use real AWS instead of LocalStack")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    USE_AWS = args.aws

    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  3-Tier Architecture Dashboard{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    if USE_AWS:
        print(f"  Mode: {Colors.YELLOW}Real AWS{Colors.END}")
        print(f"  Checking AWS credentials... ", end="")
        if not check_aws_credentials():
            print(f"{Colors.RED}NOT CONFIGURED{Colors.END}")
            print(f"\n  {Colors.YELLOW}Configure AWS credentials first:{Colors.END}")
            print(f"  aws configure\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")
    else:
        print(f"  Mode: {Colors.CYAN}LocalStack{Colors.END}")
        print(f"  Checking LocalStack... ", end="")
        if not check_localstack():
            print(f"{Colors.RED}NOT RUNNING{Colors.END}")
            print(f"\n  {Colors.YELLOW}Start LocalStack first:{Colors.END}")
            print(f"  docker-compose up -d\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")

    port = 8080
    server = HTTPServer(("localhost", port), DashboardHandler)

    print(f"\n  {Colors.GREEN}Dashboard running at:{Colors.END}")
    print(f"  {Colors.BOLD}http://localhost:{port}{Colors.END}\n")
    print(f"  Press Ctrl+C to stop.\n")

    if not args.no_browser:
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}Dashboard stopped.{Colors.END}\n")
        server.shutdown()


if __name__ == "__main__":
    main()
