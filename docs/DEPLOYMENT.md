# Deployment Notes

This is a seed deployment checklist for the production hardening phase.

## Required Secrets And Environment

Production deployments must provide these values from a secret manager or
deployment environment, never from committed files:

- `DATABASE_URL`: PostgreSQL async SQLAlchemy URL. Use a least-privileged app
  role and TLS where the provider supports it.
- `REDIS_URL`: Redis URL. Use authentication/TLS in managed or shared networks.
- `KAFKA_BROKERS`: Kafka broker list for click-event publishing.
- `JWT_SECRET`: at least 32 random bytes, unique per environment.
- `JWT_ALGORITHM`: keep one of `HS256`, `HS384`, or `HS512`.
- `GOOGLE_SAFE_BROWSING_API_KEY`: optional but recommended for malicious URL
  detection.
- `CORS_ALLOWED_ORIGINS`: comma-separated production frontend origins. Do not
  use `*`.

Operational tuning:

- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT_SECONDS`
- `REDIS_MAX_CONNECTIONS`
- `RATE_LIMIT_*`
- `REDIRECT_PASSWORD_ATTEMPT_LIMIT`
- `REDIRECT_PASSWORD_ATTEMPT_WINDOW_SECONDS`

Security-sensitive defaults:

- `APP_ENV=production` enables HSTS headers.
- `ALLOW_PRIVATE_REDIRECT_URLS=false` should remain false in production.
- `.env.example` is for local development shape only; production values must be
  injected securely.

## Dependency Audit Commands

Frontend:

```text
cd apps/web
npm audit --audit-level=high
```

Python direct dependency audit until Poetry lock files are introduced:

```text
pip-audit -r <pinned-project-requirements.txt> --no-deps
```

Full lock-file audits should replace the temporary pinned-requirements approach
once Phase 13 adds reproducible lock files for the API and worker.

## Production-Like Docker Compose

The production simulation stack is defined in
`infra/docker-compose.prod.yml`. It builds three application images:

- `api`: FastAPI app, migrations run at container startup, served by Uvicorn.
- `analytics-worker`: Kafka click-event consumer.
- `web`: Vite static assets served by nginx. nginx also proxies `/api` and `/r`
  to the API container so the browser can use same-origin requests locally.

Internal service communication uses Docker DNS names: `postgres`, `redis`,
`kafka`, and `api`. Persistent Postgres, Redis, and Kafka data are stored in
named Docker volumes.

Create a local production-simulation env file from the placeholder template:

```text
copy .env.example .env
```

Replace every placeholder secret before starting the stack. At minimum,
`POSTGRES_PASSWORD`, `JWT_SECRET`, and `IP_HASH_SECRET` must be strong random
values. The checked-in `.env.example` intentionally contains placeholders only;
the real `.env` file is gitignored.

Start the full stack from the repository root. Because the compose file lives in
`infra/`, pass the root `.env` explicitly for variable interpolation:

```text
docker-compose --env-file .env -f infra/docker-compose.prod.yml up --build
```

With newer Docker Compose installations, the equivalent command is:

```text
docker compose --env-file .env -f infra/docker-compose.prod.yml up --build
```

Verify health checks:

```text
docker-compose --env-file .env -f infra/docker-compose.prod.yml ps
```

Expected result: `postgres`, `redis`, `kafka`, `api`, and `web` report healthy.
The analytics worker has an image-level import health check and should stay
running after Kafka is healthy.

Smoke checks:

```text
curl http://localhost:8080/health
curl http://localhost:8080/api/health
```

Then verify the application path from the browser at `http://localhost:8080`:
register, log in, create a link, open its `/r/{short_code}` redirect, and view
the analytics page after the worker consumes click events.

## AWS Deployment Architecture

The deployable AWS path is intentionally cost-conscious for a solo developer or
portfolio project:

- Compute: ECS Fargate services for `api`, `analytics-worker`, `web`, and a
  single lightweight Kafka-compatible broker task.
- Database: RDS PostgreSQL Single-AZ `db.t4g.micro`.
- Cache: ElastiCache Redis Single-AZ `cache.t4g.micro`.
- Routing: public Application Load Balancer. `/api/*`, `/r/*`, and `/health`
  route to the API service; everything else routes to the web service.
- Networking: one VPC, two public subnets for the ALB/ECS tasks, two private
  subnets for RDS/Redis. ECS tasks receive public IPs to avoid NAT Gateway cost,
  but their security group only accepts inbound traffic from the ALB or other ECS
  tasks.
- Secrets: AWS Secrets Manager. Terraform references secret ARNs and JSON keys;
  secret values are not stored in `.tfvars`.

The main tradeoff is cost versus isolation. The minimal path avoids NAT Gateway
and MSK, which are often disproportionate for a portfolio app. A larger
production architecture should move ECS tasks into private subnets behind NAT
Gateways or VPC endpoints, use Multi-AZ RDS, Redis replication/failover, MSK or
a managed queue, HTTPS with ACM, WAF, autoscaling, and centralized observability.

### Estimated Monthly Cost

Rough low-traffic estimate for `us-east-1`, assuming one task per service and
minimal storage:

- ECS Fargate: roughly `$55-$75` for API, web, worker, and broker tasks sized at
  `0.25-0.5 vCPU` / `0.5-1 GB` running continuously.
