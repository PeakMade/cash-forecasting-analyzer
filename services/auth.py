"""
Azure AD Authentication Module
Handles user authentication via Microsoft identity platform
"""

import os
import logging
from functools import wraps
from flask import redirect, url_for, session, request
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
        
        # Use .default scope to get all configured API permissions in one token
        # This includes both Graph API (User.Read) and SharePoint access
        # configured in Azure AD app registration
        self.scopes = ["https://peakcampus.sharepoint.com/.default"]
        self.sharepoint_url = os.environ.get('SHAREPOINT_SITE_URL', 'https://peakcampus.sharepoint.com/sites/BaseCampApps')
    
    def get_msal_app(self, cache=None):
        """Create MSAL confidential client application with token cache"""
        # Use session-based token cache if available
        if cache is None and 'token_cache' in session:
            cache = msal.SerializableTokenCache()
            cache.deserialize(session['token_cache'])
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
            token_cache=cache
        )
        
        # Save cache back to session if it changed
        if cache and cache.has_state_changed:
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
        sharepoint_scopes = ["https://peakcampus.sharepoint.com/.default"]
        
        auth_url = msal_app.get_authorization_request_url(
            scopes=sharepoint_scopes,
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
        # Don't use cache - we'll store the token directly in the session
        msal_app = self.get_msal_app(cache=None)
        sharepoint_scopes = ["https://peakcampus.sharepoint.com/.default"]
        
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=sharepoint_scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            logger.error(f"SharePoint token acquisition error: {result.get('error_description')}")
            return None
        
        print(f"### SharePoint token acquired successfully")
        
        # Debug: decode token to check audience
        try:
            import base64
            import json
            token_parts = result['access_token'].split('.')
            if len(token_parts) >= 2:
                # Decode payload (add padding if needed)
                payload = token_parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)
                print(f"### Token audience (aud): {token_data.get('aud', 'N/A')}")
                print(f"### Token scopes (scp): {token_data.get('scp', 'N/A')}")
        except Exception as e:
            print(f"### Could not decode token: {e}")
        
        return result
    
    def acquire_token_by_auth_code(self, code):
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token response dictionary with access_token
        """
        msal_app = self.get_msal_app()
        
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            logger.error(f"Token acquisition error: {result.get('error_description')}")
            return None
        
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
    
    def get_sharepoint_token(self):
        """
        Get SharePoint-specific access token
        
        Returns:
            Access token for SharePoint API
        """
        # Check if we have a stored SharePoint token
        sharepoint_token = session.get('sharepoint_access_token')
        if sharepoint_token:
            print("### Returning stored SharePoint access token from session")
            return sharepoint_token
        
        print("### No SharePoint token in session")
        return None


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
