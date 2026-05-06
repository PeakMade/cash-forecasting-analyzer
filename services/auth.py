"""
Azure AD Authentication Module
Handles user authentication via Microsoft identity platform
"""

import os
import logging
from functools import wraps
from flask import redirect, url_for, session, request, render_template_string
import msal

logger = logging.getLogger(__name__)


class AzureADAuth:
    """Handle Azure AD OAuth authentication flows"""
    
    def __init__(self, app=None):
        self.app = app
        self.client_id = os.environ.get('AZURE_AD_CLIENT_ID', '')
        self.client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('AZURE_AD_TENANT_ID', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.redirect_uri = os.environ.get('AZURE_AD_REDIRECT_URI', 
                                          'http://localhost:5000/auth/callback')
        
        # Request Graph API scopes during initial login for group membership checking
        # SharePoint access will be requested separately via consent flow
        # Note: offline_access, openid, profile are automatically added by MSAL
        self.scopes = [
            "User.Read",                # Graph: Read user profile
            "GroupMember.Read.All"      # Graph: Read group memberships
        ]
        
        # SharePoint-specific scopes (used in separate consent flow)
        self.sharepoint_scopes = ["https://peakcampus.sharepoint.com/.default"]
        
        # Graph API scopes for user profile and group membership
        self.graph_scopes = ["User.Read", "GroupMember.Read.All"]
        
        self.sharepoint_url = os.environ.get('SHAREPOINT_SITE_URL', 'https://peakcampus.sharepoint.com/sites/BaseCampApps')
    
    def get_msal_app(self, cache=None):
        """Create MSAL confidential client application with token cache"""
        # Always use a token cache - initialize from session if available
        if cache is None:
            cache = msal.SerializableTokenCache()
            if 'token_cache' in session:
                cache.deserialize(session['token_cache'])
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
            token_cache=cache
        )
        
        # Save cache back to session if it changed
        if cache.has_state_changed:
            session['token_cache'] = cache.serialize()
        
        return app
    
    def get_auth_url(self):
        """
        Generate Azure AD authorization URL
        
        Returns:
            Tuple of (auth_url, state)
        """
        msal_app = self.get_msal_app()
        
        auth_url = msal_app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url
    
    def get_sharepoint_consent_url(self):
        """
        Generate SharePoint consent URL
        
        Returns:
            Authorization URL for SharePoint consent
        """
        msal_app = self.get_msal_app()
        
        auth_url = msal_app.get_authorization_request_url(
            scopes=self.sharepoint_scopes,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url
    
    def acquire_sharepoint_token_by_code(self, code):
        """
        Exchange authorization code for SharePoint access token
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token response dictionary with access_token
        """
        # Use token cache so tokens/refresh tokens are persisted for future use
        cache = msal.SerializableTokenCache()
        if 'token_cache' in session:
            cache.deserialize(session['token_cache'])
            
        msal_app = self.get_msal_app(cache=cache)
        
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.sharepoint_scopes,
            redirect_uri=self.redirect_uri
        )
        
        # Save cache after token acquisition so refresh token is persisted
        if cache.has_state_changed:
            session['token_cache'] = cache.serialize()
        
        if "error" in result:
            logger.error(f"SharePoint token acquisition error: {result.get('error_description')}")
            return None
        
        return result
        
        return result
    
    def acquire_token_by_auth_code(self, code):
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token response dictionary
        """
        # Use token cache so tokens/refresh tokens are persisted for future use
        cache = msal.SerializableTokenCache()
        if 'token_cache' in session:
            cache.deserialize(session['token_cache'])
            
        msal_app = self.get_msal_app(cache=cache)
        
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        # Save cache after token acquisition so refresh token is persisted  
        if cache.has_state_changed:
            session['token_cache'] = cache.serialize()
        
        return result
    
    def get_token_from_cache(self):
        """
        Get token from cache or refresh if needed
        
        Returns:
            Access token string or None
        """
        account = session.get('account')
        if not account:
            return None
        
        msal_app = self.get_msal_app()
        
        # Try to get token silently (will use refresh token if needed)
        result = msal_app.acquire_token_silent(
            scopes=self.scopes,
            account=account
        )
        
        if result and "access_token" in result:
            # Update refresh token if a new one was issued
            if "refresh_token" in result:
                session['refresh_token'] = result['refresh_token']
            return result["access_token"]
        
        return None
    
    def get_app_only_token(self):
        """
        Get app-only access token using client credentials (application permissions)
        Uses Microsoft Graph API for SharePoint logging operations
        
        Returns:
            Access token string for app-only operations or None if acquisition fails
        """
        try:
            print("=== ACQUIRING APP-ONLY TOKEN FOR GRAPH API ===")
            print(f"Client ID: {self.client_id[:8]}...")
            print(f"Tenant ID: {self.tenant_id}")
            print(f"Authority: {self.authority}")
            
            msal_app = self.get_msal_app()
            
            # Use client credentials flow for application permissions
            # Use Graph API scope instead of SharePoint - more reliable!
            result = msal_app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            print(f"=== TOKEN RESULT KEYS: {result.keys() if result else 'None'} ===")
            
            if "access_token" in result:
                token_length = len(result["access_token"])
                print(f"=== GRAPH API APP-ONLY TOKEN ACQUIRED: {token_length} chars ===")
                logger.info(f"Successfully acquired app-only Graph token (length: {token_length})")
                return result["access_token"]
            else:
                error_desc = result.get('error_description', result.get('error', 'Unknown error'))
                error_code = result.get('error', 'no_error_code')
                print(f"=== APP-ONLY TOKEN ACQUISITION FAILED ===")
                print(f"Error Code: {error_code}")
                print(f"Error Description: {error_desc}")
                print(f"\nTo fix:")
                print(f"  1. Go to Azure Portal → Azure AD → App Registrations")
                print(f"  2. Select your app: {self.client_id}")
                print(f"  3. Go to 'API permissions'")
                print(f"  4. Add permission → Microsoft Graph → Application permissions")
                print(f"  5. Select 'Sites.ReadWrite.All'")
                print(f"  6. Click 'Grant admin consent' button")
                logger.error(f"Failed to acquire app-only token: {error_code} - {error_desc}")
                return None
                
        except Exception as e:
            print(f"=== EXCEPTION ACQUIRING APP-ONLY TOKEN: {str(e)} ===")
            import traceback
            traceback.print_exc()
            logger.error(f"Exception acquiring app-only token: {str(e)}")
            return None
    
    def get_sharepoint_token(self):
        """
        Get SharePoint-specific access token with automatic refresh
        Uses MSAL's acquire_token_silent, with fallback to refresh token if needed
        
        Returns:
            Access token for SharePoint API
        """
        sharepoint_token = session.get('sharepoint_access_token')
        if not sharepoint_token:
            return None
        
        account = session.get('account')
        if not account:
            return sharepoint_token
        
        # Try MSAL's built-in silent token acquisition (uses cache + refresh token)
        msal_app = self.get_msal_app()
        result = msal_app.acquire_token_silent(scopes=self.sharepoint_scopes, account=account)
        
        # If MSAL returned a new token, store it
        if result and "access_token" in result:
            session['sharepoint_access_token'] = result['access_token']
            if "refresh_token" in result:
                session['refresh_token'] = result['refresh_token']
            return result['access_token']
        
        # Fallback: If MSAL silent acquisition didn't work, try refresh token directly
        if not result or "access_token" not in result:
            refresh_token = session.get('refresh_token')
            if refresh_token:
                try:
                    result = msal_app.acquire_token_by_refresh_token(
                        refresh_token,
                        scopes=self.sharepoint_scopes
                    )
                    if result and "access_token" in result:
                        session['sharepoint_access_token'] = result['access_token']
                        if "refresh_token" in result:
                            session['refresh_token'] = result['refresh_token']
                        return result['access_token']
                except Exception:
                    pass  # If refresh fails, return existing token
        
        return sharepoint_token


    def get_user_groups(self):
        """
        Get current user's group memberships using Microsoft Graph API
        Requires User.Read.All or GroupMember.Read.All delegated permission
        
        Returns:
            list: List of group object IDs, or empty list on failure
        """
        try:
            account = session.get('account')
            if not account:
                logger.warning("No account in session - cannot fetch groups")
                return []
            
            # Get Graph API token with appropriate scopes
            msal_app = self.get_msal_app()
            result = msal_app.acquire_token_silent(
                scopes=["User.Read", "GroupMember.Read.All"],
                account=account
            )
            
            if not result or "access_token" not in result:
                logger.warning("Could not acquire Graph token for group lookup")
                return []
            
            # Fetch groups from Microsoft Graph
            return fetch_user_groups(result["access_token"])
            
        except Exception as e:
            logger.error(f"Error getting user groups: {str(e)}")
            return []


def login_required(f):
    """
    Decorator to protect routes that require authentication
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This requires login"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # Store the original URL to redirect back after login
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_user():
    """
    Get current logged-in user from session
    
    Returns:
        User dict with name, email, etc. or None
    """
    return session.get('user')


