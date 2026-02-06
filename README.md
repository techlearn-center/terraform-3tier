# Terraform 3-Tier Architecture

> **What you'll create:** Build a production-ready 3-tier web application infrastructure on AWS using Terraform - including load balancer, web/app servers, and database.

---

## Learning Objectives

By the end of this challenge, you will be able to:

1. **Explain** what a 3-tier architecture is, why companies use it, and how it maps to AWS services
2. **Design** a VPC with public, private, and isolated subnets using proper CIDR allocation
3. **Implement** security group chaining where each tier only accepts traffic from the tier above it
4. **Configure** an Application Load Balancer with target groups and health checks
5. **Deploy** EC2 instances (or ECS Fargate containers) across multiple availability zones
6. **Set up** an RDS database in an isolated subnet with encryption and Multi-AZ failover
7. **Test** infrastructure locally using LocalStack before deploying to real AWS

---

## Quick Start

```bash
# 1. Fork and clone this repo

# 2. Install Terraform (see Step 0)

# 3. Choose your approach:
#    - EC2 (traditional) - simpler, start here
#    - ECS (containerized) - modern, learn containers

# 4. Complete the .tf files

# 5. Test locally with LocalStack
docker-compose up -d
terraform init
terraform apply

# 6. Push and check your score!
git push origin main
```

---

## Understanding 3-Tier Architecture

### What is it?

A **3-tier architecture** is a software design pattern that separates an application into three logical layers, each with a specific responsibility. Think of it like a restaurant:

| Tier | Restaurant Analogy | Application Role |
|------|-------------------|------------------|
| **Presentation (Web)** | Dining room & waiters | User interface - what users see and interact with |
| **Application (App)** | Kitchen & chefs | Business logic - processes requests, makes decisions |
| **Data (Database)** | Pantry & storage | Data storage - stores and retrieves information |

### Why Use 3-Tier Architecture?

**1. Security (Defense in Depth)**
```
Internet → [Firewall] → Web Tier → [Firewall] → App Tier → [Firewall] → Database
                ↑                       ↑                        ↑
         Only ports 80/443      Only from Web Tier       Only from App Tier
```
- Database is **never** directly exposed to the internet
- Each tier has its own security rules
- Attackers must breach multiple layers

**2. Scalability (Scale What You Need)**
```
High traffic day?                    Complex calculations?
        ↓                                    ↓
Add more Web servers              Add more App servers
(Database stays same)             (Web tier stays same)
```
- Scale each tier independently based on load
- Cost-effective: only pay for what you need

**3. Maintainability (Change Without Breaking)**
```
Update the UI?          Change business rules?       Switch databases?
      ↓                         ↓                          ↓
Only touch Web Tier     Only touch App Tier        Only touch Data Tier
(App & DB unchanged)    (Web & DB unchanged)       (Web & App unchanged)
```
- Teams can work on different tiers simultaneously
- Updates to one tier don't affect others

**4. Reliability (Failure Isolation)**
```
Web server crashes?     App server overloaded?      DB maintenance?
        ↓                       ↓                        ↓
Load balancer routes    Other app servers           Failover to
to healthy servers      handle requests             standby DB
```

---

## AWS Architecture Diagram

Here's how the 3-tier architecture maps to AWS services:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   INTERNET                                       │
│                                      🌐                                          │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        ROUTE 53 (DNS)                                     │  │
│  │                    myapp.example.com → ALB                                │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────────┐
│                              VPC (10.0.0.0/16)                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                    PUBLIC SUBNETS (10.0.1.0/24, 10.0.2.0/24)               │ │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│  │  │              APPLICATION LOAD BALANCER (ALB)                         │  │ │
│  │  │     ┌─────────────┐                        ┌─────────────┐           │  │ │
│  │  │     │   AZ-1a     │                        │   AZ-1b     │           │  │ │
│  │  │     │  ┌───────┐  │                        │  ┌───────┐  │           │  │ │
│  │  │     │  │  ALB  │  │◄── Health Checks ────► │  │  ALB  │  │           │  │ │
│  │  │     │  │ Node  │  │    (Multi-AZ)          │  │ Node  │  │           │  │ │
│  │  │     │  └───────┘  │                        │  └───────┘  │           │  │ │
│  │  │     └─────────────┘                        └─────────────┘           │  │ │
│  │  └──────────────────────────────┬───────────────────────────────────────┘  │ │
│  │                                 │ Port 80                                  │ │
│  │  ┌──────────────────────────────▼───────────────────────────────────────┐  │ │
│  │  │                         NAT GATEWAY                                  │  │ │
│  │  │              (Allows private subnets to reach internet)              │  │ │
│  │  └──────────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌─────────────────────────────────▼──────────────────────────────────────────┐ │
│  │              PRIVATE SUBNETS - APP (10.0.10.0/24, 10.0.11.0/24)            │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                      WEB TIER (EC2 / ECS)                           │   │ │
│  │  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │ │
│  │  │   │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │             │   │ │
│  │  │   │  │ Web 1 │  │    │  │ Web 2 │  │    │  │ Web 3 │  │  Auto       │   │ │
│  │  │   │  │ Nginx │  │    │  │ Nginx │  │    │  │ Nginx │  │  Scaling    │   │ │
│  │  │   │  └───────┘  │    │  └───────┘  │    │  └───────┘  │  Group      │   │ │
│  │  │   └─────────────┘    └─────────────┘    └─────────────┘             │   │ │
│  │  └─────────────────────────────┬───────────────────────────────────────┘   │ │
│  │                                │ Port 8080                                 │ │
│  │  ┌─────────────────────────────▼───────────────────────────────────────┐   │ │
│  │  │                      APP TIER (EC2 / ECS)                           │   │ │
│  │  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │ │
│  │  │   │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │             │   │ │
│  │  │   │  │ App 1 │  │    │  │ App 2 │  │    │  │ App 3 │  │  Auto       │   │ │
│  │  │   │  │ Node  │  │    │  │ Node  │  │    │  │ Node  │  │  Scaling    │   │ │
│  │  │   │  └───────┘  │    │  └───────┘  │    │  └───────┘  │  Group      │   │ │
│  │  │   └─────────────┘    └─────────────┘    └─────────────┘             │   │ │
│  │  └─────────────────────────────┬───────────────────────────────────────┘   │ │
│  └────────────────────────────────┼───────────────────────────────────────────┘ │
│                                   │ Port 3306                                    │
│  ┌────────────────────────────────▼───────────────────────────────────────────┐ │
│  │            PRIVATE SUBNETS - DB (10.0.20.0/24, 10.0.21.0/24)               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    DATABASE TIER (RDS)                              │   │ │
│  │  │      ┌─────────────────┐              ┌─────────────────┐           │   │ │
│  │  │      │     AZ-1a       │   Sync       │      AZ-1b      │           │   │ │
│  │  │      │  ┌───────────┐  │   Repl.      │  ┌───────────┐  │           │   │ │
│  │  │      │  │  PRIMARY  │  │◄──────────►  │  │  STANDBY  │  │           │   │ │
│  │  │      │  │   MySQL   │  │              │  │   MySQL   │  │           │   │ │
│  │  │      │  └───────────┘  │              │  └───────────┘  │           │   │ │
│  │  │      └─────────────────┘              └─────────────────┘           │   │ │
│  │  │                         Multi-AZ RDS                                │   │ │
│  │  └─────────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