- RDS `db.t4g.micro`: roughly `$12-$18`, plus storage and backups.
- ElastiCache `cache.t4g.micro`: roughly `$12-$18`.
- ALB: roughly `$18-$25` before data transfer, depending on LCU usage.
- CloudWatch logs, data transfer, Secrets Manager, and storage: roughly `$5-$15`
  for low traffic.

Expected total: approximately `$100-$150/month`. Prices vary by region, traffic,
and AWS pricing changes. Check the official pricing pages before leaving the
stack running: [Fargate pricing](https://aws.amazon.com/fargate/pricing/),
[RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/),
[ElastiCache pricing](https://aws.amazon.com/elasticache/pricing/), and
[Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/).

For an even cheaper demo, run the production Docker Compose stack on one small
EC2 instance and accept the operational tradeoff. For interview discussion,
describe the FAANG-scale version: multi-account AWS, private ECS/EKS workloads,
Multi-AZ RDS or Aurora, read replicas, MSK, CloudFront, WAF, autoscaling,
blue/green deploys, SLO dashboards, and disaster recovery runbooks.

## AWS Terraform Setup

Terraform lives in `infra/terraform`.

Prerequisites:

- AWS CLI authenticated to the target account.
- Terraform `>= 1.7`.
- GHCR images published by the CD workflow.
- A Route 53/ACM HTTPS setup is recommended later; the current minimal stack is
  HTTP-only to keep Phase 15 small.

Create a non-secret Terraform variables file:

```text
copy infra\terraform\terraform.tfvars.example infra\terraform\terraform.tfvars
```

Edit `terraform.tfvars` with your AWS region, lowercase GitHub owner, and app
secret ARN. Do not put secret values in this file.

Create the app secret container in Secrets Manager. Use temporary values for the
first infrastructure apply:

```text
aws secretsmanager create-secret ^
  --name devlink-prod/app-secrets ^
  --secret-string "{\"DATABASE_URL\":\"postgresql+asyncpg://placeholder:placeholder@localhost:5432/devlink\",\"JWT_SECRET\":\"replace-with-at-least-32-random-bytes\",\"IP_HASH_SECRET\":\"replace-with-a-random-privacy-secret\"}"
```

Copy the returned ARN into `terraform.tfvars`.

First apply, with app services scaled to zero while RDS is being created:

```text
cd infra/terraform
terraform init
terraform apply ^
  -var api_desired_count=0 ^
  -var worker_desired_count=0 ^
  -var web_desired_count=0
```

Fetch the RDS endpoint and AWS-managed master password:

```text
terraform output rds_endpoint
terraform output -raw rds_master_user_secret_arn
aws secretsmanager get-secret-value --secret-id <rds-master-secret-arn>
```

Update `devlink-prod/app-secrets` with the real JSON values. The `DATABASE_URL`
should look like:

```text
postgresql+asyncpg://devlink:<rds-password>@<rds-endpoint>:5432/devlink
```

Then scale services up:

```text
terraform apply
```

Open the app using:

```text
terraform output alb_dns_name
```

Smoke test:

```text
curl http://<alb-dns-name>/health
```

Then use the browser to register, create a link, visit `/r/{short_code}`, and
check analytics after the worker consumes the click event.

### Private GHCR Packages

If GHCR packages are private, ECS needs registry credentials. Create a Secrets
Manager secret shaped like:

```json
{"username":"<github-user>","password":"<ghcr-token-with-read-packages>"}
```

Set `container_registry_credentials_secret_arn` in `terraform.tfvars`. Public
GHCR packages can leave that variable empty.

## GitHub Actions Deployment

The CD workflow pushes images to GHCR, then deploys the new SHA tag to ECS.

Configure these GitHub repository variables:

- `AWS_REGION`
- `ECS_CLUSTER_NAME`
- `ECS_API_SERVICE_NAME`
- `ECS_WORKER_SERVICE_NAME`
- `ECS_WEB_SERVICE_NAME`

Use the Terraform outputs for the ECS names.

Configure this GitHub repository secret:

- `AWS_ROLE_TO_ASSUME`: IAM role ARN trusted by GitHub Actions OIDC.

That role needs permission to describe/register ECS task definitions, update ECS
services, pass the ECS task roles, and read the ECS task definition metadata.
Keep the role scoped to this cluster and task families where possible.

## Rollback

Fast rollback to the previous ECS task definition revision:

```text
aws ecs list-task-definitions ^
  --family-prefix devlink-prod-api ^
  --sort DESC

aws ecs update-service ^
  --cluster devlink-prod ^
  --service devlink-prod-api ^
  --task-definition <previous-api-task-definition-arn>
```

Repeat for `devlink-prod-web` and `devlink-prod-analytics-worker` if needed,
then wait for stability:

```text
aws ecs wait services-stable ^
  --cluster devlink-prod ^
  --services devlink-prod-api devlink-prod-web devlink-prod-analytics-worker
```

For image rollback through Terraform, set `image_tag` to a previous Git SHA and
run `terraform apply`.

## AWS Teardown

To avoid runaway costs, destroy the stack when the demo is not needed:

```text
cd infra/terraform
terraform destroy
```

Secrets Manager secrets may have scheduled deletion windows. If you created test
secrets manually, schedule or force-delete them separately after confirming you
do not need the data:

```text
aws secretsmanager delete-secret --secret-id devlink-prod/app-secrets
```
