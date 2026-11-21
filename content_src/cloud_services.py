# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Cloud services explained in plain words. Source for the "<cloud> services
explained" guides (run build_cloud_guides.py to regenerate the seed)."""

# (name, category, plain words, use it for, avoid when, equivalents, starter command, tip)
AWS = [
	("IAM", "Identity", "The rulebook for who can do what in your AWS account: people, apps and services.", "Roles for apps and CI, permission policies, access reviews.", "Never use the root account day to day.", "Azure: Entra ID + RBAC · GCP: Cloud IAM",
	 "aws sts get-caller-identity", "Give people SSO (IAM Identity Center) and give apps roles. Avoid IAM users with access keys."),
	("VPC", "Networking", "Your own private network inside AWS, split into subnets across data centres (AZs).", "Every workload: public subnets for load balancers, private subnets for apps and databases.", "-", "Azure: VNet · GCP: VPC (global)",
	 "aws ec2 describe-vpcs --output table", "Use 3 AZs, keep databases in private subnets, add VPC endpoints for S3/ECR to save NAT costs."),
	("EC2", "Compute", "Virtual servers you rent by the second.", "Apps that need a full server, special software, steady workloads.", "Short, spiky jobs (use Lambda) or containers you don't want to manage (use Fargate).", "Azure: Virtual Machines · GCP: Compute Engine",
	 "aws ec2 run-instances --image-id ami-xxxx --instance-type t3.small --key-name mykey", "Launch from a template with an Auto Scaling group, even for one server: it replaces itself when it fails."),
	("Auto Scaling", "Compute", "Adds or removes servers automatically based on load or schedule.", "Web tiers with changing traffic; self-healing for single servers.", "Stateful servers that keep data on local disk.", "Azure: VM Scale Sets · GCP: Managed Instance Groups",
	 "aws autoscaling describe-auto-scaling-groups", "Scale on target tracking (e.g. 60% CPU) and keep a warm minimum."),
	("ELB (ALB / NLB)", "Networking", "Load balancers that spread traffic across healthy servers or containers.", "ALB: websites and APIs (HTTP routing, TLS). NLB: very high throughput or static IPs.", "-", "Azure: Application Gateway / Load Balancer · GCP: Cloud Load Balancing",
	 "aws elbv2 describe-target-health --target-group-arn <arn>", "Health-check a real endpoint and terminate TLS on the ALB with a free ACM certificate."),
	("S3", "Storage", "Unlimited file storage over HTTP (objects in buckets).", "Backups, uploads, static websites, data lakes, logs.", "A disk for a database (use EBS) or shared file system (use EFS).", "Azure: Blob Storage · GCP: Cloud Storage",
	 "aws s3 cp backup.sql.gz s3://my-backups/ --storage-class STANDARD_IA", "Keep Block Public Access on, turn on versioning, and add lifecycle rules to cheaper tiers."),
	("EBS", "Storage", "A virtual hard disk attached to one EC2 instance.", "Boot disks and databases on EC2.", "Sharing files between servers.", "Azure: Managed Disks · GCP: Persistent Disk",
	 "aws ec2 create-snapshot --volume-id vol-xxxx --description nightly", "Use gp3, snapshot it on a schedule (Data Lifecycle Manager), encrypt by default."),
	("EFS", "Storage", "A shared network file system many servers can mount at once.", "Shared uploads or content across several app servers.", "Databases or very latency-sensitive I/O.", "Azure: Azure Files · GCP: Filestore",
	 "sudo mount -t efs fs-xxxx:/ /mnt/shared", "Prefer S3 for new apps; use EFS only when the app needs a real file system."),
	("RDS / Aurora", "Database", "Managed SQL databases (MySQL, MariaDB, PostgreSQL, SQL Server); AWS runs backups, patching and failover.", "Almost every app database.", "You need OS access or unsupported extensions.", "Azure: Azure Database for MySQL/PostgreSQL, Azure SQL · GCP: Cloud SQL, AlloyDB",
	 "aws rds describe-db-instances --query 'DBInstances[].[DBInstanceIdentifier,MultiAZ]'", "Turn on Multi-AZ for production, automated backups with PITR, and connect through RDS Proxy if you have many app instances."),
	("DynamoDB", "Database", "A serverless key-value database that scales to huge traffic with single-digit-millisecond reads.", "Sessions, carts, user profiles, event data with known access patterns.", "Ad-hoc queries and joins (use a SQL database).", "Azure: Cosmos DB · GCP: Firestore / Bigtable",
	 "aws dynamodb describe-table --table-name orders", "Design the table from your access patterns first; use on-demand capacity to start."),
	("ElastiCache", "Database", "Managed Redis or Memcached in memory.", "Caching, sessions, rate limits, queues.", "Your only copy of important data.", "Azure: Azure Cache for Redis · GCP: Memorystore",
	 "redis-cli -h <endpoint> INFO stats", "Watch the cache hit ratio and add replicas for failover."),
	("Lambda", "Serverless", "Runs your function when an event happens; you pay only while it runs.", "APIs with spiky traffic, file processing, scheduled jobs, glue between services.", "Long or steady heavy workloads (cheaper on containers).", "Azure: Functions · GCP: Cloud Functions / Cloud Run functions",
	 "aws lambda invoke --function-name resize-image out.json", "Make handlers idempotent and add a dead-letter queue."),
	("ECS / Fargate", "Containers", "AWS's own container orchestrator; Fargate runs containers without you managing servers.", "Running containers simply without Kubernetes.", "You need Kubernetes features or portability.", "Azure: Container Apps · GCP: Cloud Run",
	 "aws ecs list-services --cluster prod", "Start with Fargate; move to EC2 capacity only to save cost at scale."),
	("EKS", "Containers", "Managed Kubernetes: AWS runs the control plane, you run workloads.", "Teams already using Kubernetes; many services; portability.", "A few simple services (ECS/Fargate is simpler).", "Azure: AKS · GCP: GKE",
	 "aws eks update-kubeconfig --name platform --region us-east-2", "Use managed node groups or Karpenter, Pod Identity for AWS access, and upgrade one minor version at a time."),
	("ECR", "Containers", "A private registry for your container images.", "Storing images built by CI.", "-", "Azure: ACR · GCP: Artifact Registry",
	 "aws ecr describe-images --repository-name web", "Turn on scan-on-push and lifecycle rules to delete old images."),
	("Route 53", "Networking", "AWS's DNS service, with health checks and failover routing.", "Domains, DNS records, failover between regions.", "-", "Azure: Azure DNS / Traffic Manager · GCP: Cloud DNS",
	 "aws route53 list-hosted-zones", "Use alias records for AWS resources and lower TTLs before migrations."),
	("CloudFront", "Networking", "A CDN that caches your content close to users worldwide.", "Static assets, websites, APIs that benefit from edge caching.", "-", "Azure: Front Door / CDN · GCP: Cloud CDN",
	 "aws cloudfront create-invalidation --distribution-id EXXXX --paths '/*'", "Use versioned file names so you rarely need invalidations; attach AWS WAF."),
	("SQS", "Integration", "A message queue: one part of your system leaves work, another picks it up.", "Background jobs, smoothing traffic spikes, decoupling services.", "Fan-out to many subscribers (add SNS) or ordered event replay (use Kinesis/MSK).", "Azure: Service Bus / Storage Queues · GCP: Pub/Sub",
	 "aws sqs get-queue-attributes --queue-url <url> --attribute-names ApproximateNumberOfMessages", "Add a dead-letter queue and alarm on its depth."),
	("SNS", "Integration", "Publish once, deliver to many subscribers (queues, functions, email, SMS).", "Fan-out events and alerts.", "-", "Azure: Event Grid · GCP: Pub/Sub",
	 "aws sns publish --topic-arn <arn> --message 'deploy finished'", "Pair SNS with SQS queues per consumer for durability."),
	("EventBridge", "Integration", "An event bus that routes events by rules, including schedules and SaaS events.", "Event-driven architectures, cron jobs, reacting to AWS changes.", "-", "Azure: Event Grid · GCP: Eventarc",
	 "aws events list-rules", "Keep event schemas documented and versioned."),
	("CloudWatch", "Operations", "Metrics, logs, dashboards and alarms for everything in AWS.", "Monitoring and alerting on AWS resources and apps.", "-", "Azure: Azure Monitor · GCP: Cloud Monitoring/Logging",
	 "aws logs tail /aws/lambda/resize-image --follow", "Set log retention (default is forever) and alarm on symptoms like 5xx and latency."),
	("CloudTrail", "Security", "A record of every API call made in your account: who did what, when.", "Audits, investigations, compliance.", "-", "Azure: Activity Log · GCP: Cloud Audit Logs",
	 "aws cloudtrail lookup-events --max-results 20", "Enable an organization trail to a locked S3 bucket in a separate account."),
	("KMS", "Security", "Creates and controls encryption keys.", "Encrypting S3, EBS, RDS, secrets with keys you control.", "-", "Azure: Key Vault keys · GCP: Cloud KMS",
	 "aws kms list-aliases", "Use customer-managed keys for sensitive data and restrict who can use them."),
	("Secrets Manager", "Security", "Stores passwords and API keys and can rotate them automatically.", "Database credentials, API tokens for apps.", "Simple non-secret config (use Parameter Store).", "Azure: Key Vault · GCP: Secret Manager",
	 "aws secretsmanager get-secret-value --secret-id prod/db --query SecretString", "Read secrets at runtime via roles, rotate automatically, never copy them into code."),
	("WAF & Shield", "Security", "A web firewall that blocks common attacks, plus DDoS protection.", "Public websites and APIs.", "-", "Azure: Front Door WAF / DDoS Protection · GCP: Cloud Armor",
	 "aws wafv2 list-web-acls --scope REGIONAL", "Start with AWS managed rule groups in count mode, then block."),
	("GuardDuty & Security Hub", "Security", "Threat detection from logs, and one place for all security findings.", "Every account, from day one.", "-", "Azure: Defender for Cloud · GCP: Security Command Center",
	 "aws guardduty list-detectors", "Enable organization-wide and route high-severity findings to on-call."),
	("Systems Manager", "Operations", "Manage servers without SSH: shell sessions, patching, inventory, parameters.", "Patching fleets, running commands, storing config.", "-", "Azure: Azure Arc / Update Manager · GCP: OS Config / VM Manager",
	 "aws ssm start-session --target i-0abc123", "Close port 22 and use Session Manager; patch with Patch Manager in maintenance windows."),
	("CloudFormation / CDK", "IaC", "AWS's own infrastructure-as-code (YAML/JSON templates or code with CDK).", "AWS-only teams that want native IaC.", "Multi-cloud estates (Terraform).", "Azure: Bicep/ARM · GCP: Infrastructure Manager",
	 "aws cloudformation deploy --template-file stack.yml --stack-name app", "Use change sets to review before deploying."),
	("Cost Explorer & Budgets", "Cost", "See where money goes and get alerts before you overspend.", "Every account.", "-", "Azure: Cost Management · GCP: Billing reports & budgets",
	 "aws ce get-cost-and-usage --time-period Start=2026-11-01,End=2026-11-21 --granularity MONTHLY --metrics UnblendedCost", "Tag everything and set a budget per team with anomaly detection."),
]

