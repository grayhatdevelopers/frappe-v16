#!/usr/bin/env bash
# Prints the image built from this commit's build/ and image workflow, so each is built once
# and a release publishes the image its pull requests tested.
set -Eeuo pipefail

key=$(git ls-tree HEAD build .github/workflows/build-image.yml | git hash-object --stdin)
echo "ghcr.io/grayhatdevelopers/frappe-v16:build-${key:0:12}"
