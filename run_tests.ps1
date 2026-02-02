#!/usr/bin/env pwsh
# Quick test runner script for Cash Forecast Analyzer
# Usage: .\run_tests.ps1 [test_type]
# Examples:
#   .\run_tests.ps1          # Run all tests
#   .\run_tests.ps1 smoke    # Run smoke tests only
#   .\run_tests.ps1 quick    # Run quick tests (smoke only)
#   .\run_tests.ps1 full     # Run all tests with coverage

param(
    [string]$TestType = "all"
)

Write-Host "Cash Forecast Analyzer - Test Runner" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we're in the project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Virtual environment not activated. Activating..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

switch ($TestType) {
    "smoke" {
        Write-Host "Running smoke tests only..." -ForegroundColor Green
        pytest tests/test_smoke.py -v
    }
    "endpoints" {
        Write-Host "Running endpoint tests only..." -ForegroundColor Green
        pytest tests/test_endpoints.py -v
    }
    "session" {
        Write-Host "Running session tests only..." -ForegroundColor Green
        pytest tests/test_session_flow.py -v
    }
    "quick" {
        Write-Host "Running quick tests (smoke)..." -ForegroundColor Green
        pytest tests/test_smoke.py -v --tb=line
    }
    "full" {
        Write-Host "Running full test suite with coverage..." -ForegroundColor Green
        pytest --cov=. --cov-report=term --cov-report=html -v
        Write-Host ""
        Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Cyan
    }
    "ci" {
        Write-Host "Running CI test suite..." -ForegroundColor Green
        pytest --tb=short -v
    }
    default {
        Write-Host "Running all tests..." -ForegroundColor Green
        pytest -v
    }
}

# Capture exit code
$ExitCode = $LASTEXITCODE

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Exit code: $ExitCode" -ForegroundColor Red
}

Write-Host ""
exit $ExitCode
