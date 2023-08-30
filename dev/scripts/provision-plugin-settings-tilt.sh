#!/usr/bin/env bash
set -Eeou pipefail

echo "Starting post build"

while :
do
    # timeout -1s means a week
    tilt wait --timeout=-1s --for=condition=UpToDate=true uiresource/$1

    echo "Build UpToDate! Running post_build command"

    tilt trigger "$2"

    tilt wait --timeout=-1s --for=condition=UpToDate=false uiresource/$1
    echo "Build not UpToDate..."
done