AZURE = [
	("Entra ID (Azure AD)", "Identity", "Azure's identity system for users, groups, apps and managed identities.", "Sign-in, SSO, app registrations, conditional access.", "-", "AWS: IAM Identity Center + IAM · GCP: Cloud Identity + IAM",
	 "az ad signed-in-user show", "Require MFA, use groups for access and conditional access for admins."),
	("Azure RBAC", "Identity", "Who can do what on which subscription, resource group or resource.", "Granting least-privilege access.", "-", "AWS: IAM policies · GCP: IAM roles",
	 "az role assignment list --assignee <user-or-sp> -o table", "Assign roles to groups at resource-group scope; avoid Owner."),
	("Managed Identity", "Identity", "An identity Azure creates for your app, so it can reach other services with no secret.", "Apps on VMs, App Service, Functions, AKS reaching Key Vault, Storage, SQL.", "-", "AWS: IAM roles for EC2/Lambda · GCP: service accounts",
	 "az webapp identity assign -g rg -n myapp", "Prefer user-assigned identities you can reuse and audit."),
	("Virtual Network (VNet)", "Networking", "Your private network in Azure with subnets and security groups (NSGs).", "Every workload.", "-", "AWS: VPC · GCP: VPC",
	 "az network vnet list -o table", "Plan address space up front; use Private Endpoints for PaaS services."),
	("Virtual Machines & Scale Sets", "Compute", "Rentable servers; scale sets add/remove them automatically.", "Lift-and-shift apps, special software, steady workloads.", "Simple web apps (App Service) or containers (Container Apps).", "AWS: EC2 + ASG · GCP: Compute Engine + MIGs",
	 "az vm list -o table", "Use scale sets even for small fleets and Azure Update Manager for patching."),
	("App Service", "Compute", "Hosts web apps and APIs without managing servers (code or containers).", "Websites and APIs in .NET, Node, Python, Java, PHP.", "Complex microservices (AKS/Container Apps).", "AWS: Elastic Beanstalk / App Runner · GCP: App Engine / Cloud Run",
	 "az webapp up --name myapp --runtime 'PYTHON:3.12'", "Use deployment slots for zero-downtime swaps."),
	("Azure Functions", "Serverless", "Event-driven functions billed per execution.", "Triggers from queues, timers, HTTP, storage.", "Long-running steady work.", "AWS: Lambda · GCP: Cloud Functions",
	 "func azure functionapp publish myfuncapp", "Use the Flex Consumption or Premium plan to avoid cold starts on critical paths."),
	("AKS", "Containers", "Managed Kubernetes on Azure.", "Many containerised services, teams using Kubernetes.", "A few simple services (Container Apps).", "AWS: EKS · GCP: GKE",
	 "az aks get-credentials -g rg -n aks-prod", "Enable Workload Identity, Azure Policy and autoscaler; upgrade regularly."),
	("Container Apps", "Containers", "Run containers serverlessly with autoscaling (including to zero), built on Kubernetes.", "APIs, workers and microservices without managing Kubernetes.", "You need full Kubernetes control.", "AWS: ECS Fargate / App Runner · GCP: Cloud Run",
	 "az containerapp up --name api --source .", "Use revisions with traffic splitting for safe releases."),
	("ACR", "Containers", "Private container registry.", "Storing images from CI.", "-", "AWS: ECR · GCP: Artifact Registry",
	 "az acr repository list --name myacr -o table", "Enable Defender scanning and pull with managed identity (no admin user)."),
	("Blob Storage", "Storage", "Object storage for files of any size.", "Backups, uploads, data lakes, static sites.", "Shared file systems (Azure Files).", "AWS: S3 · GCP: Cloud Storage",
	 "az storage blob upload --account-name st --container-name backups --file db.sql.gz --name db.sql.gz --auth-mode login", "Disable public access, use lifecycle management to Cool/Archive tiers."),
	("Azure SQL / Database for MySQL & PostgreSQL", "Database", "Managed relational databases with backups, patching and HA.", "Most app databases.", "-", "AWS: RDS/Aurora · GCP: Cloud SQL",
	 "az mysql flexible-server list -o table", "Zone-redundant HA for production and Private Endpoint access only."),
	("Cosmos DB", "Database", "Globally distributed NoSQL database with several APIs.", "Low-latency global apps, flexible documents.", "Relational data with joins.", "AWS: DynamoDB · GCP: Firestore",
	 "az cosmosdb list -o table", "Choose the partition key carefully; it decides scale and cost."),
	("Azure Cache for Redis", "Database", "Managed Redis.", "Caching and sessions.", "-", "AWS: ElastiCache · GCP: Memorystore",
	 "az redis list -o table", "Use Standard tier or higher for production (replica)."),
	("Service Bus", "Integration", "Enterprise message broker with queues and topics.", "Reliable messaging between services, ordered processing.", "Simple high-volume events (Event Grid/Event Hubs).", "AWS: SQS + SNS · GCP: Pub/Sub",
	 "az servicebus queue list -g rg --namespace-name sb -o table", "Use dead-letter queues and sessions for ordering."),
	("Event Grid & Event Hubs", "Integration", "Event Grid routes events; Event Hubs ingests huge event streams (Kafka-compatible).", "Reacting to resource events; telemetry and log streams.", "-", "AWS: EventBridge / Kinesis · GCP: Eventarc / Pub/Sub",
	 "az eventhubs namespace list -o table", "Pick Event Hubs for streams, Event Grid for discrete events."),
	("Front Door & Application Gateway", "Networking", "Front Door: global entry point with CDN and WAF. Application Gateway: regional L7 load balancer with WAF.", "Public web apps and APIs.", "-", "AWS: CloudFront + ALB · GCP: Cloud Load Balancing + Cloud CDN",
	 "az network front-door list -o table", "Put WAF in prevention mode after a learning period."),
	("Key Vault", "Security", "Stores secrets, keys and certificates with access control and audit.", "All app and pipeline secrets.", "-", "AWS: Secrets Manager + KMS · GCP: Secret Manager + KMS",
	 "az keyvault secret show --vault-name kv-prod -n db-password --query value", "RBAC mode, private endpoint, soft-delete and purge protection on."),
	("Azure Monitor & Log Analytics", "Operations", "Metrics, logs (KQL queries), alerts and Application Insights for apps.", "Monitoring everything in Azure.", "-", "AWS: CloudWatch · GCP: Cloud Monitoring/Logging",
	 "az monitor metrics list --resource <id> --metric 'Percentage CPU'", "Set data retention and daily caps to control cost."),
	("Defender for Cloud & Azure Policy", "Security", "Security posture and threat protection; Policy enforces rules on resources.", "Every subscription.", "-", "AWS: Security Hub + Config · GCP: Security Command Center + Org Policy",
	 "az policy assignment list -o table", "Assign the Microsoft cloud security benchmark initiative from day one."),
	("Azure DevOps", "Delivery", "Repos, YAML pipelines, boards, artifacts and test plans.", "End-to-end delivery for Azure-centric teams.", "-", "AWS: CodePipeline · GCP: Cloud Build · Also: GitHub Actions",
	 "az pipelines run --name app-ci", "Use workload identity federation for service connections and approvals on environments."),
	("Bicep", "IaC", "Azure's native infrastructure-as-code language.", "Azure-only teams.", "Multi-cloud (Terraform).", "AWS: CloudFormation/CDK · GCP: Infrastructure Manager",
	 "az deployment group create -g rg -f main.bicep", "Run what-if before every deployment."),
]

