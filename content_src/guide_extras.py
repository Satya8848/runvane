"""Per-guide plain-language summary, best practices, common mistakes and recommendations."""

# id: (in plain words, [best practices], [common mistakes], what we recommend)
EXTRAS = {
    "linux": (
        "Linux is the operating system under almost every server, container and cloud VM. Administering it means knowing what is running, what is using resources, and how to change it safely.",
        ["Log in with SSH keys only; disable password and root login", "Run each service as its own non-root user under systemd", "Rotate logs and alert on disk and inode usage at 80%",
         "Apply security updates automatically; reboot in a planned window", "Change config in a file under version control, not by hand on the box"],
        ["Running apps as root", "Editing production config without a backup or `sshd -t` / `nginx -t` test", "Ignoring `df -i` (inodes) when the disk looks full", "Killing a process holding a deleted log instead of rotating properly"],
        "Treat servers as cattle: build them from a script (cloud-init or Ansible), keep them patched automatically, and never fix the same thing by hand twice."),
    "networking": (
        "Every request travels DNS → TCP → TLS → load balancer or proxy → app. When something is slow or failing, walk that path step by step and check each hop.",
        ["Terminate TLS at the edge with automatic renewal (Let's Encrypt / ACM)", "Put nginx or a load balancer in front of every app; never expose app ports directly",
         "Set timeouts consistently: client < proxy < upstream keep-alive", "Rate-limit login and API paths", "Keep databases in private subnets with no public IP"],
        ["Opening 0.0.0.0/0 on SSH or database ports", "Mismatched keep-alive timeouts causing random 502s", "Forgetting to forward `Host` and `X-Forwarded-*` headers", "Low DNS TTL never set before a migration"],
        "Draw the request path once for each service. When an incident happens, use it as a checklist: DNS, TLS, proxy logs, app logs, database."),
    "docker": (
        "A container image packages your app with everything it needs, so it runs the same on a laptop, in CI and in production.",
        ["Multi-stage builds; small base images pinned by version or digest", "Copy dependency files and install before copying code (better caching)", "Run as a non-root user; add a HEALTHCHECK",
         "Tag images with the git commit SHA, never deploy `latest`", "Scan images in CI and rebuild weekly for patches"],
        ["Secrets baked into image layers or `ENV`", "One giant layer with build tools left inside", "Writing data inside the container instead of a volume", "Unbounded container logs filling the disk"],
        "Start every service from a reviewed Dockerfile template, scan with Trivy in the pipeline, and set log rotation on every Docker host."),
    "kubernetes": (
        "Kubernetes runs your containers across machines and keeps them in the state you describe: how many copies, how much CPU and memory, and how to roll out changes.",
        ["Set CPU/memory requests on every container (and memory limits)", "Readiness and liveness probes on real endpoints", "At least 2 replicas + PodDisruptionBudget for anything user-facing",
         "Rolling updates with `maxUnavailable: 0`", "One namespace per team or environment with ResourceQuotas and RBAC", "Secrets from a vault via External Secrets, not plain YAML in Git"],
        ["No requests → noisy neighbours and broken HPA", "Liveness probe so strict it restarts healthy pods under load", "Using `latest` image tags", "Running everything in the `default` namespace with cluster-admin"],
        "Package apps with Helm, deploy with GitOps (Argo CD), autoscale with HPA, and watch restarts, pending pods and OOMKilled as your first three alerts."),
    "cicd": (
        "A pipeline turns every commit into a tested, scanned, versioned artifact and deploys it the same way every time, so releases become boring.",
        ["Build once, promote the same artifact through environments", "Protect main: PR reviews + required pipeline checks", "Use OIDC / workload identity instead of stored cloud keys",
         "Keep pipelines as code with shared templates", "Fail fast: lint and unit tests first, slow scans later", "Approvals and checks on production environments"],
        ["Rebuilding a different artifact for each environment", "Long-lived secrets in pipeline variables", "Deploys that need manual steps nobody documented", "No rollback path"],
        "Aim for trunk-based development, a 10-minute pipeline, automated deploy to staging, one-click (or automatic canary) promotion to production, and DORA metrics to track it."),
    "iac": (
        "Infrastructure as code means your networks, servers and databases are described in files, reviewed in pull requests, and created by a tool instead of clicks.",
        ["Remote, locked, encrypted state (S3+DynamoDB / Azure Storage / Terraform Cloud)", "Small reusable modules with pinned versions", "One root and one state per environment",
         "Plan in the PR, apply the saved plan after approval", "Scan IaC with Checkov/tfsec; detect drift on a schedule"],
        ["Local state files on a laptop", "Giant single state for everything (slow, risky)", "Console changes that drift from code", "Secrets in `.tfvars` committed to Git"],
        "Use Terraform (or Pulumi if your team prefers real code) for cloud resources, Ansible or images for what runs on machines, and apply only from pipelines."),
    "python": (
        "Python is the glue for automation: calling APIs, talking to clouds, cleaning up resources and building internal tools. Reliable scripts matter more than clever ones.",
        ["Timeouts on every network call", "Retry only transient errors, with exponential backoff and jitter", "Use the logging module; exit non-zero on failure",
         "Dry-run mode by default for anything destructive", "Pin dependencies and use a virtualenv per tool"],
        ["Bare `except:` swallowing errors", "Retrying non-idempotent writes", "Hard-coded credentials instead of the SDK's credential chain", "No pagination on cloud API calls"],
        "Write automation as small CLI tools with `--dry-run`, structured logs and tests, and run them from the pipeline or a scheduler, not from someone's laptop."),
    "gitops": (
        "Helm packages a Kubernetes app; GitOps makes Git the single source of truth, and a controller in the cluster keeps it in sync.",
        ["One values file per environment; no secrets in values", "Promote by pull request (change the image tag)", "Argo CD with auto-sync + self-heal for non-prod, manual sync or waves for prod",
         "Use `helm upgrade --atomic` in push-based setups", "Keep chart versions and app versions separate"],
        ["Editing cluster objects by hand (drift)", "Secrets committed in plain YAML", "One mega-chart for many unrelated apps"],
        "Separate app repos from an environment (deploy) repo; let CI build and bump tags, and Argo CD deploy."),
    "ansible": (
        "Ansible configures servers over SSH from YAML playbooks: packages, files, users, services and patches, safely repeatable.",
        ["Use modules (idempotent) instead of `shell` commands", "Roles per component, variables per environment", "Encrypt secrets with Ansible Vault",
         "Run with `--check --diff` first; roll changes with `serial`", "Keep inventories dynamic from the cloud"],
        ["Shell commands that change things on every run", "Patching all servers at once", "Plain-text passwords in group_vars"],
        "Bake common setup into images (Packer) and use Ansible for the rest, with rolling patch playbooks run on a schedule."),
    "aws": (
        "AWS offers building blocks for networks, compute, storage, databases and security. Good AWS design is mostly about identity, networking and choosing managed services.",
        ["AWS Organizations with separate accounts per environment", "SSO (IAM Identity Center) for people; roles for workloads; no IAM users with keys",
         "Multi-AZ for anything production", "VPC endpoints for S3/ECR to cut NAT cost", "CloudTrail, GuardDuty, Config and budgets on from day one"],
        ["Everything in one account and one AZ", "Public S3 buckets or databases", "Root account used day to day", "No tags, so nobody owns the bill"],
        "Start with a landing zone (Control Tower), managed services (RDS, EKS/ECS, ALB), Terraform for everything, and least-privilege roles per service."),
    "aws-catalog": (
        "A map of the AWS services you will meet, grouped by job, with the Azure and GCP equivalents so you can translate designs between clouds.",
        ["Prefer managed services over self-hosting when the team is small", "Pick the simplest service that meets the need (S3 before EFS, SQS before Kafka)", "Check regional availability and pricing early"],
        ["Choosing a service because it is new rather than needed", "Ignoring data-transfer costs between services and AZs"],
        "Learn the core first: IAM, VPC, EC2/ASG, ELB, S3, RDS, CloudWatch. Then EKS/ECS, SQS/SNS/EventBridge, Lambda and the security services."),
    "azure": (
        "Azure's model centres on Entra ID identities, subscriptions and resource groups, with managed identities and Key Vault for secrets.",
        ["Management groups + subscriptions per environment", "Managed identities and workload identity federation; no client secrets", "Key Vault with RBAC, private endpoints and purge protection",
         "Azure Policy for guardrails", "Private endpoints for PaaS databases and storage"],
        ["Service principals with long-lived secrets in pipelines", "Owner role handed out broadly", "Public endpoints on databases"],
        "Use Azure DevOps or GitHub with workload identity federation, AKS with Workload Identity, and Key Vault as the single source for secrets."),
    "gcp": (
        "GCP organises everything in projects under folders; IAM is granted on resources, and services like GKE Autopilot and Cloud Run remove a lot of operations work.",
        ["One project per app per environment", "Service accounts per workload; Workload Identity Federation for CI", "Cloud Run or GKE Autopilot before managing nodes"],
        ["Using the default compute service account with broad roles", "Primitive roles (Owner/Editor) everywhere"],
        "Start with Cloud Run for stateless services, Cloud SQL for databases, and Artifact Registry + Cloud Build or GitHub Actions for delivery."),
    "cloudflare": (
        "Cloudflare sits in front of your site: DNS, caching, the web application firewall and Zero Trust access, so attacks and load stop before reaching your server.",
        ["Proxied DNS with SSL/TLS Full (strict) and an origin certificate", "Firewall the origin to Cloudflare IPs only (or use a Tunnel)", "Managed WAF rules + rate limiting on login and API",
         "Cache static assets with versioned file names", "Access (Zero Trust) in front of admin tools instead of a VPN"],
        ["Flexible SSL (unencrypted to the origin)", "Origin IP still exposed and attackable directly", "Caching logged-in pages"],
        "Put every public hostname behind Cloudflare, lock the origin, and move internal tools behind Access + Tunnel."),
    "serverless": (
        "Serverless runs your code only when events arrive and scales automatically; you pay per use and manage no servers.",
        ["Make handlers idempotent; events can arrive twice", "Dead-letter queues and alerts on failures", "Keep functions small and fast; watch cold starts", "Least-privilege role per function"],
        ["Long-running or steady heavy workloads on functions (expensive)", "No timeouts or retries configured", "Huge deployment packages"],
        "Use serverless for event-driven glue, APIs with spiky traffic and scheduled jobs; use containers for steady services."),
    "observability": (
        "Observability is knowing what your system is doing from its metrics, logs and traces, and being able to jump between them during an incident.",
        ["Unified tags (service, env, version) on every metric, log and trace", "Structured JSON logs with trace IDs", "Dashboards per service with RED metrics",
         "Alert on user symptoms (errors, latency, SLO burn), not on every CPU spike", "Every alert has an owner and a runbook link"],
        ["Hundreds of noisy alerts nobody reads", "Logs indexed at full volume (huge bill)", "No deploy markers on dashboards"],
        "Define SLOs for key journeys, alert on burn rate, route pages to on-call, and keep monitors as code."),
    "monitoring": (
        "Prometheus collects metrics, Grafana shows them, Alertmanager routes alerts, and Loki or Elasticsearch stores logs: the self-hosted monitoring stack.",
        ["Use histograms for latency so you can compute p95/p99", "Keep label cardinality low (no user IDs as labels)", "Recording rules for expensive queries", "Alert rules with `for:` durations"],
        ["Graphing raw counters instead of `rate()`", "Unbounded labels exploding memory", "Alerts without runbooks"],
        "Install kube-prometheus-stack, start from community dashboards, and add your own SLO-based alerts."),
    "sre": (
        "Site reliability engineering treats reliability as a feature: measure what users feel, set a target, and spend the error budget wisely.",
        ["Pick 1–3 SLIs per critical user journey", "Set SLOs slightly below current performance", "Multi-window burn-rate alerts", "Blameless postmortems with tracked actions", "Automate toil"],
        ["SLOs of 100%", "Too many SLOs nobody reviews", "Treating every incident as someone's fault"],
        "Review error budgets weekly with product: when the budget is gone, reliability work comes first."),
    "oncall": (
        "On-call means someone is ready to respond when production breaks. Good on-call is calm, practised and fair.",
        ["Clear escalation policies and handovers", "Runbooks linked from every alert", "Mitigate first (rollback, scale), investigate later", "Communicate on a fixed cadence", "Track MTTA/MTTR and alert noise"],
        ["Paging for non-urgent issues", "One person always on call", "No postmortems after big incidents"],
        "Use PagerDuty (or similar) with weekly rotations, two levels of escalation, and a monthly review of every page."),
    "devsecops": (
        "DevSecOps builds security into every step: code, dependencies, images, infrastructure and runtime, with checks that run automatically in the pipeline.",
        ["Secret scanning and SAST on every PR", "Dependency and image scanning with severity gates", "SBOM + signed images; verify at admission",
         "OIDC / workload identity for all pipeline cloud access", "Policy as code (Kyverno/OPA, Checkov) for clusters and IaC"],
        ["Blocking every finding (teams start ignoring the tools)", "Long-lived tokens in CI variables", "Scanning once and never again after release"],
        "Gate on Critical/High with a fix available, track exceptions with expiry dates, and re-scan running images continuously."),
    "iam": (
        "Identity and access decides who and what can do what. Most breaches start with a leaked or over-powered credential.",
        ["SSO + MFA for every human", "Roles and short-lived credentials for workloads", "Least privilege, reviewed with last-used data", "Secrets in a vault, rotated automatically", "Break-glass accounts locked away with alerts"],
        ["Shared admin accounts", "Access keys older than 90 days", "Wildcard `*` permissions"],
        "Federate everything to one identity provider and remove every long-lived key you can find."),
    "patching": (
        "Patch management keeps servers, images and endpoints updated on a schedule, proves it with reports, and has a way back when a patch breaks something.",
        ["Prioritise by exploitability (KEV, EPSS) and exposure, not only CVSS", "Patch in rings: pilot → broad → critical", "Snapshots/AMIs before patching; rollback documented",
         "Rebuild container images instead of patching inside them", "Report compliance per team with SLAs"],
        ["Patching everything at once", "No test or pilot group", "Exceptions that never expire"],
        "Automate OS patching (Ivanti, AWS Patch Manager, Ansible) in maintenance windows and rebuild images weekly."),
    "architecture": (
        "Solution architecture is choosing how the pieces fit to meet the goals: availability, security, performance and cost, and explaining the trade-offs.",
        ["Start from requirements: users, SLOs, RPO/RTO, budget, compliance", "Stateless app tier, managed data services, async work in queues", "Design for failure of an AZ",
         "Write ADRs for important decisions", "Estimate cost early"],
        ["Microservices before you need them", "Single points of failure", "Designs with no numbers (traffic, latency, cost)"],
        "Use the Well-Architected pillars as a checklist and draw the design on the Runvane board for an AI review before building."),
    "data": (
        "Data systems are where most performance problems and the worst outages end. Know replication, backups, indexes, pooling, caching and queues.",
        ["Backups + point-in-time recovery, with regular restore tests", "Connection pooling sized to the database limit", "Indexes for your real queries; check plans",
         "Cache-aside with TTL jitter", "Queues for slow or bursty work"],
        ["Never testing a restore", "Every pod opening its own large pool", "Long transactions holding locks", "Schema changes that lock big tables"],
        "Use managed databases, monitor slow queries and replication lag, and run expand/contract migrations."),
    "hadr": (
        "High availability keeps you up when parts fail; disaster recovery brings you back after losing a region or your data.",
        ["Define RPO/RTO per service", "Multi-AZ by default; cross-region for critical data", "Immutable, cross-account backups", "Practise failover in game days"],
        ["Backups in the same account and region", "DR plan that was never tested", "Assuming the cloud provider does DR for you"],
        "Pick backup-restore, pilot light or warm standby per service based on RTO, and test it every quarter."),
    "finops": (
        "FinOps makes cloud cost an engineering metric: know who spends what, and use the levers that cut cost without hurting reliability.",
        ["Mandatory tags (owner, service, env)", "Budgets and anomaly alerts per team", "Right-size from real usage", "Savings Plans for baseline, Spot for burst", "Clean up idle resources automatically"],
        ["Nobody owns the bill", "NAT gateway and cross-AZ traffic surprises", "Dev environments running all weekend"],
        "Review cost weekly per team, automate shutdown of non-prod at night, and buy commitments only for steady load."),
    "bash": (
        "Bash scripts glue tools together. Good scripts fail loudly, quote everything and clean up after themselves.",
        ["`set -euo pipefail` at the top", "Quote every variable", "`trap` for cleanup", "Check inputs and print usage", "ShellCheck in CI"],
        ["Unquoted variables with spaces", "Ignoring exit codes in pipelines", "Hard-coded paths and secrets"],
        "Keep scripts short; when they grow past a page, move to Python or Ansible."),
    "git": (
        "Git records every change. A clean branching model and protected main branch keep releases predictable.",
        ["Trunk-based development with short-lived branches", "Protected main: reviews + required checks", "Small, focused commits with clear messages", "Tags for releases (SemVer)"],
        ["Long-lived feature branches", "Force-pushing shared branches", "Committing secrets"],
        "Use PRs for every change, Conventional Commits, and secret scanning on push."),
}
