#!/bin/bash

set -x

# If $CELERY_WORKER_SHUTDOWN_INTERVAL env variable is set,
# then add the background process to shutdown celery in $CELERY_WORKER_SHUTDOWN_INTERVAL
if [ -n "$CELERY_WORKER_SHUTDOWN_INTERVAL" ]; then
  sleep $CELERY_WORKER_SHUTDOWN_INTERVAL && celery -A engine control shutdown &
fi

# Validating required parameters
if [ -z "$CELERY_WORKER_QUEUE" ]; then
  echo "CELERY_WORKER_QUEUE is not set"
  exit 1
fi

if [ -z "$CELERY_WORKER_CONCURRENCY" ]; then
  echo "CELERY_WORKER_CONCURRENCY is not set"
  exit 1
fi

if [ -z "$CELERY_WORKER_MAX_TASKS_PER_CHILD" ]; then
  echo "CELERY_WORKER_MAX_TASKS_PER_CHILD is not set"
  exit 1
fi

CELERY_ARGS=(
  "--quiet"  # --quite parameter removes pointless banner when celery starts
  "-A" "engine"
  "worker"
  "--concurrency=$CELERY_WORKER_CONCURRENCY"
  "--max-tasks-per-child=$CELERY_WORKER_MAX_TASKS_PER_CHILD"
  "-Q" "$CELERY_WORKER_QUEUE"
)
if [[ $CELERY_WORKER_BEAT_ENABLED = True ]]; then
  CELERY_ARGS+=("--beat")
fi
if [[ $CELERY_WORKER_WITHOUT_MINGLE = True ]]; then
  CELERY_ARGS+=("--without-mingle")
fi
if [[ $CELERY_WORKER_WITHOUT_GOSSIP = True ]]; then
  CELERY_ARGS+=("--without-gossip")
fi
if [[ $CELERY_WORKER_WITHOUT_HEARTBEAT = True ]]; then
  CELERY_ARGS+=("--without-heartbeat")
fi
if [[ $CELERY_WORKER_DEBUG_LOGS = True ]]; then
  CELERY_ARGS+=("-l" "debug")
else
  CELERY_ARGS+=("-l" "info")
fi

celery "${CELERY_ARGS[@]}"