GCP = [
	("Cloud IAM", "Identity", "Who can do what on organisation, folders, projects and resources.", "Granting access to people and service accounts.", "-", "AWS: IAM · Azure: Entra ID + RBAC",
	 "gcloud projects get-iam-policy my-project", "Use predefined roles at the lowest scope; avoid Owner/Editor."),
	("Service Accounts & Workload Identity Federation", "Identity", "Identities for apps; federation lets CI and other clouds use them without keys.", "Apps on GKE, Cloud Run; GitHub Actions to GCP.", "-", "AWS: IAM roles + OIDC · Azure: managed identity + federation",
	 "gcloud iam service-accounts list", "Never download service account keys; use federation."),
	("VPC", "Networking", "A global private network with regional subnets.", "Every workload.", "-", "AWS: VPC · Azure: VNet",
	 "gcloud compute networks subnets list", "Use Shared VPC for many projects; Cloud NAT for outbound."),
	("Compute Engine", "Compute", "Virtual machines.", "Full-server workloads.", "Stateless web services (Cloud Run).", "AWS: EC2 · Azure: Virtual Machines",
	 "gcloud compute instances list", "Use managed instance groups with autohealing."),
	("Cloud Run", "Containers", "Runs any container, scales from zero, pay per request.", "APIs, web apps, workers, jobs.", "Very long-lived connections or GPUs (check limits).", "AWS: App Runner / Fargate · Azure: Container Apps",
	 "gcloud run deploy api --source . --region asia-south1", "Set min instances for latency-sensitive services."),
	("GKE", "Containers", "Managed Kubernetes; Autopilot manages nodes for you.", "Many services, Kubernetes teams.", "A few simple services (Cloud Run).", "AWS: EKS · Azure: AKS",
	 "gcloud container clusters get-credentials platform --region asia-south1", "Start with Autopilot; enable Workload Identity."),
	("Cloud Functions", "Serverless", "Event-driven functions.", "Glue, triggers from Pub/Sub and Storage.", "Steady heavy load.", "AWS: Lambda · Azure: Functions",
	 "gcloud functions deploy resize --gen2 --runtime python312 --trigger-http", "Use 2nd gen (built on Cloud Run)."),
	("Cloud Storage", "Storage", "Object storage.", "Backups, uploads, data lakes.", "-", "AWS: S3 · Azure: Blob Storage",
	 "gcloud storage cp db.sql.gz gs://my-backups/", "Uniform bucket-level access and lifecycle rules."),
	("Cloud SQL & AlloyDB", "Database", "Managed MySQL, PostgreSQL, SQL Server; AlloyDB for high-performance PostgreSQL.", "App databases.", "-", "AWS: RDS/Aurora · Azure: Database for MySQL/PostgreSQL",
	 "gcloud sql instances list", "High availability on, private IP, automated backups with PITR."),
	("Firestore, Bigtable & Spanner", "Database", "Firestore: documents; Bigtable: huge wide-column; Spanner: global relational.", "Mobile/web apps; time-series; global consistency.", "-", "AWS: DynamoDB · Azure: Cosmos DB",
	 "gcloud firestore databases list", "Pick by access pattern and scale; Spanner only when you truly need global SQL."),
	("Memorystore", "Database", "Managed Redis and Memcached.", "Caching.", "-", "AWS: ElastiCache · Azure: Cache for Redis",
	 "gcloud redis instances list --region asia-south1", "Standard tier for failover."),
	("Pub/Sub", "Integration", "Global messaging for events and streams.", "Decoupling services, event ingestion.", "-", "AWS: SNS+SQS / Kinesis · Azure: Service Bus / Event Hubs",
	 "gcloud pubsub topics publish orders --message '{\"id\":1}'", "Dead-letter topics and idempotent subscribers."),
	("Cloud Load Balancing & Cloud CDN", "Networking", "One global anycast IP load balancer with optional CDN.", "Public apps worldwide.", "-", "AWS: ELB + CloudFront · Azure: Front Door",
	 "gcloud compute forwarding-rules list", "Attach Cloud Armor for WAF and DDoS protection."),
	("Cloud Armor", "Security", "WAF and DDoS protection at the edge.", "Public apps.", "-", "AWS: WAF/Shield · Azure: Front Door WAF",
	 "gcloud compute security-policies list", "Start with preconfigured OWASP rules in preview mode."),
	("Secret Manager & Cloud KMS", "Security", "Stores secrets; manages encryption keys.", "All app secrets and keys.", "-", "AWS: Secrets Manager + KMS · Azure: Key Vault",
	 "gcloud secrets versions access latest --secret db-password", "Grant secretAccessor per secret to specific service accounts."),
	("Cloud Monitoring & Logging", "Operations", "Metrics, dashboards, alerting and logs for GCP and apps.", "Everything you run.", "-", "AWS: CloudWatch · Azure: Monitor",
	 "gcloud logging read 'severity>=ERROR' --limit 20", "Use log-based metrics and exclusion filters to control cost."),
	("Artifact Registry & Cloud Build", "Delivery", "Registry for images/packages; managed CI builds.", "Building and storing artifacts.", "-", "AWS: ECR + CodeBuild · Azure: ACR + Pipelines",
	 "gcloud builds submit --tag asia-south1-docker.pkg.dev/proj/apps/web:abc1234", "Turn on vulnerability scanning in Artifact Registry."),
	("BigQuery", "Analytics", "Serverless data warehouse: SQL over terabytes in seconds.", "Analytics, reporting, log analysis.", "Transactional app databases.", "AWS: Redshift/Athena · Azure: Synapse/Fabric",
	 "bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `proj.ds.events`'", "Partition and cluster tables; set cost controls on queries."),
]