SECURITY GROUPS FLOW:
━━━━━━━━━━━━━━━━━━━━━
Internet ──► ALB-SG (80, 443) ──► Web-SG (80 from ALB) ──► App-SG (8080 from Web) ──► DB-SG (3306 from App)
```

### Visual Architecture References

The ASCII diagrams above show the logical structure. For polished visual diagrams of 3-tier architecture on AWS, see these resources:

- [AWS Well-Architected Labs - Multi-Tier Architecture](https://wellarchitectedlabs.com) — Official AWS reference architectures with detailed diagrams
- [AWS Architecture Blog - Three-Tier Web Architecture](https://aws.amazon.com/architecture/) — Search "three tier" for reference architecture diagrams with icons
- [AWS Icons & Diagram Kit](https://aws.amazon.com/architecture/icons/) — Download official AWS architecture icons to create your own diagrams
- [Draw.io AWS Architecture Templates](https://app.diagrams.net) — Free diagramming tool with AWS shape libraries (search "AWS 3-tier" in templates)

These visual references show the same architecture you're building, rendered with official AWS service icons instead of ASCII art. They're useful for presentations, documentation, and understanding how the pieces connect visually.

---

## Real-World Examples

### Example 1: E-Commerce Website (Amazon-like)

```
USER JOURNEY: "I want to buy a laptop"

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────►│  Web Tier   │────►│  App Tier   │────►│  Database   │
│             │     │             │     │             │     │             │
│ Shows product     │ Serves HTML │     │ Checks      │     │ Stores      │
│ page, images      │ CSS, JS     │     │ inventory   │     │ products,   │
│                   │ React app   │     │ processes   │     │ orders,     │
│                   │             │     │ payment     │     │ users       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Real Companies Using This:**
- **Amazon**: Web (CloudFront + S3), App (EC2 + Lambda), DB (Aurora + DynamoDB)
- **Shopify**: Web (Nginx), App (Ruby on Rails), DB (MySQL + Redis)
- **Etsy**: Web (Apache), App (PHP), DB (MySQL + Memcached)

### Example 2: Social Media Platform (Instagram-like)

```
USER JOURNEY: "I want to post a photo"

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mobile    │────►│  Web Tier   │────►│  App Tier   │────►│  Database   │
│    App      │     │             │     │             │     │             │
│             │     │ API Gateway │     │ Image       │     │ PostgreSQL  │
│ Takes photo │     │ REST/GraphQL│     │ processing  │     │ (posts)     │
│ uploads     │     │             │     │ Feed algo   │     │ S3 (images) │
│             │     │             │     │ Notifications│    │ Redis(cache)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Real Companies Using This:**
- **Instagram**: Web (Django), App (Python + Go), DB (PostgreSQL + Cassandra)
- **Twitter/X**: Web (Scala), App (Java + Scala), DB (MySQL + Manhattan)
- **TikTok**: Web (Go), App (Go + Python), DB (MySQL + Redis)

### Example 3: Banking Application

```
USER JOURNEY: "I want to transfer $100"

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────►│  Web Tier   │────►│  App Tier   │────►│  Database   │
│             │     │             │     │             │     │             │
│ Login page  │     │ HTTPS only  │     │ Auth service│     │ Encrypted   │
│ Dashboard   │     │ WAF protect │     │ Fraud check │     │ at rest     │
│ Transfer UI │     │ Rate limit  │     │ Transaction │     │ Audit logs  │
│             │     │             │     │ processing  │     │ Compliance  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Real Companies Using This:**
- **Chase**: Web (Angular), App (Java Spring), DB (Oracle + DB2)
- **Capital One**: Web (React), App (Java + Python), DB (AWS Aurora)
- **Stripe**: Web (Ruby), App (Ruby + Go), DB (MongoDB + PostgreSQL)

### Example 4: Video Streaming (Netflix-like)

```
USER JOURNEY: "I want to watch a movie"

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Smart TV  │────►│  Web Tier   │────►│  App Tier   │────►│  Database   │
│             │     │             │     │             │     │             │
│ Netflix app │     │ CDN (video) │     │ Recommend   │     │ User prefs  │
│ UI/playback │     │ API Gateway │     │ engine      │     │ Watch hist  │
│             │     │             │     │ Encoding    │     │ Video meta  │
│             │     │             │     │ DRM         │     │ S3 (videos) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Real Companies Using This:**
- **Netflix**: Web (Node.js), App (Java + Python), DB (Cassandra + S3)
- **Disney+**: Web (React), App (Java), DB (AWS services)
- **YouTube**: Web (Python), App (C++ + Python), DB (Bigtable + Spanner)

---

## How Traffic Flows Through 3-Tier

Let's trace a real request step by step:

```
1. USER types "myapp.com" in browser
   │
   ▼
2. DNS (Route 53) resolves to ALB IP address
   │
   ▼
3. REQUEST hits Application Load Balancer
   │  - SSL termination (HTTPS → HTTP)
   │  - Health check: which servers are alive?
   │  - Load balancing: pick least busy server
   │
   ▼
4. ALB forwards to WEB TIER (port 80)
   │  - Web server (Nginx/Apache) receives request
   │  - Serves static files (HTML, CSS, JS, images)
   │  - For dynamic content, calls App Tier
   │
   ▼
5. Web Tier calls APP TIER (port 8080)
   │  - Application server processes business logic
   │  - Validates user input
   │  - Checks permissions
   │  - Needs data? Calls Database
   │
   ▼
6. App Tier queries DATABASE (port 3306)
   │  - SQL query executed
   │  - Data retrieved/stored
   │  - Results returned to App Tier
   │
   ▼
7. RESPONSE travels back
   Database → App Tier → Web Tier → ALB → User
```

---

## Security in 3-Tier Architecture

### The "Onion" Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
│   Attackers are HERE - trying to get to your data               │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   LAYER 1: WAF    │  ← Blocks SQL injection,
                    │   Web App Firewall │    XSS, bad bots
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  LAYER 2: ALB     │  ← Only ports 80/443 open
                    │  Security Group   │    Rate limiting
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  LAYER 3: Web SG  │  ← Only accepts from ALB
                    │  (Private subnet) │    No direct internet
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  LAYER 4: App SG  │  ← Only accepts from Web
                    │  (Private subnet) │    Business logic here
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  LAYER 5: DB SG   │  ← Only accepts from App
                    │  (Isolated subnet)│    Encrypted at rest
                    └───────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    YOUR DATA      │  ← Protected by 5 layers!
                    │  (The treasure)   │
                    └───────────────────┘
```

---

## Do I Need Prior Knowledge?

**You need:**
- Completed the Terraform Basics challenge (or equivalent)
- Understanding of VPCs, subnets, security groups
- Basic networking concepts (public vs private)

