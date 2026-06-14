# Future Work

These items are intentionally left as future work and are useful talking points
for interviews or planning.

## Product

- Implement Google OAuth end-to-end once real client credentials and callback
  domains exist.
- Add API keys for programmatic link creation.
- Add branded domains and custom domain verification.
- Add webhook notifications for link events.
- Add campaign/UTM builder UI.

## Analytics

- Add privacy-preserving unique click estimates. Options include HyperLogLog or
  rotating salted visitor hashes with clear retention rules.
- Add retention/archival jobs for old `click_events` partitions.
- Add export endpoints for CSV analytics reports.
- Add finer time granularities once aggregate tables support hour-level rollups.

## Infrastructure

- Add HTTPS/ACM and Route 53 domain setup to Terraform.
- Replace the low-cost Kafka-compatible ECS broker with MSK or another managed
  event bus for real production use.
- Move ECS tasks into private subnets with NAT Gateway or VPC endpoints.
- Add SNS alarm actions and notification routing.
- Add Terraform remote state and state locking.

## Security

- Commit reproducible lock files or exported hashed requirements for Python
  dependency auditing.
- Add WAF/bot protection on the public ALB or CDN.
- Add admin tooling for malicious-link review and appeal workflows.

## Developer Experience

- Add a one-command local bootstrap script.
- Add generated TypeScript API clients from `docs/api-spec.yaml`.
- Add Playwright end-to-end tests for register -> create link -> redirect ->
  analytics.