OTHERS = [
	("DigitalOcean", "Simple cloud", "Easy VMs (Droplets), managed Kubernetes, databases and App Platform with simple pricing.", "Startups, side projects, small teams.", "Deep enterprise compliance or huge managed-service catalogue.", "Like a simpler AWS/Azure/GCP",
	 "doctl compute droplet list", "Use managed databases and backups; DO's pricing is predictable."),
	("Hetzner Cloud", "Simple cloud", "Very low-cost VMs and dedicated servers in Europe and the US.", "Cost-sensitive workloads, self-hosted stacks, CI runners.", "You need many managed services.", "Like EC2 with fewer services",
	 "hcloud server list", "Automate with Terraform and handle backups/HA yourself."),
	("Oracle Cloud (OCI)", "Hyperscaler", "Full cloud with a generous Always Free tier (Arm VMs) and strong database offerings.", "Free-tier labs, Oracle workloads.", "Teams without OCI skills for production.", "AWS/Azure/GCP alternative",
	 "oci compute instance list --compartment-id <ocid>", "Great for free learning labs on Arm VMs."),
	("Cloudflare", "Edge", "DNS, CDN, WAF, Zero Trust, Workers (edge functions), R2 storage with no egress fees.", "Putting any site behind a fast, protected edge.", "-", "AWS CloudFront+WAF · Azure Front Door · GCP Cloud CDN+Armor",
	 "wrangler deploy", "Proxy all public hostnames and lock the origin to Cloudflare."),
]