**You don't need:**
- AWS account (we'll use LocalStack)
- Prior load balancer or RDS experience
- Container experience (for EC2 path)

**You'll learn:**
- Multi-tier architecture design
- Application Load Balancer (ALB)
- RDS database setup
- Public/private subnet networking
- Security group chaining
- (Optional) ECS/Fargate containers

---

## Choose Your Path

| Path | Difficulty | What You'll Use | Best For |
|------|------------|-----------------|----------|
| **EC2 (Traditional)** | Intermediate | EC2, ALB, RDS | Learning infrastructure basics |
| **ECS (Containerized)** | Advanced | ECS, Fargate, ALB, RDS | Modern cloud-native apps |

**Recommendation:** Start with EC2, then try ECS after.

---

## What You'll Build

### EC2 Path (Traditional)

| File | What You Create | Points |
|------|-----------------|--------|
| `main.tf` | Provider + backend config | 5 |
| `vpc.tf` | VPC, subnets, NAT gateway | 20 |
| `alb.tf` | Application Load Balancer | 20 |
| `ec2.tf` | Web + App tier EC2 instances | 25 |
| `rds.tf` | RDS database | 15 |
| `security.tf` | Security groups for all tiers | 10 |
| `variables.tf` | Input variables | 5 |

### ECS Path (Containerized)

| File | What You Create | Points |
|------|-----------------|--------|
| `main.tf` | Provider + backend config | 5 |
| `vpc.tf` | VPC, subnets, NAT gateway | 20 |
| `alb.tf` | Application Load Balancer | 15 |
| `ecs.tf` | ECS cluster + services | 30 |
| `rds.tf` | RDS database | 15 |
| `security.tf` | Security groups for all tiers | 10 |
| `variables.tf` | Input variables | 5 |

---

## Step 0: Prerequisites

### How Terraform Works

Before diving in, understand what Terraform actually does. You write `.tf` files that describe the infrastructure you want, and Terraform talks to the AWS API to create it:

```
You write code             Terraform does the work              AWS creates resources
┌──────────────┐          ┌──────────────────────┐             ┌──────────────────┐
│  vpc.tf      │          │                      │             │  VPC             │
│  security.tf │  ─────►  │  terraform plan      │  ─────►    │  Subnets         │
│  alb.tf      │  "Here's │  (preview changes)   │  AWS API   │  Security Groups │
│  ec2.tf      │  what I  │                      │  calls     │  Load Balancer   │
│  rds.tf      │  want"   │  terraform apply     │             │  EC2 Instances   │
│              │          │  (create resources)  │             │  RDS Database    │
└──────────────┘          └──────────────────────┘             └──────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  terraform.tfstate   │
                          │  (tracks what exists)│
                          └─────────────────────┘
```

**Key workflow:**
1. `terraform init` — Download providers (AWS plugin)
2. `terraform plan` — Preview what will be created/changed (safe, read-only)
3. `terraform apply` — Actually create the resources
4. `terraform destroy` — Tear everything down

### Install Required Tools

<details>
<summary>Windows</summary>

```powershell
# Terraform
choco install terraform

# Docker Desktop (for LocalStack)
# Download from https://docker.com/products/docker-desktop

# AWS CLI
choco install awscli

# Verify
terraform --version
docker --version
aws --version
```

</details>

<details>
<summary>Mac</summary>

```bash
# Terraform
brew install terraform

# Docker Desktop
brew install --cask docker

# AWS CLI
brew install awscli

# Verify
terraform --version
docker --version
aws --version
```

</details>

<details>
<summary>Linux</summary>

```bash
# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Docker
curl -fsSL https://get.docker.com | sh

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Verify
terraform --version
docker --version
aws --version
```

</details>

### Configure AWS CLI for LocalStack

```bash
# Set dummy credentials for LocalStack
aws configure
# Access Key ID: test
# Secret Access Key: test
# Region: us-east-1
# Output format: json
```

---

## Step 1: Understanding the Architecture

### Network Design

```
VPC: 10.0.0.0/16
│
├── Public Subnets (Internet-facing)
│   ├── 10.0.1.0/24 (AZ-a) ─── ALB, NAT Gateway
│   └── 10.0.2.0/24 (AZ-b) ─── ALB (multi-AZ)
│
├── Private Subnets - App (No direct internet)
│   ├── 10.0.10.0/24 (AZ-a) ─── Web/App servers
│   └── 10.0.11.0/24 (AZ-b) ─── Web/App servers
│
└── Private Subnets - Data (Isolated)
    ├── 10.0.20.0/24 (AZ-a) ─── RDS Primary
    └── 10.0.21.0/24 (AZ-b) ─── RDS Standby
```

### Understanding CIDR Notation

The network design above uses CIDR notation (e.g., `10.0.0.0/16`). If this is new to you, here's what it means:

**The `/number` tells you how many IP addresses are available:**

```
CIDR             What it means                    IP addresses
──────────────   ──────────────────────────────   ────────────
10.0.0.0/16      10.0.0.0 → 10.0.255.255         65,536 IPs (the whole VPC)
10.0.1.0/24      10.0.1.0 → 10.0.1.255           256 IPs (one subnet)
10.0.10.0/24     10.0.10.0 → 10.0.10.255         256 IPs (one subnet)
10.0.20.0/24     10.0.20.0 → 10.0.20.255         256 IPs (one subnet)
```

**Think of it like a building with floors and rooms:**

```
VPC 10.0.0.0/16 = The entire building (65,536 rooms)
│
├── /24 subnets = individual floors (256 rooms each)
│   ├── Floor 1  (10.0.1.0/24)  = Public subnet AZ-a
│   ├── Floor 2  (10.0.2.0/24)  = Public subnet AZ-b
│   ├── Floor 10 (10.0.10.0/24) = App subnet AZ-a
│   ├── Floor 11 (10.0.11.0/24) = App subnet AZ-b
│   ├── Floor 20 (10.0.20.0/24) = DB subnet AZ-a
│   └── Floor 21 (10.0.21.0/24) = DB subnet AZ-b
```

**The `cidrsubnet()` function in Terraform:**

In the hints and solutions, you'll see `cidrsubnet(var.vpc_cidr, 8, count.index + 1)`. Here's what the 3 arguments mean:

```
cidrsubnet("10.0.0.0/16",  8,  1)
             │               │   │
             │               │   └─ Which subnet number? (1 = 10.0.1.0/24)
             │               └─── Add 8 bits to the prefix (16+8=24, so /24 subnets)
             └─────────────────── The VPC CIDR to subdivide

Examples:
  cidrsubnet("10.0.0.0/16", 8, 1)  → "10.0.1.0/24"
  cidrsubnet("10.0.0.0/16", 8, 2)  → "10.0.2.0/24"
  cidrsubnet("10.0.0.0/16", 8, 10) → "10.0.10.0/24"
  cidrsubnet("10.0.0.0/16", 8, 20) → "10.0.20.0/24"
```

### Security Group Rules

```
Internet ──► ALB (port 80/443)
             │
             ▼
         Web Tier SG ◄── Only ALB can access (port 80)
             │
             ▼
         App Tier SG ◄── Only Web Tier can access (port 8080)
             │
             ▼
          RDS SG ◄── Only App Tier can access (port 3306/5432)
```

### Checkpoint: Self-Reflection

- [ ] **Q1:** Why are there 3 types of subnets (public, private-app, private-db) instead of just public and private?
- [ ] **Q2:** What would happen if the database was in a public subnet?
- [ ] **Q3:** Why do we need a NAT Gateway? What can private subnets NOT do without one?
- [ ] **Q4:** Why deploy across 2 Availability Zones instead of 1?

---

## Step 2: Set Up LocalStack

### What is LocalStack?

**LocalStack is a fake AWS that runs on your laptop.** It simulates AWS services locally so you can test your Terraform code without:
- Needing an AWS account
- Paying for any resources
- Waiting for real infrastructure to provision
- Accidentally leaving resources running and getting charged

It works by running a Docker container that exposes the same API endpoints as AWS, but everything stays on your machine.

> **Important: LocalStack Community vs Pro**
>
> LocalStack **Community Edition** (free, what we use) supports: **EC2, VPC, Subnets, Security Groups, IAM, S3, CloudWatch**.
>
> LocalStack **Pro** (paid) adds: **ELBv2 (ALB), RDS, ECS**, and more.
>
> **What this means for you:**
> - `terraform apply` will successfully create VPCs, subnets, security groups, and EC2 instances
> - `terraform apply` will **fail** on ALB and RDS resources with a `501` error — this is expected, not a bug in your code
> - Your ALB and RDS code is validated by `python run.py` and `terraform validate` instead
> - Visit **http://localhost:3000** after `docker-compose up -d` for a preview of the web tier page

### How the Provider Override Works

When you use Terraform with real AWS, it sends API calls to `https://ec2.us-east-1.amazonaws.com`. With LocalStack, we redirect those calls to `http://localhost:4566` instead.

The file `provider_override.tf.example` contains this redirect configuration. You'll copy it to `provider_override.tf` to activate it:

```
Real AWS:        .tf files → Terraform → https://aws.amazon.com → Real resources ($$$)
LocalStack:      .tf files → Terraform → http://localhost:4566  → Simulated resources (free)
```

### Start LocalStack

```bash
# Start LocalStack
docker-compose up -d

# Wait for it to be ready (about 30 seconds)
docker-compose logs -f
# Look for "Ready." message, then Ctrl+C

# Verify LocalStack is running
curl http://localhost:4566/_localstack/health
```

**Expected output:**
```json
{"services": {"ec2": "running", "iam": "running", "sts": "running", ...}}
```
> Note: `elbv2` and `rds` may show as `"available"` in the health check but will return `501` errors when you try to create resources — this is a Community Edition limitation.

### Activate the Provider Override

```bash
# Copy the override file to redirect Terraform to LocalStack
cp provider_override.tf.example provider_override.tf

# Initialize Terraform (downloads the AWS provider)
terraform init
```

---

## How the Starter Files Work

Before you start coding, understand what's in the repo. Each `.tf` file contains **commented-out starter code** with TODO markers. Your job is to **uncomment the code and fill in any missing parts**.

Here's an example from `main.tf`:

```hcl
# What you'll see (starter):
# TODO: Uncomment and configure the AWS provider
# aws = {
#   source  = "hashicorp/aws"
#   version = "~> 5.0"
# }

# What you need to change it to (uncommented + completed):
aws = {
  source  = "hashicorp/aws"
  version = "~> 5.0"
}
```

**The workflow for each step:**
1. Open the `.tf` file mentioned in the step
2. Read the TODO comments to understand what's needed
3. Use the README hints if you get stuck
4. Uncomment and complete the code
5. Run `terraform validate` to check syntax
6. Run `python run.py` to check your score

### Check Your Starting Score

Run the progress checker now to see your baseline:

```bash
python run.py
```

You should see 0/100 points. As you complete each step, your score will increase.

---

## EC2 Path: Traditional 3-Tier

> **🖥️ ENVIRONMENT: LocalStack (Local Testing)**
>
> All steps below (Steps 3–8) run against **LocalStack on your machine** — not real AWS.
> Nothing costs money. Nothing leaves your laptop. If you completed Step 2, your `provider_override.tf` is redirecting all Terraform commands to `http://localhost:4566`.
>
> **How to verify you're using LocalStack (run this anytime):**
> ```bash
> # If this file exists, you're using LocalStack. If not, you're pointing at real AWS.
> ls provider_override.tf
> ```
>
> You will NOT touch real AWS until the optional ["Deploying to Real AWS"](#deploying-to-real-aws) section at the very end.

---

### Step 3: Create the VPC and Networking

Complete `vpc.tf`:

**Requirements:**
- [ ] VPC with CIDR 10.0.0.0/16
- [ ] 2 public subnets (different AZs)
- [ ] 2 private subnets for app tier
- [ ] 2 private subnets for database tier
- [ ] Internet Gateway for public subnets
- [ ] NAT Gateway for private subnet internet access
- [ ] Route tables for each subnet type

<details>
<summary>Hint 1: VPC and Subnets</summary>

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
    Tier = "public"
  }
}
```

</details>

<details>
<summary>Hint 2: NAT Gateway</summary>

```hcl
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.project_name}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}
```

</details>

<details>
<summary>Full VPC Solution</summary>

```hcl
# Data source for AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
    Tier = "public"
  }
}

