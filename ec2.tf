# EC2 Instances for 3-Tier Architecture - STARTER FILE
# ======================================================
# TODO: Create EC2 instances for Web and App tiers!
#
# In this challenge, you'll create:
# - Web Tier: Apache web servers behind the ALB
# - App Tier: Python API servers handling business logic
#
# Architecture:
#   ALB -> Web Tier (Apache/Nginx) -> App Tier (Python API)
#
# Key Concepts:
# - Use count for multiple instances (high availability)
# - Use user_data to bootstrap servers on launch
# - Place instances in private subnets (accessed via ALB)
#
# See README.md for detailed guidance!

# Data source to find latest Amazon Linux 2 AMI (provided for you)
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# =============================================================================
# STEP 1: Web Tier Instances
# =============================================================================
# TODO: Create web server instances
# - Use count to create multiple instances
# - Place in private_app subnets
# - Use user_data to install and configure Apache
#
# resource "aws_instance" "web" {
#   count                  = var.use_ecs ? 0 : var.web_instance_count
#   ami                    = data.aws_ami.amazon_linux.id
#   instance_type          = var.web_instance_type
#   subnet_id              = aws_subnet.private_app[count.index % 2].id
#   vpc_security_group_ids = [aws_security_group.web.id]
#
#   user_data = <<-EOF
#               #!/bin/bash
#               yum update -y
#               yum install -y httpd
#
#               # Start Apache
#               systemctl start httpd
#               systemctl enable httpd
#
#               # Get instance metadata
#               INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
#               AZ=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
#               LOCAL_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
#
#               # Create web page
#               cat <<'HTML' > /var/www/html/index.html
#               <!DOCTYPE html>
#               <html>
#               <head>
#                 <title>Web Tier - ${var.project_name}</title>
#                 <style>
#                   body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
#                   .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
#                   h1 { color: #232f3e; }
#                   .tier { background: #ff9900; color: white; padding: 5px 15px; border-radius: 5px; display: inline-block; }
#                   .info { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
#                   .info p { margin: 5px 0; }
#                 </style>
#               </head>
#               <body>
#                 <div class="container">
#                   <span class="tier">Web Tier</span>
#                   <h1>3-Tier Architecture Demo</h1>
#                   <p>This page is served from the <strong>Web Tier</strong> (EC2 instance behind ALB)</p>
#                   <div class="info">
#                     <p><strong>Server:</strong> Web-${count.index + 1}</p>
#                     <p><strong>Instance ID:</strong> $INSTANCE_ID</p>
#                     <p><strong>Availability Zone:</strong> $AZ</p>
#                     <p><strong>Private IP:</strong> $LOCAL_IP</p>
#                   </div>
#                   <h2>Architecture</h2>
#                   <pre>
#               Internet -> ALB -> [Web Tier] -> App Tier -> Database
#                                     ^
#                                You are here
#                   </pre>
#                 </div>
#               </body>
#               </html>
#               HTML
#
#               # Substitute variables
#               sed -i "s/\$INSTANCE_ID/$INSTANCE_ID/g" /var/www/html/index.html
#               sed -i "s/\$AZ/$AZ/g" /var/www/html/index.html
#               sed -i "s/\$LOCAL_IP/$LOCAL_IP/g" /var/www/html/index.html
#               EOF
#
#   tags = {
#     Name = "${var.project_name}-web-${count.index + 1}"
#     Tier = "web"
#   }
# }

# =============================================================================
# STEP 2: App Tier Instances
# =============================================================================
# TODO: Create app server instances
# - Use count to create multiple instances
# - Place in private_app subnets
# - Use user_data to install Python and run API server
#
# resource "aws_instance" "app" {
#   count                  = var.use_ecs ? 0 : var.app_instance_count
#   ami                    = data.aws_ami.amazon_linux.id
#   instance_type          = var.app_instance_type
#   subnet_id              = aws_subnet.private_app[count.index % 2].id
#   vpc_security_group_ids = [aws_security_group.app.id]
#
#   user_data = <<-EOF
#               #!/bin/bash
#               yum update -y
#
#               # Install Python for simple API server
#               yum install -y python3
#
#               # Create simple app server
#               mkdir -p /opt/app
#               cat <<'PYTHON' > /opt/app/server.py
#               #!/usr/bin/env python3
#               import http.server
#               import json
#               import urllib.request
#               import socketserver
#
#               PORT = 8080
#
#               class AppHandler(http.server.BaseHTTPRequestHandler):
#                   def do_GET(self):
#                       # Get instance metadata
#                       try:
#                           instance_id = urllib.request.urlopen(
#                               'http://169.254.169.254/latest/meta-data/instance-id',
#                               timeout=2
#                           ).read().decode()
#                       except:
#                           instance_id = 'unknown'
#
#                       response = {
#                           'status': 'healthy',
#                           'tier': 'app',
#                           'server': 'app-${count.index + 1}',
#                           'instance_id': instance_id,
#                           'message': 'Hello from App Tier!'
#                       }
#
#                       self.send_response(200)
#                       self.send_header('Content-type', 'application/json')
#                       self.end_headers()
#                       self.wfile.write(json.dumps(response, indent=2).encode())
#
#                   def log_message(self, format, *args):
#                       pass  # Suppress logging
#
#               with socketserver.TCPServer(("", PORT), AppHandler) as httpd:
#                   print(f"App server running on port {PORT}")
#                   httpd.serve_forever()
#               PYTHON
#
#               chmod +x /opt/app/server.py
#
#               # Create systemd service
#               cat <<'SERVICE' > /etc/systemd/system/appserver.service
#               [Unit]
#               Description=App Tier Server
#               After=network.target
#
#               [Service]
#               ExecStart=/usr/bin/python3 /opt/app/server.py
#               Restart=always
#               User=root
#
#               [Install]
#               WantedBy=multi-user.target
#               SERVICE
#
#               # Start app server
#               systemctl daemon-reload
#               systemctl enable appserver
#               systemctl start appserver
#               EOF
#
#   tags = {
#     Name = "${var.project_name}-app-${count.index + 1}"
#     Tier = "app"
#   }
# }
