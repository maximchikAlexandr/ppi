#!/bin/sh
# Point git at tracked hooks. Run once after clone (PyCharm, terminal, any IDE):
#   sh .githooks/install.sh

set -e

git config --local core.hooksPath .githooks
echo "core.hooksPath = .githooks"