# Private Subnets - App Tier
resource "aws_subnet" "private_app" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-app-${count.index + 1}"
    Tier = "app"
  }
}

# Private Subnets - Database Tier
resource "aws_subnet" "private_db" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-db-${count.index + 1}"
    Tier = "database"
  }
}

# Elastic IP for NAT
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.project_name}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_app" {
  count          = 2
  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_db" {
  count          = 2
  subnet_id      = aws_subnet.private_db[count.index].id
  route_table_id = aws_route_table.private.id
}
```

</details>

### Checkpoint: Self-Reflection

- [ ] **Q1:** What does the NAT Gateway enable private subnets to do? Why not just attach an Internet Gateway to private subnets?
- [ ] **Q2:** Why do we place the NAT Gateway in a public subnet?
- [ ] **Q3:** What does `depends_on = [aws_internet_gateway.main]` do? What would happen without it?

### Check Your Progress (LocalStack)

```bash
terraform validate          # Check syntax
terraform apply             # Apply to LocalStack (free, local only)
python run.py               # Should show ~25/100 (provider + VPC)
```

> Remember: `terraform apply` here hits LocalStack, not real AWS. You can run it as many times as you want with zero cost.

---

### Step 4: Create Security Groups

Complete `security.tf`:

**Requirements:**
- [ ] ALB security group (allow 80, 443 from internet)
- [ ] Web tier security group (allow from ALB only)
- [ ] App tier security group (allow from web tier only)
- [ ] Database security group (allow from app tier only)

<details>
<summary>Hint: Security Group Chain</summary>

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# Web Tier - Only from ALB
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]  # Only ALB!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}
```

</details>

<details>
<summary>Full Security Groups Solution</summary>

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
    Tier = "public"
  }
}

# Web Tier Security Group
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Security group for Web tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
    Tier = "web"
  }
}

# App Tier Security Group
resource "aws_security_group" "app" {
  name        = "${var.project_name}-app-sg"
  description = "Security group for App tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "App port from Web tier"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg"
    Tier = "app"
  }
}

# Database Tier Security Group
resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg"
  description = "Security group for Database tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from App tier"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-db-sg"
    Tier = "database"
  }
}
```

</details>

### Checkpoint: Self-Reflection

- [ ] **Q1:** Why do we reference `security_groups = [aws_security_group.alb.id]` instead of using a CIDR block like `cidr_blocks = ["10.0.1.0/24"]`? What's the advantage?
- [ ] **Q2:** What does `protocol = "-1"` mean in the egress rules?
- [ ] **Q3:** If an attacker compromises a web server, can they directly access the database? Why or why not?

### Check Your Progress (LocalStack)

```bash
terraform apply             # Apply to LocalStack (free, local only)
python run.py               # Should show ~35/100 (provider + VPC + security)
```

---

### Step 5: Create the Application Load Balancer

Complete `alb.tf`:

**Requirements:**
- [ ] Application Load Balancer in public subnets
- [ ] Target group for web tier instances
- [ ] HTTP listener on port 80
- [ ] Health check configuration

<details>
<summary>Hint: ALB Components</summary>

```hcl
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${var.project_name}-alb"
  }
}

resource "aws_lb_target_group" "web" {
  name     = "${var.project_name}-web-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    path                = "/"
    timeout             = 5
    unhealthy_threshold = 2
  }
}
```

</details>

<details>
<summary>Full ALB Solution</summary>

```hcl
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

