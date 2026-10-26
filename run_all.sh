#!/usr/bin/env bash
# run_all.sh - Master execution script for Assignment 8: Optimize Anything
# Executes unit tests and verification suites across all tracks.

set -euo pipefail

echo "======================================================================"
echo " Starting Assignment 8 Test & Verification Suite"
echo " Date: $(date)"
echo " Environment: $(uname -s 2>/dev/null || echo Windows/PowerShell)"
echo "======================================================================"

python3 -m pytest -v --tb=short track_*/tests/ || python -m pytest -v --tb=short track_*/tests/

echo "======================================================================"
echo " All track test suites executed successfully."
echo "======================================================================"