def card(service):
	"""
	Markdown for one service card.

	Parameters:
		service (tuple, required): Service data.

	Returns:
		str: Markdown.
	"""
	name, category, plain, use, avoid, equivalents, command, tip = service
	lines = [f"### {name}", f"*{category}*", "", f"**In plain words:** {plain}", "",
		"| | |", "| --- | --- |", f"| ✅ Use it for | {use} |"]
	if avoid and avoid != "-":
		lines.append(f"| ⛔ Not for | {avoid} |")
	lines += [f"| 🔁 Same idea on other clouds | {equivalents} |", "", "```bash", command, "```", f"💡 **Best practice:** {tip}", ""]
	return "\n".join(lines)


def guide(slug, title, intro, services):
	"""
	One guide made of service cards grouped by category.

	Parameters:
		slug (str, required): Guide slug.
		title (str, required): Title.
		intro (str, required): Plain-words intro.
		services (list, required): Services.

	Returns:
		dict: Guide record.
	"""
	order = []
	for s in services:
		if s[1] not in order:
			order.append(s[1])
	body = ["**Jump to:** " + " · ".join(order), ""]
	for category in order:
		body.append(f"## {category}\n")
		body += [card(s) for s in services if s[1] == category]
	return {"slug": slug, "title": title, "category": "Cloud services explained", "intro": intro, "body": "\n".join(body), "diagram": ""}