# Target Group for Web Tier
resource "aws_lb_target_group" "web" {
  name     = "${var.project_name}-web-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

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

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# Attach EC2 instances to target group
resource "aws_lb_target_group_attachment" "web" {
  count            = var.web_instance_count
  target_group_arn = aws_lb_target_group.web.arn
  target_id        = aws_instance.web[count.index].id
  port             = 80
}
```

</details>

### Checkpoint: Self-Reflection

- [ ] **Q1:** What happens if ALL targets in the target group fail health checks? What does the user see?
- [ ] **Q2:** Why is the ALB in public subnets but the web servers are in private subnets?
- [ ] **Q3:** What does `matcher = "200"` mean in the health check? What if your app returns a 302 redirect on `/`?

### Check Your Progress (LocalStack)

```bash
terraform validate          # Check syntax (works for all resources)
python run.py               # Should show ~55/100 (provider + VPC + security + ALB)
```

> Note: `terraform apply` will fail for ALB resources on LocalStack Community (501 error). This is expected — elbv2 is a Pro-only service. Your ALB code is validated by `python run.py` and `terraform validate`.

---

### Step 6: Create EC2 Instances

Complete `ec2.tf`:

**Requirements:**
- [ ] Web tier EC2 instances (2) in private app subnets
- [ ] App tier EC2 instances (2) in private app subnets
- [ ] User data scripts to install web server / app server
- [ ] Proper security group attachments

<details>
<summary>Hint: EC2 with User Data</summary>

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "web" {
  count                  = var.web_instance_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.web_instance_type
  subnet_id              = aws_subnet.private_app[count.index % 2].id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Web Server ${count.index + 1}</h1>" > /var/www/html/index.html
              EOF

  tags = {
    Name = "${var.project_name}-web-${count.index + 1}"
    Tier = "web"
  }
}
```

</details>

<details>
<summary>Full EC2 Solution</summary>

```hcl
# Find latest Amazon Linux 2 AMI
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

# Web Tier Instances
resource "aws_instance" "web" {
  count                  = var.web_instance_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.web_instance_type
  subnet_id              = aws_subnet.private_app[count.index % 2].id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd

              # Create web page
              cat <<'HTML' > /var/www/html/index.html
              <!DOCTYPE html>
              <html>
              <head><title>Web Tier</title></head>
              <body>
                <h1>Web Server ${count.index + 1}</h1>
                <p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
                <p>Availability Zone: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)</p>
              </body>
              </html>
              HTML
              EOF

  tags = {
    Name = "${var.project_name}-web-${count.index + 1}"
    Tier = "web"
  }
}

# App Tier Instances
resource "aws_instance" "app" {
  count                  = var.app_instance_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.app_instance_type
  subnet_id              = aws_subnet.private_app[count.index % 2].id
  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y java-11-amazon-corretto

              # Simple app server simulation
              mkdir -p /opt/app
              cat <<'JAVA' > /opt/app/SimpleServer.java
              import com.sun.net.httpserver.*;
              import java.io.*;
              import java.net.*;
              public class SimpleServer {
                public static void main(String[] args) throws Exception {
                  HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
                  server.createContext("/health", exchange -> {
                    String response = "{\"status\":\"healthy\",\"server\":\"app-${count.index + 1}\"}";
                    exchange.sendResponseHeaders(200, response.length());
                    exchange.getResponseBody().write(response.getBytes());
                    exchange.close();
                  });
                  server.start();
                }
              }
              JAVA

              cd /opt/app && javac SimpleServer.java && java SimpleServer &
              EOF

  tags = {
    Name = "${var.project_name}-app-${count.index + 1}"
    Tier = "app"
  }
}
```

</details>

### Checkpoint: Self-Reflection

- [ ] **Q1:** Why are EC2 instances placed in private subnets instead of public subnets? Users need to reach them — how does traffic get there?
- [ ] **Q2:** What does `user_data` do? When does it run? What happens if it fails?
- [ ] **Q3:** What does `count.index % 2` achieve? Why not just `count.index`?

### Check Your Progress (LocalStack)

```bash
terraform validate          # Check syntax (works for all resources)
terraform apply             # VPC/SG/EC2 will succeed; ALB will fail (expected on Community)
python run.py               # Should show ~80/100 (provider + VPC + security + ALB + EC2)
```

---

### Step 7: Create RDS Database

Complete `rds.tf`:

**Requirements:**
- [ ] DB subnet group using private database subnets
- [ ] RDS MySQL instance
- [ ] Proper security group attachment
- [ ] Multi-AZ for high availability (optional)

<details>
<summary>Hint: RDS Setup</summary>

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private_db[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier           = "${var.project_name}-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = var.db_instance_class
  allocated_storage    = 20
  storage_type         = "gp2"

  db_name              = var.db_name
  username             = var.db_username
  password             = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  skip_final_snapshot  = true

  tags = {
    Name = "${var.project_name}-db"
    Tier = "database"
  }
}
```

</details>

<details>
<summary>Full RDS Solution</summary>

```hcl
# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name        = "${var.project_name}-db-subnet-group"
  description = "Database subnet group for ${var.project_name}"
  subnet_ids  = aws_subnet.private_db[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# RDS MySQL Instance
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  multi_az               = var.db_multi_az
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  tags = {
    Name = "${var.project_name}-db"
    Tier = "database"
  }
}
```

</details>

### Checkpoint: Self-Reflection

- [ ] **Q1:** Why do we need a DB subnet group? Why can't we just specify a single subnet for RDS?
- [ ] **Q2:** What does Multi-AZ protect against? What does it NOT protect against? (Hint: think about data corruption vs hardware failure)
- [ ] **Q3:** Why is `publicly_accessible = false` important for a database?
- [ ] **Q4:** The password is set with `default = "changeme123!"` in variables.tf. Why is this bad for production? How would you fix it?

### Check Your Progress (LocalStack)

```bash
terraform validate          # Check syntax (works for all resources)
python run.py               # Should show ~95-100/100
```

> Note: `terraform apply` will fail for RDS resources on LocalStack Community (501 error). This is expected — rds is a Pro-only service. Your RDS code is validated by `python run.py` and `terraform validate`.

---

### Step 8: Variables and Outputs

The `variables.tf` file is already complete with all needed variables. The `outputs.tf` file contains commented-out outputs organized by section — **uncomment outputs as you uncomment the corresponding resources**. On LocalStack Community, keep ALB and RDS outputs commented since those resources can't be created.

Review the variables to understand what they define:

**variables.tf** — Input variables with defaults:

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "terraform-3tier"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "web_instance_count" {
  description = "Number of web tier instances"
  type        = number
  default     = 2
}

variable "web_instance_type" {
  description = "Web tier instance type"
  type        = string
  default     = "t2.micro"
}

variable "app_instance_count" {
  description = "Number of app tier instances"
  type        = number
  default     = 2
}

variable "app_instance_type" {
  description = "App tier instance type"
  type        = string
  default     = "t2.micro"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = "changeme123!"
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}
```

**outputs.tf** — Values displayed after `terraform apply`:

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "Application URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "web_instance_ids" {
  description = "Web tier instance IDs"
  value       = aws_instance.web[*].id
}

output "app_instance_ids" {
  description = "App tier instance IDs"
  value       = aws_instance.app[*].id
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}
```

---

## ECS Path: Containerized 3-Tier

> **🖥️ ENVIRONMENT: LocalStack (Local Testing)**
>
> Like the EC2 path, all ECS steps run against **LocalStack on your machine**. Nothing costs money.

> **Note:** Complete the VPC (Step 3) and Security Groups (Step 4) from the EC2 path first! The ECS path reuses those resources.

### Step 9a: Create the ECS Cluster

Complete `ecs.tf` — start with the cluster and IAM role:

**Requirements:**
- [ ] ECS cluster with container insights enabled
- [ ] IAM execution role for ECS tasks

<details>
<summary>Hint: ECS Cluster and IAM</summary>

```hcl
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "web" {
  family                   = "${var.project_name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = "nginx:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
    }
  ])
}
```

</details>

### Step 9b: Create Task Definitions

Define what containers to run for web and app tiers. Task definitions are like Docker Compose service definitions — they specify the image, CPU, memory, ports, and environment variables.

### Step 9c: Create ECS Services

Services ensure the desired number of tasks (containers) are always running, and connect them to the load balancer.

<details>
<summary>Full ECS Solution</summary>

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ECS Execution Role
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-ecs-execution"

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
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Web Tier Task Definition
resource "aws_ecs_task_definition" "web" {
  family                   = "${var.project_name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = "nginx:latest"
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
          awslogs-group         = "/ecs/${var.project_name}-web"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "web"
        }
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
  family                   = "${var.project_name}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = "node:18-alpine"
      essential = true
      command   = ["node", "-e", "require('http').createServer((req,res)=>{res.end(JSON.stringify({status:'healthy'}))}).listen(8080)"]
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
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.project_name}-app"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "app"
        }
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-app-task"
    Tier = "app"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${var.project_name}-web"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}-app"
  retention_in_days = 7
}

# Web Tier ECS Service
resource "aws_ecs_service" "web" {
  name            = "${var.project_name}-web-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_instance_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.web.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web_ecs.arn
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
  name            = "${var.project_name}-app-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
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

# Target Group for ECS (different health check)
resource "aws_lb_target_group" "web_ecs" {
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
```

