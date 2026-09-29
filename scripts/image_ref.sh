#!/usr/bin/env bash
# Prints the image built from this commit's build/, so each version of it is built once
# and a release publishes the image its pull requests tested.
set -Eeuo pipefail

key=$(git ls-tree HEAD build | git hash-object --stdin)
echo "ghcr.io/grayhatdevelopers/frappe-v16:build-${key:0:12}"
