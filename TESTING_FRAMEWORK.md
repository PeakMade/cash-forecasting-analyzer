# Automated Testing Framework

**Project:** Cash Forecast Analyzer  
**Testing Framework:** pytest  
**Last Updated:** January 27, 2026  
**Test Suite Status:** ✅ 36 Passing, 1 Skipped

---

## Overview

This document describes our automated testing framework and serves as a template for implementing automated tests across all team applications. Automated testing ensures code quality, prevents regressions, and validates functionality before deployment.

## Test Organization

Our tests are organized into three main categories:

### 1. **Endpoint Tests** (`tests/test_endpoints.py`)
Tests HTTP endpoints for proper responses, status codes, and authentication handling.

### 2. **Session Flow Tests** (`tests/test_session_flow.py`)
Tests session management lifecycle, including session start, end, restart, and state preservation.

### 3. **Smoke Tests** (`tests/test_smoke.py`)
Quick sanity checks that verify the application can start and core functionality works.

---

## Test Inventory

### Endpoint Tests (13 tests)

#### **Public Endpoints** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_login_page_accessible` | Verifies login page redirects to Microsoft authentication |
| `test_session_ended_page_exists` | Verifies session ended page is accessible without authentication |

#### **Protected Endpoints** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_index_requires_auth` | Verifies main page redirects to login when not authenticated |
| `test_api_properties_requires_auth` | Verifies properties API endpoint requires authentication |
| `test_api_analyze_requires_auth` | Verifies analysis endpoint requires authentication |

#### **Session Endpoints** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_session_end_endpoint_exists` | Verifies logout endpoint exists and is accessible |
| `test_session_start_endpoint_exists` | Verifies session start endpoint exists |
| `test_session_check_endpoint_exists` | Verifies session validation endpoint returns JSON |

#### **API Endpoints** (1 test)
| Test Name | Purpose |
|-----------|---------|
| `test_api_analyze_without_files` | Verifies analyze endpoint rejects requests without required files |

#### **Error Handling** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_404_handling` | Verifies 404 errors are properly handled |
| `test_invalid_method` | Verifies invalid HTTP methods are rejected with 405 status |

#### **Health Checks** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_app_has_secret_key` | Verifies Flask secret key is configured |
| `test_app_in_correct_mode` | Verifies app runs in testing mode during tests |

---

### Session Flow Tests (12 tests)

#### **Session State Management** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_session_starts_unauthenticated` | Verifies new sessions are not authenticated by default |
| `test_session_can_store_user_info` | Verifies session can store and retrieve user information |
| `test_session_ended_flag` | Verifies session_ended flag behavior works correctly |

#### **Session Logging Flags** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_session_start_logged_flag` | Verifies session_start_logged flag prevents duplicate logging |
| `test_session_restart_clears_flag` | Verifies session restart clears logging flags |

#### **Session Validity Checking** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_session_check_no_tokens` | Verifies session check returns invalid when no tokens present |
| `test_session_check_returns_json` | Verifies session check endpoint returns proper JSON format |

#### **User Info Preservation** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_user_info_preserved_on_session_end` | Verifies user info is preserved when session ends |
| `test_preserved_user_info_restored_on_restart` | Verifies preserved user info is restored on session restart |

#### **Environment Functions** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_is_local_environment` | Verifies environment detection returns boolean |
| `test_get_application_name_returns_correct_format` | Verifies application name format is correct |
| `test_application_name_matches_environment` | Verifies application name consistency |

---

### Smoke Tests (12 tests)

#### **Application Startup** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_app_imports_without_error` | Verifies app.py can be imported without exceptions |
| `test_flask_app_exists` | Verifies Flask app object is created properly |
| `test_required_config_exists` | Verifies required configuration values are present |

#### **Core Modules** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_services_import` | Verifies services module imports successfully |
| `test_azure_auth_import` | ⏭️ **SKIPPED** - AzureAuth class not currently in use |

#### **Environment Configuration** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_required_packages_installed` | Verifies all critical Python packages are available |
| `test_upload_folder_exists` | Verifies upload folder exists or can be created |

#### **Route Registration** (2 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_main_routes_exist` | Verifies all expected routes are registered |
| `test_static_files_configured` | Verifies static files configuration exists |