</details>

### Checkpoint: Self-Reflection (ECS Path)

- [ ] **Q1:** What is the difference between an ECS Task Definition and an ECS Service?
- [ ] **Q2:** Why does the ECS target group use `target_type = "ip"` instead of `"instance"`?
- [ ] **Q3:** What advantage does Fargate have over EC2 for this architecture? What do you NOT have to manage?
- [ ] **Q4:** Why do we need an IAM execution role for ECS tasks? What permissions does it grant?

---

## Testing Locally with LocalStack

> **🖥️ ENVIRONMENT: LocalStack (Local Testing)** — This entire section runs on your machine. No AWS costs.

### LocalStack Community Limitations

LocalStack **Community Edition** (free) does **not** support `elbv2` (ALB) or `rds`. These are **Pro-only** services. This means:

| Resource | `terraform apply` on LocalStack Community | How to validate |
|----------|------------------------------------------|-----------------|
| VPC, Subnets, IGW, NAT, Route Tables | Works | `terraform apply` + CLI |
| Security Groups | Works | `terraform apply` + CLI |
| EC2 Instances | Works | `terraform apply` + CLI |
| **ALB, Target Groups, Listeners** | **Fails (501 error)** | `python run.py` + `terraform validate` |
| **RDS, DB Subnet Group** | **Fails (501 error)** | `python run.py` + `terraform validate` |

**The 501 errors on ALB and RDS are expected** — they are not bugs in your code.

### Recommended Workflow (LocalStack Community)

```bash
# 1. Start LocalStack (skip if already running)
docker-compose up -d

# 2. Copy LocalStack provider override (skip if already done)
cp provider_override.tf.example provider_override.tf

# 3. Initialize Terraform (skip if already done)
terraform init

# 4. Validate your code (checks syntax and references — works for ALL resources)
terraform validate

# 5. Check your progress (reads your .tf files — works for ALL resources)
python run.py --verbose

# 6. Apply what LocalStack supports (VPC, subnets, SGs, EC2)
#    ALB and RDS will show errors — that's expected on Community Edition
terraform apply
# Type "yes" to confirm

# 7. See the web tier preview
#    Open http://localhost:3000 in your browser
```

**Expected `terraform apply` output on LocalStack Community:**
```
Apply complete! Resources: ~15 added, 0 changed, 0 destroyed.

# You will also see errors like:
# Error: ... elbv2 ... not included in your current license plan
# Error: ... rds ... not included in your current license plan
# These are EXPECTED — ALB and RDS require LocalStack Pro.
```

> **Your score comes from `python run.py`**, which checks your `.tf` files for correct code structure. It works the same whether you're using LocalStack or real AWS — it reads your code, not your running infrastructure. The ALB/RDS errors from `terraform apply` do not affect your score.

### Verify Deployed Resources with CLI (LocalStack)

These commands verify resources that LocalStack Community supports. They use `--endpoint-url=http://localhost:4566` to target LocalStack.

```bash
# List all VPCs
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs \
  --query "Vpcs[*].{VpcId:VpcId,CIDR:CidrBlock,Name:Tags[?Key=='Name']|[0].Value}" \
  --output table

# List all subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets \
  --query "Subnets[*].{SubnetId:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,Tier:Tags[?Key=='Tier']|[0].Value}" \
  --output table

# List EC2 instances
aws --endpoint-url=http://localhost:4566 ec2 describe-instances \
  --query "Reservations[*].Instances[*].{InstanceId:InstanceId,Type:InstanceType,Tier:Tags[?Key=='Tier']|[0].Value,State:State.Name}" \
  --output table

# List Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups \
  --query "SecurityGroups[?GroupName!='default'].{Name:GroupName,Id:GroupId}" \
  --output table
```

### Automated Verification

Instead of running the CLI commands above manually, you can verify all deployed resources at once:

```bash
python run.py --verify
```

This checks LocalStack for VPCs, subnets, security groups, and EC2 instances. ALB and RDS checks will show as unavailable on Community Edition — that's expected.

### Web Tier Preview

After running `docker-compose up -d` and `terraform apply`, visit:

**http://localhost:3000**

This shows a preview of what the ALB would serve in production (the Web Tier page from your EC2 instances).

> **Why a preview instead of the real ALB URL?**
>
> LocalStack Community Edition creates ALB resources via the API (you can see them with `describe-load-balancers`), but it does **not** route real HTTP traffic through the ALB. This is a known limitation of the free tier — the ALB is registered as a resource, but visiting its DNS name returns a **502 Bad Gateway** because no actual load balancer process is running behind it.
>
> The preview container (`web-preview` in docker-compose) serves the same page that the EC2 user_data script would create, so you can see what your infrastructure would look like on real AWS.
>
> To verify your ALB configuration is correct, use `python run.py --verify` or the CLI commands above.

### Visual Dashboard

```bash
python dashboard.py
```

Opens a web page at http://localhost:8080 showing:
- Architecture diagram with all 3 tiers
- VPC and subnet visualization
- ALB with target group status
- EC2/ECS instances per tier
- RDS database status

---

## Challenge Complete — What's Next?

If you've reached **100/100 on `python run.py`**, congratulations — **the challenge is done!** Your Terraform code is correct and complete. Everything was validated locally — no AWS account needed and nothing cost money.

> Note: On LocalStack Community, `terraform apply` only fully works for VPC/subnets/security groups/EC2. The ALB and RDS 501 errors are expected (Pro-only services) and do **not** affect your score. Your code is validated by `python run.py` and `terraform validate`.

**You can stop here.** The section below is entirely optional.

---

## (Optional) Deploying to Real AWS

> **⚠️ ENVIRONMENT CHANGE: Real AWS (costs real money)**
>
> Everything below this line creates **real infrastructure in your AWS account** that **costs money** (~$95/month after free tier).
> Do NOT proceed unless you:
> 1. Have an AWS account with billing enabled
> 2. Understand you will be charged for running resources
> 3. Will run `terraform destroy` immediately when done testing
>
> **How to switch from LocalStack to real AWS:**
> ```bash
> # Delete the LocalStack override — this is what tells Terraform to use real AWS
> rm provider_override.tf
>
> # Reinitialize Terraform (it will now download the real AWS provider config)
> terraform init
> ```
>
> **How to verify which environment you're targeting:**
> ```bash
> # If this file EXISTS → you're using LocalStack (safe, free)
> # If this file is GONE → you're pointing at real AWS ($$$)
> ls provider_override.tf
> ```

### Prerequisites

1. **AWS Account with billing enabled**
2. **IAM User with these permissions:**
   - `AmazonVPCFullAccess`
   - `AmazonEC2FullAccess`
   - `ElasticLoadBalancingFullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonECS_FullAccess` (for ECS path)

3. **Configure AWS CLI:**
   ```bash
   aws configure
   # Enter your real Access Key ID
   # Enter your real Secret Access Key
   # Region: us-east-1
   ```

### Deploy

If you haven't already, switch to real AWS (see the environment change box above):

```bash
# Verify LocalStack override is removed
ls provider_override.tf  # Should say "No such file"

# Update variables for production
# Edit terraform.tfvars or use -var flags
# IMPORTANT: Change the default database password from "changeme123!"

# Plan first — review what will be created
terraform plan

# Apply — THIS CREATES REAL RESOURCES THAT COST MONEY
terraform apply
# Type "yes" only if you've reviewed the plan above
```

