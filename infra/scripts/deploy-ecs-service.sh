#!/usr/bin/env bash
set -euo pipefail

cluster_name="${1:?cluster name is required}"
service_name="${2:?service name is required}"
container_name="${3:?container name is required}"
image_uri="${4:?image URI is required}"

current_task_definition_arn="$(
  aws ecs describe-services \
    --cluster "$cluster_name" \
    --services "$service_name" \
    --query 'services[0].taskDefinition' \
    --output text
)"

aws ecs describe-task-definition \
  --task-definition "$current_task_definition_arn" \
  --query 'taskDefinition' \
  --output json > task-definition.json

jq \
  --arg container_name "$container_name" \
  --arg image_uri "$image_uri" \
  '
  .containerDefinitions |= map(
    if .name == $container_name then .image = $image_uri else . end
  )
  | del(
      .taskDefinitionArn,
      .revision,
      .status,
      .requiresAttributes,
      .compatibilities,
      .registeredAt,
      .registeredBy
    )
  ' task-definition.json > task-definition-updated.json

new_task_definition_arn="$(
  aws ecs register-task-definition \
    --cli-input-json file://task-definition-updated.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text
)"

aws ecs update-service \
  --cluster "$cluster_name" \
  --service "$service_name" \
  --task-definition "$new_task_definition_arn" \
  --force-new-deployment \
  >/dev/null

echo "Updated $service_name to $new_task_definition_arn"
