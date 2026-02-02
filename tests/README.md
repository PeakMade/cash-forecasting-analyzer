# Test Suite for Cash Forecast Analyzer

## Overview

This test suite provides automated testing for the Cash Forecast Analyzer application. Tests are organized into three main categories:

### 1. Smoke Tests (`test_smoke.py`)
Basic sanity checks that verify the application can start and core functionality works:
- Application imports without errors
- Flask app is properly configured
- Required packages are installed
- Core modules can be imported
- Routes are registered correctly
- Utility functions work as expected

**Run with:** `pytest tests/test_smoke.py`

### 2. Endpoint Tests (`test_endpoints.py`)
HTTP endpoint testing to verify proper responses and status codes:
- Public endpoints are accessible
- Protected endpoints require authentication
- Session management endpoints exist
- Error handling works correctly
- API endpoints respond appropriately

**Run with:** `pytest tests/test_endpoints.py`

### 3. Session Flow Tests (`test_session_flow.py`)
Session management and lifecycle testing:
- Session state management
- Session logging flags
- User info preservation
- Environment detection
- Session validity checking

**Run with:** `pytest tests/test_session_flow.py`

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_smoke.py
pytest tests/test_endpoints.py
pytest tests/test_session_flow.py
```

### Run Specific Test Class
```bash
pytest tests/test_smoke.py::TestApplicationStartup
```

### Run Specific Test
```bash
pytest tests/test_smoke.py::TestApplicationStartup::test_app_imports_without_error
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage Report
```bash
pytest --cov=. --cov-report=html
```

## Test Markers

Tests can be marked for selective execution:

```bash
# Run only smoke tests
pytest -m smoke

# Run only endpoint tests
pytest -m endpoints

# Run only session tests
pytest -m session

# Skip slow tests
pytest -m "not slow"
```

## Continuous Integration

These tests should be run:
- Before every commit
- Before every push to production
- As part of CI/CD pipeline
- After any dependency updates

## Expected Results

When all tests pass, you should see output like:
```
===================== test session starts ======================
collected 35 items

tests/test_smoke.py ........................    [ 68%]
tests/test_endpoints.py ............            [ 80%]
tests/test_session_flow.py .......              [100%]

===================== 35 passed in 2.45s =======================
```

## Adding New Tests

When adding new features:
1. Add smoke tests for basic functionality
2. Add endpoint tests for new routes
3. Add session tests for state changes
4. Update this README with new test descriptions

## Common Issues

### Import Errors
If you see import errors, ensure you're in the project root and the virtual environment is activated:
```bash
cd C:\Users\ffree\OneDrive - PeakMade Real Estate\Documents\git\cash-forecast-analyzer
.\venv\Scripts\Activate.ps1
pytest
```

### Missing Dependencies
Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

### Authentication Errors
Some tests may require environment variables to be set. Check `.env` file is present with required Azure credentials.

## Test Philosophy

These tests follow the testing pyramid:
- **Many** smoke/unit tests (fast, isolated)
- **Some** endpoint/integration tests (medium speed)
- **Few** full end-to-end tests (slow, comprehensive)

Goal: Catch 80% of issues in < 5 seconds, 95% in < 30 seconds.