### Verify in AWS Console

1. **VPC** - Check VPC dashboard for new VPC and subnets
2. **EC2** - Check running instances in each tier
3. **RDS** - Check database instance
4. **Load Balancer** - Get the ALB URL and test

### Access Your Application

```bash
# Get the ALB URL
terraform output alb_url

# Test the application
curl $(terraform output -raw alb_url)
```

### IMPORTANT: Clean Up!

```bash
# Destroy all resources when done
terraform destroy
# Type "yes" to confirm

# Verify cleanup
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=terraform-3tier"
# Should return empty
```

### Cost Estimate

| Resource | Free Tier | After Free Tier |
|----------|-----------|-----------------|
| t2.micro EC2 (x4) | 750 hrs/month free | ~$34/month |
| ALB | Not free tier | ~$16/month |
| NAT Gateway | Not free tier | ~$32/month |
| RDS db.t3.micro | 750 hrs free | ~$12/month |
| Data transfer | 100GB free | $0.09/GB |

**Estimated monthly cost: ~$95/month** (after free tier)

**Tip:** Run `terraform destroy` immediately after testing!

---

## Run the Progress Checker

> `python run.py` checks your `.tf` files for correct structure. It works the same whether you're using LocalStack or real AWS — it reads your code, not your running infrastructure.

```bash
python run.py
```

**Expected output when complete (EC2 path):**
```
============================================================
  Terraform 3-Tier Architecture Challenge
============================================================

  Path: EC2 (Traditional)

  [PASS] Provider Config (5/5 points)
  [PASS] VPC & Networking (20/20 points)
  [PASS] Security Groups (10/10 points)
  [PASS] Application Load Balancer (20/20 points)
  [PASS] EC2 Instances (25/25 points)
  [PASS] RDS Database (15/15 points)
  [PASS] Variables (5/5 points)

============================================================
  Total Score: 100/100
  CHALLENGE COMPLETE!
============================================================
```

For detailed output showing each individual check:

```bash
python run.py --verbose
```

---

## Final Self-Reflection

Before you move on, test your understanding. Try answering these without looking back:

1. **Draw the 3-tier architecture from memory.** Include the VPC, all 6 subnets, the ALB, EC2/ECS instances, RDS, and security group flow. Label which subnets are public vs private.

2. **Explain to a non-technical colleague** why the database is never directly accessible from the internet. Use the restaurant or onion analogy.

3. **A junior engineer asks:** "Why can't we just put everything in public subnets? It's simpler." What are the 3 biggest risks of that approach?

4. **Your `terraform apply` created 25 resources.** If you accidentally delete the `terraform.tfstate` file, what happens? Can Terraform still manage those resources?

5. **You need to scale for Black Friday traffic.** Which tier(s) would you scale? How would you change the Terraform code? What stays the same?

If you can answer all 5 confidently, you have a solid understanding of 3-tier architecture and Terraform.

---

## (Bonus) Customize the Web Page

> **When to do this:** Only after deploying to **real AWS** and successfully accessing your ALB URL in a browser. This does NOT work on LocalStack.
>
> **What you'll see first:** The default nginx or Apache welcome page. This means your infrastructure is working correctly!
>
> **What this bonus does:** Replace the default page with a custom page showing instance metadata, proving the ALB is load balancing.

If your ALB URL (`terraform-3tier-alb-xxx.us-east-1.elb.amazonaws.com`) shows the default web server page, your infrastructure is working. This optional step customizes that page.

### SSH into a Web Instance

First, connect to one of your web EC2 instances. Since they're in private subnets, you'll need either:
- **AWS Systems Manager Session Manager** (recommended, no bastion needed)
- A bastion host in a public subnet

```bash
# Using Session Manager (if you added the IAM role):
aws ssm start-session --target i-xxxxxxxxx

# Or via bastion:
ssh -J ec2-user@bastion-ip ec2-user@web-instance-private-ip
```

### Create Custom Page (Apache httpd)

```bash
# Get instance metadata
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
AZ=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
LOCAL_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

# Create custom page
cat <<EOF | sudo tee /var/www/html/index.html
<!DOCTYPE html>
<html>
<head>
  <title>Web Tier - 3-Tier Demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
    .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; }
    h1 { color: #232f3e; }
    .tier { background: #ff9900; color: white; padding: 5px 15px; border-radius: 5px; display: inline-block; }
    .info { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
    .info p { margin: 5px 0; }
    pre { background: #232f3e; color: #f5f5f5; padding: 15px; border-radius: 5px; }
  </style>
</head>
<body>
  <div class="container">
    <span class="tier">Web Tier</span>
    <h1>3-Tier Architecture Demo</h1>
    <p>This page is served from the <strong>Web Tier</strong> behind the ALB.</p>
    <div class="info">
      <p><strong>Instance ID:</strong> ${INSTANCE_ID}</p>
      <p><strong>Availability Zone:</strong> ${AZ}</p>
      <p><strong>Private IP:</strong> ${LOCAL_IP}</p>
    </div>
    <h3>Architecture</h3>
    <pre>Internet → ALB → [Web Tier] → App Tier → Database
                      ↑
                  You are here</pre>
  </div>
</body>
</html>
EOF
```

### Create Custom Page (nginx)

If you're using nginx instead of Apache:

```bash
# Same commands, different path:
cat <<EOF | sudo tee /usr/share/nginx/html/index.html
# ... same HTML content as above ...
EOF
```

### Test Load Balancing

After customizing the page on **both** web instances (with different instance IDs):

1. Open your ALB URL in a browser
2. Refresh the page multiple times
3. Watch the Instance ID and AZ change — this proves the ALB is distributing traffic

> **Tip:** If you see the same instance every time, the ALB might be using sticky sessions, or you're hitting the browser cache. Try `curl` instead:
> ```bash
> for i in {1..10}; do curl -s http://your-alb-url | grep "Instance ID"; done
> ```

---

## Glossary

| Term | Definition |
|------|-----------|
| **VPC** | Virtual Private Cloud — your own isolated network in AWS, like having your own private data center. |
| **Subnet** | A subdivision of a VPC. Each subnet lives in one Availability Zone and has a range of IP addresses. |
| **CIDR** | Classless Inter-Domain Routing — notation for IP address ranges (e.g., `10.0.0.0/16` = 65,536 addresses). |
| **Internet Gateway (IGW)** | Connects a VPC to the internet. Attached to public subnets. |
| **NAT Gateway** | Allows private subnets to reach the internet (for updates, packages) without being reachable FROM the internet. |
| **Route Table** | Rules that determine where network traffic is directed. Each subnet is associated with one route table. |
| **Security Group** | A virtual firewall for AWS resources. Controls inbound and outbound traffic with allow rules. |
| **ALB** | Application Load Balancer — distributes incoming HTTP/HTTPS traffic across multiple targets (EC2, ECS). |
| **Target Group** | A group of resources (EC2 instances, IP addresses) that an ALB routes traffic to. |
| **Listener** | A process on the ALB that checks for connection requests on a specific port and protocol. |
| **Health Check** | Periodic requests the ALB makes to targets to verify they're healthy and can receive traffic. |
| **Availability Zone (AZ)** | A physically separate data center within an AWS region. Using multiple AZs provides fault tolerance. |
| **Multi-AZ** | Deploying resources across multiple AZs for high availability. If one AZ fails, the other keeps running. |
| **EC2** | Elastic Compute Cloud — virtual servers in AWS. You choose the OS, instance type, and manage the machine. |
| **ECS** | Elastic Container Service — runs Docker containers on AWS without managing servers (with Fargate). |
| **Fargate** | Serverless compute engine for ECS. AWS manages the underlying servers; you just define containers. |
| **RDS** | Relational Database Service — managed database (MySQL, PostgreSQL, etc.) with backups, patching, and failover. |
| **AMI** | Amazon Machine Image — a template containing the OS and software for launching EC2 instances. |
| **User Data** | A bash script that runs when an EC2 instance first boots. Used to install software and configure the server. |
| **EIP** | Elastic IP — a static public IP address that you can assign to AWS resources like NAT Gateways. |
| **Terraform State** | A file (`terraform.tfstate`) that tracks which real resources Terraform manages. Never delete it. |