#### **Utility Functions** (3 tests)
| Test Name | Purpose |
|-----------|---------|
| `test_environment_detection` | Verifies environment detection function works |
| `test_application_name_generation` | Verifies application name is generated correctly |
| `test_allowed_file_validation` | Verifies file extension validation works (xlsx, xls, csv, txt, pdf) |

---

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_endpoints.py -v
python -m pytest tests/test_session_flow.py -v
python -m pytest tests/test_smoke.py -v
```

### Run Specific Test
```bash
python -m pytest tests/test_endpoints.py::TestPublicEndpoints::test_login_page_accessible -v
```

### Run Tests with Coverage (if coverage installed)
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

---

## Test Results Summary

**Current Status (as of January 27, 2026):**
- ✅ **36 tests passing**
- ⏭️ **1 test skipped** (AzureAuth import - class not currently in use)
- ⚠️ **4 warnings** (deprecation warnings in dependencies - non-critical)
- ⏱️ **Total runtime: ~3-5 seconds**

---

## Best Practices for Team Implementation

### 1. **Test Organization**
- Organize tests by functionality (endpoints, workflows, smoke tests)
- Use descriptive test class names that group related tests
- Keep test files under a `tests/` directory

### 2. **Test Naming Conventions**
- Test functions should start with `test_`
- Use descriptive names: `test_login_page_accessible` not `test_1`
- Names should clearly indicate what is being tested

### 3. **Test Types to Include**

#### **Smoke Tests** (Quick sanity checks)
- Application starts without errors
- Required modules can be imported
- Critical configuration exists
- Required dependencies are installed

#### **Endpoint Tests** (API/Route validation)
- All routes exist and are accessible
- Authentication/authorization works correctly
- Error handling returns proper status codes
- Invalid requests are rejected

#### **Flow Tests** (Business logic validation)
- Session management works correctly
- State transitions function as expected
- Data persistence works properly
- User workflows complete successfully

### 4. **Pre-Deployment Checklist**
Before deploying to production:
1. ✅ Run full test suite: `python -m pytest tests/ -v`
2. ✅ Verify all tests pass (0 failures)
3. ✅ Check warnings for critical issues
4. ✅ Review any skipped tests to ensure they're intentional
5. ✅ Commit test updates along with code changes

### 5. **Continuous Integration**
- Run tests automatically before every deployment
- Set up CI/CD pipeline to run tests on every commit
- Block merges if tests fail
- Track test coverage metrics over time

---

## Dependencies

**Required Packages:**
```
pytest>=9.0.0
flask
pandas
openpyxl
pypdf
openai
requests
msal
```

Install test dependencies:
```bash
pip install pytest
# or install all requirements
pip install -r requirements.txt
```

---

## Extending the Test Suite

When adding new features, add corresponding tests:

1. **New Endpoint?** → Add test to `test_endpoints.py`
2. **New Session Logic?** → Add test to `test_session_flow.py`
3. **New Module/Service?** → Add test to `test_smoke.py`

Example test structure:
```python
def test_new_feature(self, client):
    """Test that new feature works correctly"""
    # Arrange: Set up test data
    test_data = {'key': 'value'}
    
    # Act: Execute the feature
    response = client.post('/api/new-feature', json=test_data)
    
    # Assert: Verify expected outcome
    assert response.status_code == 200
    assert 'expected_field' in response.get_json()
```

---

## Questions or Issues?

If tests fail:
1. Read the error message carefully
2. Check if code changes broke existing functionality
3. Update tests if behavior intentionally changed
4. Ensure all dependencies are installed
5. Verify environment configuration is correct

---

## Team Standards

**This testing framework represents our team's commitment to:**
- ✅ Code quality through automated validation
- ✅ Preventing regressions with comprehensive test coverage
- ✅ Faster debugging with clear test failures
- ✅ Confidence in deployments with pre-deployment validation
- ✅ Documentation through test descriptions

**Every application should include:**
- Smoke tests (application starts, imports work)
- Endpoint tests (all routes validated)
- Flow tests (business logic verified)
- Pre-deployment test runs

**Goal:** Make automated testing a standard part of every project, not an afterthought.
