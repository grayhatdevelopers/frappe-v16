#!/usr/bin/env bash
# Prints the image built from this commit's build/, so each version of it is built once
# and a release publishes the image its pull requests tested. The image records the same
# Git tree as its revision (build/Containerfile).
set -Eeuo pipefail

tree=$(git rev-parse HEAD:build)
echo "ghcr.io/grayhatdevelopers/frappe-v16:build-${tree:0:12}"