def comparison():
	"""
	The side-by-side "which service should I use" guide.

	Returns:
		dict: Guide record.
	"""
	rows = [
		("Virtual servers", "EC2", "Virtual Machines", "Compute Engine"),
		("Autoscaling servers", "Auto Scaling groups", "VM Scale Sets", "Managed Instance Groups"),
		("Run a container, no servers", "Fargate / App Runner", "Container Apps", "Cloud Run"),
		("Managed Kubernetes", "EKS", "AKS", "GKE"),
		("Functions", "Lambda", "Functions", "Cloud Functions"),
		("Web app hosting", "Elastic Beanstalk / App Runner", "App Service", "App Engine / Cloud Run"),
		("Object storage", "S3", "Blob Storage", "Cloud Storage"),
		("Block disks", "EBS", "Managed Disks", "Persistent Disk"),
		("Shared files", "EFS / FSx", "Azure Files", "Filestore"),
		("Managed SQL", "RDS / Aurora", "Azure SQL / Database for MySQL & PostgreSQL", "Cloud SQL / AlloyDB"),
		("NoSQL", "DynamoDB", "Cosmos DB", "Firestore / Bigtable"),
		("Redis cache", "ElastiCache", "Azure Cache for Redis", "Memorystore"),
		("Queue", "SQS", "Service Bus / Storage Queues", "Pub/Sub"),
		("Pub/sub & events", "SNS / EventBridge", "Event Grid", "Pub/Sub / Eventarc"),
		("Streaming", "Kinesis / MSK", "Event Hubs", "Pub/Sub / Managed Kafka"),
		("Private network", "VPC", "VNet", "VPC"),
		("Load balancer", "ALB / NLB", "Application Gateway / Load Balancer", "Cloud Load Balancing"),
		("CDN", "CloudFront", "Front Door / CDN", "Cloud CDN"),
		("DNS", "Route 53", "Azure DNS", "Cloud DNS"),
		("WAF", "AWS WAF", "Front Door WAF", "Cloud Armor"),
		("Identity for people", "IAM Identity Center", "Entra ID", "Cloud Identity"),
		("Identity for apps", "IAM roles / Pod Identity", "Managed identity / Workload Identity", "Service accounts / Workload Identity"),
		("Secrets", "Secrets Manager", "Key Vault", "Secret Manager"),
		("Encryption keys", "KMS", "Key Vault keys", "Cloud KMS"),
		("Monitoring & logs", "CloudWatch", "Azure Monitor / Log Analytics", "Cloud Monitoring / Logging"),
		("Audit log", "CloudTrail", "Activity Log", "Cloud Audit Logs"),
		("Threat detection", "GuardDuty / Security Hub", "Defender for Cloud", "Security Command Center"),
		("Container registry", "ECR", "ACR", "Artifact Registry"),
		("CI/CD", "CodePipeline / CodeBuild", "Azure DevOps Pipelines", "Cloud Build / Cloud Deploy"),
		("Native IaC", "CloudFormation / CDK", "Bicep / ARM", "Infrastructure Manager"),
		("Data warehouse", "Redshift / Athena", "Synapse / Fabric", "BigQuery"),
		("Cost tools", "Cost Explorer / Budgets", "Cost Management", "Billing reports / Budgets"),
	]
	body = ["Find the job you need on the left, then read across.", "",
		"| I need… | AWS | Azure | Google Cloud |", "| --- | --- | --- | --- |"]
	body += [f"| **{a}** | {b} | {c} | {d} |" for a, b, c, d in rows]
	body += ["", "## How to choose a cloud", "",
		"| If your situation is… | Usually pick | Why |", "| --- | --- | --- |",
		"| Company already on Microsoft 365 / .NET / Windows | **Azure** | Entra ID, licensing and tooling fit |",
		"| Widest service choice, biggest hiring pool | **AWS** | Largest ecosystem and community |",
		"| Data/analytics or simplest serverless containers | **Google Cloud** | BigQuery and Cloud Run |",
		"| Small team, simple apps, predictable bill | **DigitalOcean / Hetzner** | Simple pricing, fewer moving parts |",
		"| Learning or free labs | **Oracle Cloud free tier / AWS & GCP free tiers** | Free compute to practise on |",
		"", "## Other clouds and edge", ""] + [card(s) for s in OTHERS]
	body += ["💡 **Best practice:** pick one main cloud, learn its identity and networking deeply, and use Terraform so your skills transfer."]
	return {"slug": "cloud-comparison", "title": "Which cloud service should I use?", "category": "Cloud services explained",
		"intro": "Every big cloud has the same building blocks with different names. This map shows the equivalent service on AWS, Azure and Google Cloud for each job.",
		"body": "\n".join(body), "diagram": ""}


GUIDES = [
	comparison(),
	guide("aws-services", "AWS services explained", "AWS has 200+ services, but most systems use the same 25 or so. Each card below says what the service is, when to use it, the same idea on other clouds, a first command and one best practice.", AWS),
	guide("azure-services", "Azure services explained", "The Azure services you will meet most, explained simply: identity first (Entra ID, managed identities), then compute, data, messaging, security and delivery.", AZURE),
	guide("gcp-services", "Google Cloud services explained", "The Google Cloud services you will meet most, explained simply, from IAM and VPC to Cloud Run, GKE, BigQuery and the security tools.", GCP),
]
