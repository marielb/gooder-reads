#!/bin/bash

#
# Usage: install-python-dependencies.sh <build-environment>
#    - build-environment is one of dev|deploy
#

set -e
if [ "$1" = "deploy" ]; then
  echo "Installing base + deploy dependencies"
  poetry install --no-dev --no-ansi -n # -E deploy
else
  echo "Installing base + dev dependencies"
  poetry install --no-ansi -n
fi
