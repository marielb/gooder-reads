#!/bin/bash
#
# Usage: install-system-dependencies.sh <pip-version> <poetry-version>
#

set -e
# Install system dependencies
echo "Installing Build Dependencies"
export DEBIAN_FRONTEND=noninteractive
apt-get update

# these aren't strictly necessary but can be useful to have
apt-get install -y --no-install-recommends \
    curl \
    unzip \
    jq

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

# Upgrade pip and install poetry
echo "Installing pip/poetry"
pip install --no-cache-dir -U pip==$1
POETRY_VERSION=$2 curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
