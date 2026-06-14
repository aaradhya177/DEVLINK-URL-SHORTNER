# Monitoring

DEVLINK monitors four things first:

- API errors and request latency.
- Redirect latency, especially cache-hit versus DB-fallback timing.
- Analytics pipeline health, especially Kafka consumer lag and worker processing
  time.
- Resource utilization for ECS tasks and RDS.

## Logs

The API and analytics worker emit JSON logs to stdout. In ECS, task definitions
ship stdout to CloudWatch Logs through the `awslogs` driver:

- API: `/ecs/devlink-prod/api`
- Worker: `/ecs/devlink-prod/analytics-worker`
- Web: `/ecs/devlink-prod/web`
- Kafka-compatible broker: `/ecs/devlink-prod/kafka`

Common log fields:

- `timestamp`
- `level`
- `service`
- `logger`
- `message`
- `correlation_id`
- `event_id`, where relevant
- `link_id`, where relevant

The API correlation middleware accepts `X-Correlation-ID` or `X-Request-ID`.
If neither is present, it creates a UUID and returns it in both response
headers. Redirect clicks pass that `correlation_id` into the Kafka message so a
single click can be traced from redirect logs to worker aggregation logs.

CloudWatch Logs Insights example:

```text
fields @timestamp, service, message, correlation_id, event_id, link_id
| filter correlation_id = "paste-correlation-id-here"
| sort @timestamp asc
```

Redirect latency log event:

```text
message = "redirect_timing"
```

Important fields on that event:

- `cache`: `HIT` or `MISS`
- `rate_limit_ms`
- `cache_lookup_ms`
- `db_fallback_ms`
- `total_response_ms`

## Metrics

The API exposes Prometheus-format metrics at `/metrics` using
`prometheus-fastapi-instrumentator`. This includes request counts, latency
histograms, status codes, and handler labels.

The worker exposes Prometheus-format metrics on port `9101`:

- `devlink_worker_click_events_processed_total{result=...}`
- `devlink_worker_click_event_processing_seconds`
- `devlink_worker_kafka_consumer_lag{topic=...,partition=...}`

The public ALB intentionally does not route `/metrics`; metrics endpoints should
not be public. To inspect metrics in AWS, use a private debugging path such as
ECS Exec, an internal scraper, or a temporary bastion inside the VPC. For local
development:

```text
curl http://localhost:8000/metrics
curl http://localhost:9101/metrics
```

## CloudWatch Dashboard

Terraform creates a dashboard named `devlink-prod` by default. It includes:

- ALB API 5xx count and API unhealthy target count.
- ECS CPU for API, worker, and web services.
- RDS CPU and database connections.

Use `terraform output cloudwatch_dashboard_name` to confirm the dashboard name.

## Alarms

Terraform creates these baseline alarms:

- `devlink-prod-api-5xx`: API target group returned at least five 5xx responses
  in five minutes.
- `devlink-prod-api-unhealthy-hosts`: at least one API task is unhealthy behind
  the ALB.
- `devlink-prod-web-unhealthy-hosts`: at least one web task is unhealthy behind
  the ALB.
- `devlink-prod-rds-cpu-high`: RDS CPU averaged at least 80%.
- `devlink-prod-rds-connections-high`: RDS connections averaged at least 80.
- `devlink-prod-api-cpu-high`: API ECS service CPU averaged at least 80%.
- `devlink-prod-worker-cpu-high`: worker ECS service CPU averaged at least 80%.

Alarm actions are intentionally not wired yet because notification routing
depends on the deployment owner. Add an SNS topic or PagerDuty integration when
the AWS account is real.

## Mini Runbook

API 5xx alarm:

1. Open CloudWatch Logs Insights for `/ecs/devlink-prod/api`.
2. Query recent error logs:

   ```text
   fields @timestamp, level, message, correlation_id, error, exception
   | filter level in ["ERROR", "WARNING"]
   | sort @timestamp desc
   | limit 50
   ```

3. Check whether errors correlate with deploy time. If yes, roll back the API
   ECS service to the previous task definition revision.

Redirect latency regression:

1. Query `redirect_timing` logs.
2. If `cache_lookup_ms` is high or Redis warnings appear, check ElastiCache.
3. If `db_fallback_ms` dominates and cache status is mostly `MISS`, check cache
   invalidation patterns and DB query plans.
4. If `total_response_ms` rises while cache/DB timing is low, inspect ALB/ECS CPU
   and memory.

Worker lag:

1. Check worker logs for `click_event_db_write_failed`.
2. Check worker metrics `devlink_worker_kafka_consumer_lag`.
3. If lag grows but CPU is low, inspect DB locks/connections.
4. If CPU is high, scale worker desired count or reduce event parsing work.

RDS CPU or connection alarm:

1. Check API and worker deploys for connection pool changes.
2. Inspect slow queries and dashboard analytics traffic.
3. Temporarily reduce API concurrency or scale RDS if the traffic is legitimate.

ECS task health alarm:

1. Open the ECS service events tab.
2. Check container logs for startup failures.
3. Verify Secrets Manager values and image pull credentials.
4. Roll back to the previous task definition if the failure began after deploy.
