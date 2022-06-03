#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD | sed 's/[^[:alnum:]\.\_\-]/-/g')

# If not a tag, use branch-hash else use tag
TAG=$(git --no-pager tag --points HEAD | paste -s -d, - 2> /dev/null || echo "")
if [ -z "$TAG" ]
then
      echo "${BRANCH}"
else
      echo "${TAG},latest"
fi