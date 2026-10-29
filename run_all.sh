#!/usr/bin/env bash
# run_all.sh - Master execution script for Assignment 8: Optimize Anything
# Executes unit tests and verification suites across all tracks.

set -euo pipefail

echo "======================================================================"
echo " Starting Assignment 8 Test & Verification Suite"
echo " Date: $(date)"
echo " Environment: $(uname -s 2>/dev/null || echo Windows/PowerShell)"
echo "======================================================================"

if command -v python.exe >/dev/null 2>&1; then
    python.exe -m pytest -v --tb=short
elif command -v pytest >/dev/null 2>&1; then
    pytest -v --tb=short
elif command -v py >/dev/null 2>&1; then
    py -3 -m pytest -v --tb=short
elif command -v python >/dev/null 2>&1; then
    python -m pytest -v --tb=short
elif command -v python3 >/dev/null 2>&1; then
    python3 -m pytest -v --tb=short
else
    echo "Error: Neither python nor pytest found in PATH." >&2
    exit 1
fi

echo "======================================================================"
echo " All track test suites executed successfully."
echo "======================================================================"
