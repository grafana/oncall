#!/bin/bash

set -x

CELERY_ARGS=(
  "-A" "engine"
  "beat"
)
if [[ $CELERY_WORKER_DEBUG_LOGS = True ]]; then
  CELERY_ARGS+=("-l" "debug")
else
  CELERY_ARGS+=("-l" "info")
fi

celery "${CELERY_ARGS[@]}"