---

## What You Learned

- **3-tier architecture** - Separation of concerns
- **VPC design** - Public/private subnets, NAT gateway
- **Security groups** - Layered security (defense in depth)
- **Load balancing** - ALB with target groups and health checks
- **Database tier** - RDS in isolated private subnet
- **High availability** - Multi-AZ deployment
- **(Optional) Containers** - ECS/Fargate deployment

---

## Interview Talking Points

> "I built a 3-tier architecture on AWS using Terraform, including a VPC with public and private subnets, an Application Load Balancer for traffic distribution, EC2 instances for web and app tiers, and RDS MySQL for the database tier. Security groups were configured in a chain pattern where each tier only accepts traffic from the tier above it. I also implemented NAT Gateway for private subnet internet access and tested locally using LocalStack before deploying to AWS."

**Follow-up questions you can now answer:**
- "Why use private subnets for app servers?" — Defense in depth. No direct internet access reduces attack surface. Traffic is funneled through the ALB.
- "How does the ALB know which servers are healthy?" — Health checks. The ALB periodically sends HTTP requests to each target and removes unhealthy ones from rotation.
- "What happens if an AZ goes down?" — Multi-AZ deployment. The ALB routes traffic to healthy targets in the surviving AZ. RDS fails over to the standby in the other AZ.
- "How would you handle database credentials in production?" — Use AWS Secrets Manager or SSM Parameter Store instead of hardcoded defaults. Reference them with `data` sources in Terraform.

---

## Troubleshooting

<details>
<summary>"No valid credential sources found"</summary>

Terraform can't find AWS credentials.

**If using LocalStack:**
1. Make sure you copied the provider override: `cp provider_override.tf.example provider_override.tf`
2. Run `aws configure` with dummy credentials (Access Key: `test`, Secret Key: `test`)
3. Verify LocalStack is running: `docker-compose ps`

**If using real AWS:**
1. Run `aws configure` with your real credentials
2. Verify with: `aws sts get-caller-identity`

</details>

<details>
<summary>"Error creating VPC" or resources fail to create</summary>

1. Is LocalStack running? Check: `docker-compose ps`
2. Is LocalStack healthy? Check: `curl http://localhost:4566/_localstack/health`
3. Did you copy the provider override? `ls provider_override.tf`
4. Try restarting LocalStack: `docker-compose down && docker-compose up -d`
5. Re-initialize: `terraform init`

</details>

<details>
<summary>"terraform init" fails</summary>

Common causes:
1. **No internet connection** — Terraform needs to download the AWS provider
2. **Proxy issues** — Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
3. **Permission denied** — Run from a directory where you have write access
4. **Version conflict** — Delete `.terraform/` and `.terraform.lock.hcl`, then run `terraform init` again

</details>

<details>
<summary>501 error: "not included in your current license plan" (elbv2/rds)</summary>

This is **expected behavior** on LocalStack Community Edition. The `elbv2` (ALB) and `rds` services are **Pro-only** features.

**Your code is NOT broken.** The 501 means LocalStack doesn't support these services in the free tier.

**What to do:**
1. Ignore the 501 errors from `terraform apply` — they only affect ALB and RDS
2. VPC, subnets, security groups, and EC2 should still create successfully
3. Validate your ALB and RDS code with: `terraform validate` and `python run.py --verbose`
4. Your score comes from `python run.py`, which reads your code, not running infrastructure

**If you want full `terraform apply` to work locally**, you need [LocalStack Pro](https://localstack.cloud/pricing) (paid). Otherwise, deploy to real AWS (see the optional section below).

</details>

<details>
<summary>"Error: Resource already exists"</summary>

This means the resource exists in AWS but not in your Terraform state.

1. If using LocalStack, restart it: `docker-compose down && docker-compose up -d`
2. Remove the state: `rm terraform.tfstate terraform.tfstate.backup`
3. Re-apply: `terraform apply`

**Warning:** Only do this with LocalStack or test environments. Never delete state in production.

</details>

<details>
<summary>"Error acquiring the state lock"</summary>

Another Terraform process is running, or a previous run crashed without releasing the lock.

```bash
# Force unlock (only if you're sure no other process is running)
terraform force-unlock <LOCK_ID>
```

The lock ID is shown in the error message.

</details>

<details>
<summary>502 Bad Gateway when accessing the ALB URL</summary>

**If using LocalStack (most common):**

This is expected behavior. LocalStack Community Edition creates ALB resources via the API but does **not** route real HTTP traffic through them. The ALB DNS name is registered, but no actual load balancer process runs behind it.

**What to do instead:**
1. Use the web preview: visit **http://localhost:3000** to see the simulated web tier page
2. Verify your resources with: `python run.py --verify`
3. Verify with CLI: `aws --endpoint-url=http://localhost:4566 elbv2 describe-load-balancers --output table`

Your Terraform configuration is correct — the 502 is a LocalStack limitation, not a bug in your code.

**If using real AWS:**

A 502 on real AWS means the ALB can't reach healthy backend instances. Check these in order:

1. **Wait 1-2 minutes** — After `terraform apply`, EC2 instances need time to boot, run user_data (install Apache), and pass health checks (2 checks x 30s = 60s minimum)
2. **Check target health** — In AWS Console > EC2 > Target Groups > your target group > Targets tab. If targets show "unhealthy", the issue is below.
3. **Check security groups** — The web security group must allow port 80 from the ALB security group (not a CIDR block). Run:
   ```bash
   aws ec2 describe-security-groups --group-ids <web-sg-id> --query "SecurityGroups[*].IpPermissions"
   ```
4. **Check NAT Gateway** — EC2 instances are in private subnets and need NAT Gateway for internet access. Without it, `yum install httpd` in user_data fails silently and Apache never starts. Verify your NAT Gateway exists and the private route table has a route to it.
5. **Check user_data logs** — SSH into an EC2 instance and check:
   ```bash
   cat /var/log/cloud-init-output.log
   systemctl status httpd
   curl localhost
   ```

</details>

<details>
<summary>LocalStack container won't start or keeps restarting</summary>

1. Is Docker running? Check Docker Desktop or `docker ps`
2. Is port 4566 already in use? Check: `netstat -an | grep 4566`
3. Try removing old data: `docker-compose down -v && docker-compose up -d`
4. Check logs: `docker-compose logs localstack`

</details>

<details>
<summary>"python run.py" shows 0 points even after writing code</summary>

1. Make sure you **uncommented** the code (remove the `#` at the start of lines)
2. Check for syntax errors: `terraform validate`
3. Run with verbose output: `python run.py --verbose` to see which specific checks fail
4. Make sure you saved the files

</details>

---

## Next Steps

Continue your infrastructure journey:

| Next Step | What You'll Learn |
|-----------|------------------|
| **CI/CD Pipeline** | Automate Terraform deployments with GitHub Actions |
| **Monitoring Stack** | Add CloudWatch alarms, Grafana dashboards, and alerting |
| **Terraform Modules** | Refactor this code into reusable modules |
| **Kubernetes** | Deploy containers at scale with EKS |

**Recommended path:**
1. **CI/CD Pipeline** — Automate `terraform plan` on PRs and `terraform apply` on merge
2. **Monitoring** — Add CloudWatch metrics and alerts for each tier
3. **Terraform Modules** — Package your VPC, ALB, and compute tiers as reusable modules
