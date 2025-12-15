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
        
        # Initial scopes - just request User.Read
        # MSAL automatically handles openid, profile, offline_access
        # SharePoint token will be acquired separately when needed
        self.scopes = ["User.Read"]
    
    def get_msal_app(self):
        """Create MSAL confidential client application"""
        return msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
    
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
        Get SharePoint-specific access token using on-behalf-of flow
        
        Returns:
            Access token for SharePoint API
        """
        account = session.get('account')
        if not account:
            logger.warning("No account in session for SharePoint token")
            return None
        
        msal_app = self.get_msal_app()
        
        # Request SharePoint-specific token with User.Read scope
        # Using AllSites.Read delegated permission
        sharepoint_scopes = ["https://peakcampus.sharepoint.com/AllSites.Read"]
        
        result = msal_app.acquire_token_silent(
            scopes=sharepoint_scopes,
            account=account
        )
        
        if result and "access_token" in result:
            return result["access_token"]
        
        # If silent fails, try to acquire new token
        if session.get('refresh_token'):
            result = msal_app.acquire_token_by_refresh_token(
                session['refresh_token'],
                scopes=sharepoint_scopes
            )
            
            if result and "access_token" in result:
                return result["access_token"]
        
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
