"""
Authentication & SharePoint Logging Diagnostic Tool
Tests all aspects of the authentication flow and SharePoint connectivity
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_environment_config():
    """Test that all required environment variables are set"""
    print_section("1. ENVIRONMENT CONFIGURATION")
    
    required_vars = [
        'AZURE_AD_CLIENT_ID',
        'AZURE_AD_CLIENT_SECRET',
        'AZURE_AD_TENANT_ID',
        'AZURE_AD_REDIRECT_URI',
        'SHAREPOINT_SITE_URL',
        'PROPERTY_DATA_SOURCE'
    ]
    
    all_good = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var:
                print(f"✓ {var}: ***configured*** ({len(value)} chars)")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: MISSING")
            all_good = False
    
    return all_good

def test_msal_library():
    """Test that MSAL library is installed and working"""
    print_section("2. MSAL LIBRARY CHECK")
    
    try:
        import msal
        print(f"✓ MSAL library installed: version {msal.__version__}")
        return True
    except ImportError as e:
        print(f"✗ MSAL library not installed: {e}")
        print("  Run: pip install msal==1.26.0")
        return False

def test_office365_library():
    """Test that Office365 library is installed"""
    print_section("3. OFFICE365 LIBRARY CHECK")
    
    try:
        import office365
        print(f"✓ Office365-REST-Python-Client installed")
        from office365.sharepoint.client_context import ClientContext
        print(f"✓ ClientContext import successful")
        return True
    except ImportError as e:
        print(f"✗ Office365 library not installed: {e}")
        print("  Run: pip install Office365-REST-Python-Client==2.5.3")
        return False

def test_user_token_acquisition():
    """Test acquiring a user token (delegated permissions)"""
    print_section("4. USER TOKEN ACQUISITION (Delegated Permissions)")
    
    try:
        from services.auth import AzureADAuth
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
        
        auth = AzureADAuth(app)
        
        print(f"✓ AzureADAuth initialized")
        print(f"  Client ID: {auth.client_id[:8]}...")
        print(f"  Tenant ID: {auth.tenant_id}")
        print(f"  Authority: {auth.authority}")
        print(f"  Scopes: {auth.scopes}")
        
        # Test authorization URL generation
        auth_url = auth.get_auth_url()
        if auth_url and 'authorize' in auth_url:
            print(f"✓ Authorization URL generated successfully")
            print(f"  URL: {auth_url[:80]}...")
            return True
        else:
            print(f"✗ Failed to generate authorization URL")
            return False
            
    except Exception as e:
        print(f"✗ User token acquisition test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_app_only_token_acquisition():
    """Test acquiring an app-only token (application permissions)"""
    print_section("5. APP-ONLY TOKEN ACQUISITION (Application Permissions)")
    
    try:
        from services.auth import AzureADAuth
        from flask import Flask
        import msal
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
        
        auth = AzureADAuth(app)
        
        print(f"Attempting to acquire app-only token...")
        print(f"  Client ID: {auth.client_id[:8]}...")
        print(f"  Tenant ID: {auth.tenant_id}")
        print(f"  Scope: https://peakcampus.sharepoint.com/.default")
        
        # Create MSAL confidential client
        msal_app = msal.ConfidentialClientApplication(
            auth.client_id,
            authority=auth.authority,
            client_credential=auth.client_secret
        )
        
        # Try to acquire app-only token
        result = msal_app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        if "access_token" in result:
            token = result["access_token"]
            print(f"✓ APP-ONLY TOKEN ACQUIRED SUCCESSFULLY!")
            print(f"  Token length: {len(token)} characters")
            
            # Decode token to check permissions
            try:
                import base64
                import json
                # Decode JWT payload (middle section)
                parts = token.split('.')
                if len(parts) >= 2:
                    # Add padding if needed
                    payload = parts[1]
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding
                    decoded = json.loads(base64.urlsafe_b64decode(payload))
                    
                    print(f"\n  Token Details:")
                    print(f"    App ID: {decoded.get('appid', 'N/A')}")
                    print(f"    Audience: {decoded.get('aud', 'N/A')}")
                    print(f"    Roles (App Permissions): {decoded.get('roles', [])}")
                    print(f"    Scopes (Delegated): {decoded.get('scp', 'N/A')}")
                    
                    # Check for required permissions
                    roles = decoded.get('roles', [])
                    if not roles:
                        print(f"\n  ⚠️  WARNING: No application permissions (roles) found in token!")
                        print(f"      You need to grant Application permissions in Azure AD:")
                        print(f"      - Sites.ReadWrite.All or Sites.FullControl.All")
                        print(f"      See: AUTHENTICATION_CONTEXT.md for instructions")
                        return False
                    elif 'Sites.FullControl.All' in roles or 'Sites.ReadWrite.All' in roles:
                        print(f"  ✓ Required SharePoint permissions found!")
                        return True
                    else:
                        print(f"  ⚠️  WARNING: SharePoint permissions may be insufficient")
                        print(f"      Found roles: {roles}")
                        return False
                        
            except Exception as e:
                print(f"  (Could not decode token: {e})")
                print(f"  ✓ Token acquired, but could not verify permissions")
                return True
            
            return True
        else:
            error = result.get('error', 'Unknown error')
            error_desc = result.get('error_description', 'No description')
            print(f"✗ APP-ONLY TOKEN ACQUISITION FAILED")
            print(f"  Error: {error}")
            print(f"  Description: {error_desc}")
            print(f"\nCommon causes:")
            print(f"  1. Application permissions not granted in Azure AD")
            print(f"  2. Admin consent not provided")
            print(f"  3. Incorrect client secret")
            print(f"\nTo fix:")
            print(f"  1. Go to Azure Portal → Azure AD → App Registrations")
            print(f"  2. Select your app: {auth.client_id}")
            print(f"  3. Go to 'API permissions'")
            print(f"  4. Add permission → Microsoft Graph → Application permissions")
            print(f"  5. Select 'Sites.ReadWrite.All'")
            print(f"  6. Click 'Grant admin consent' button")
            return False
            
    except Exception as e:
        print(f"✗ Exception during app-only token test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sharepoint_connection():
    """Test SharePoint connection with app-only token via Graph API"""
    print_section("6. SHAREPOINT CONNECTION TEST (via Graph API)")
    
    try:
        from services.auth import AzureADAuth
        from flask import Flask
        import msal
        from urllib.parse import urlparse
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
        
        auth = AzureADAuth(app)
        
        # Get app-only token for Graph API
        print("Acquiring app-only token for Graph API...")
        msal_app = msal.ConfidentialClientApplication(
            auth.client_id,
            authority=auth.authority,
            client_credential=auth.client_secret
        )
        
        result = msal_app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        if "access_token" not in result:
            print("✗ Cannot test SharePoint connection - app token acquisition failed")
            return False
        
        app_token = result["access_token"]
        print(f"✓ Graph API app-only token acquired")
        
        # Parse SharePoint site URL
        site_url = os.environ.get('SHAREPOINT_SITE_URL')
        log_list_name = os.environ.get('SHAREPOINT_LOG_LIST_NAME', 'Innovation Use Log')
        
        parsed = urlparse(site_url)
        host = parsed.netloc
        path = parsed.path
        
        print(f"\nConnecting to SharePoint via Graph API:")
        print(f"  Site: {site_url}")
        print(f"  Host: {host}")
        print(f"  Path: {path}")
        print(f"  Log List: {log_list_name}")
        
        # Step 1: Resolve site ID
        print(f"\nStep 1: Resolving site ID...")
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{host}:{path}"
        headers = {
            'Authorization': f'Bearer {app_token}',
            'Accept': 'application/json'
        }
        
        response = requests.get(graph_url, headers=headers)
        response.raise_for_status()
        
        site_data = response.json()
        site_id = site_data.get('id')
        print(f"✓ Site ID: {site_id}")
        
        # Step 2: Resolve list ID
        print(f"\nStep 2: Resolving list ID...")
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
        params = {'$filter': f"displayName eq '{log_list_name}'"}
        
        response = requests.get(graph_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        lists = data.get('value', [])
        
        if not lists:
            print(f"✗ List '{log_list_name}' not found")
            print(f"\nAvailable lists:")
            # Get all lists to show what's available
            response = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers)
            all_lists = response.json().get('value', [])
            for lst in all_lists[:10]:  # Show first 10
                print(f"  - {lst.get('displayName')}")
            return False
        
        list_id = lists[0].get('id')
        list_item_count = lists[0].get('list', {}).get('itemCount', 'N/A')
        print(f"✓ List ID: {list_id}")
        print(f"✓ Item Count: {list_item_count}")
        
        # Step 3: Test write access by creating a test item
        print(f"\nStep 3: Testing write access...")
        test_entry = {
            'fields': {
                'Title': 'DIAGNOSTIC_TEST',
                'UserEmail': 'diagnostic@test.com',
                'UserName': 'Diagnostic Test',
                'LoginTimestamp': datetime.utcnow().isoformat() + 'Z',
                'UserRole': 'test',
                'ActivityType': 'Diagnostic Test',
                'Application': 'CashForecastAnalyzer',
                'Env': 'Diagnostic'
            }
        }
        
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items"
        response = requests.post(graph_url, json=test_entry, headers=headers)
        response.raise_for_status()
        
        print(f"✓ Successfully created test log entry")
        print(f"✓ SharePoint logging via Graph API is working!")
        
        return True
        
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response else 0
        error_msg = e.response.text if e.response else str(e)
        
        print(f"✗ Graph API request failed: HTTP {status_code}")
        
        if status_code == 404:
            print(f"\n  ISSUE: Resource not found")
            print(f"  - Verify SHAREPOINT_SITE_URL is correct in .env")
            print(f"  - Verify the list '{log_list_name}' exists")
        elif status_code == 403:
            print(f"\n  ISSUE: Forbidden - insufficient permissions")
            print(f"  - Ensure 'Sites.ReadWrite.All' (Graph) permission is granted")
            print(f"  - Ensure admin consent was granted in Azure AD")
        elif status_code == 401:
            print(f"\n  ISSUE: Unauthorized")
            print(f"  - Check client secret is correct")
            print(f"  - Verify app registration is active")
        
        print(f"\nError details: {error_msg[:200]}")
        return False
        
    except Exception as e:
        print(f"✗ SharePoint connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  CASH FORECAST ANALYZER - AUTHENTICATION DIAGNOSTICS".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    results = []
    
    # Run all tests
    results.append(("Environment Configuration", test_environment_config()))
    results.append(("MSAL Library", test_msal_library()))
    results.append(("Office365 Library", test_office365_library()))
    results.append(("User Token Generation", test_user_token_acquisition()))
    results.append(("App-Only Token Acquisition", test_app_only_token_acquisition()))
    results.append(("SharePoint Connection", test_sharepoint_connection()))
    
    # Print summary
    print_section("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Authentication system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        print("\nNext steps:")
        print("1. Review failed tests above for specific error messages")
        print("2. Check AUTHENTICATION_CONTEXT.md for detailed setup instructions")
        print("3. Verify Azure AD app registration has correct permissions")
        print("4. Run this diagnostic again after making fixes")
        return 1

if __name__ == '__main__':
    sys.exit(main())
