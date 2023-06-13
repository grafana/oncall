#!/bin/bash

ENGINE_DIR="engine"
UI_DIR="grafana-plugin"
PUBLIC_DOCS_DIR="docs"

DIRS_CHANGED=$(git diff HEAD~1 --name-only | xargs dirname | sort | uniq) # https://stackoverflow.com/a/73149899/3902555

if [[ $DIRS_CHANGED =~ $ENGINE_DIR ]] || [[ $DIRS_CHANGED =~ $UI_DIR ]]; then
  echo "Changes were made to the ${ENGINE_DIR} and/or ${UI_DIR} directories"

  # check if we have any changes to the public docs directory as well. If not,
  if [[ ! $DIRS_CHANGED =~ $PUBLIC_DOCS_DIR ]]; then
    echo "Changes were not made to the public documentation (${PUBLIC_DOCS_DIR} directory). Either update the documentation accordingly with your changes, or add the 'no public docs' label if changes to the public docs are not necessary for your PR."
    exit 1
  else
    echo "Changes were also made to the public documentation. Thank you!"
    exit 0
  fi

else
  echo "Changes were not made to either the ${ENGINE_DIR} or ${UI_DIR} directories"
fi