def check_group_membership(group_id=None):
    """
    Check if current user is a member of specified group
    
    Args:
        group_id: Azure AD group object ID. If None, uses AUTHORIZED_GROUP_ID from env
    
    Returns:
        bool: True if user is in the group, False otherwise
    """
    if not group_id:
        group_id = os.environ.get('AUTHORIZED_GROUP_ID')
    
    if not group_id:
        logger.warning("No AUTHORIZED_GROUP_ID configured - group check disabled")
        return True  # Fail open if not configured
    
    # Check cached group membership first
    user_groups = session.get('user_groups', [])
    return group_id in user_groups


def fetch_user_groups(access_token):
    """
    Fetch user's group memberships from Microsoft Graph API
    
    Args:
        access_token: Valid access token with GroupMember.Read.All permission
    
    Returns:
        list: List of group object IDs the user belongs to
    """
    import requests
    
    try:
        # Use Microsoft Graph to get user's group memberships
        graph_url = "https://graph.microsoft.com/v1.0/me/memberOf"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        print(f"=== FETCHING USER GROUPS FROM: {graph_url} ===")
        response = requests.get(graph_url, headers=headers)
        print(f"=== GRAPH API RESPONSE STATUS: {response.status_code} ===")
        
        if response.status_code == 200:
            data = response.json()
            # Extract group IDs from response
            groups = [group['id'] for group in data.get('value', []) 
                     if group.get('@odata.type') == '#microsoft.graph.group']
            print(f"=== SUCCESSFULLY FETCHED {len(groups)} GROUPS ===")
            if groups:
                print(f"=== GROUP IDs: {groups[:3]}{'...' if len(groups) > 3 else ''} ===")
            logger.info(f"User belongs to {len(groups)} groups")
            return groups
        else:
            error_text = response.text[:500]  # Limit error text length
            print(f"=== GRAPH API ERROR: {response.status_code} ===")
            print(f"=== ERROR DETAILS: {error_text} ===")
            logger.error(f"Failed to fetch groups: {response.status_code} - {error_text}")
            return []
            
    except Exception as e:
        print(f"=== EXCEPTION FETCHING GROUPS: {str(e)} ===")
        logger.error(f"Exception fetching user groups: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def group_required(f):
    """
    Decorator to protect routes that require group membership
    
    Usage:
        @app.route('/restricted')
        @group_required
        def restricted_route():
            return "This requires group membership"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is authenticated
        if not session.get('authenticated'):
            session['next_url'] = request.url
            return redirect(url_for('login'))
        
        # Then check group membership
        if not check_group_membership():
            logger.warning(f"Unauthorized access attempt by {session.get('user', {}).get('email')}")
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Access Denied</title>
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: #f5f5f5;
                        }
                        .container {
                            text-align: center;
                            background: white;
                            padding: 3rem;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        h1 { color: #d32f2f; margin-bottom: 1rem; }
                        p { color: #666; margin-bottom: 1.5rem; }
                        .user-info { 
                            background: #f5f5f5; 
                            padding: 1rem; 
                            border-radius: 4px;
                            margin-bottom: 1.5rem;
                            font-size: 0.9em;
                        }
                        a { 
                            color: #0066cc; 
                            text-decoration: none;
                            margin: 0 0.5rem;
                        }
                        a:hover { text-decoration: underline; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🔒 Access Denied</h1>
                        <p>You do not have permission to access this application.</p>
                        <div class="user-info">
                            Signed in as: <strong>{{ user.get('email', 'Unknown') }}</strong>
                        </div>
                        <p>If you believe you should have access, please contact:</p>
                        <p><strong>Your IT Team or Accounting VP</strong></p>
                        <p style="font-size: 0.9em; color: #999; margin-top: 2rem;">
                            <a href="/logout">Sign Out</a> | 
                            <a href="/">Return Home</a>
                        </p>
                    </div>
                </body>
                </html>
            """, user=session.get('user', {})), 403
        
        return f(*args, **kwargs)
    return decorated_function
