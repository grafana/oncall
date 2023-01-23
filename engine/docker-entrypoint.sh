#!/bin/bash
# This script will run on every start of the Grafan Oncall container
# and wait for the database to be ready.

# Fail when the first error occures
set -e

# Try to connect to the DB by showing the migrations
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT-3}
MAX_DB_WAIT_TIME=${MAX_DB_WAIT_TIME-30}
CUR_DB_WAIT_TIME=0
while [ "${CUR_DB_WAIT_TIME}" -lt "${MAX_DB_WAIT_TIME}" ]; do
  # Read and truncate connection error tracebacks to last line by default
  exec {psfd}< <(./manage.py showmigrations 2>&1)
  read -rd '' DB_ERR <&$psfd || :
  exec {psfd}<&-
  wait $! && break
  readarray -tn 0 DB_ERR_LINES <<<"$DB_ERR"
  echo "${DB_ERR_LINES[@]: -1}"
  echo "⏳ Waiting on DB... (${CUR_DB_WAIT_TIME}s / ${MAX_DB_WAIT_TIME}s)"
  sleep "${DB_WAIT_TIMEOUT}"
  CUR_DB_WAIT_TIME=$((CUR_DB_WAIT_TIME + DB_WAIT_TIMEOUT))
done
if [ "${CUR_DB_WAIT_TIME}" -ge "${MAX_DB_WAIT_TIME}" ]; then
  echo "❌ Waited ${MAX_DB_WAIT_TIME}s or more for the DB to become ready."
  exit 1
fi

echo "✅ Database is ready."

# Launch whatever is passed by docker
# (i.e. the RUN instruction in the Dockerfile)
exec "$@"
