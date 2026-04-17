"""
SharePoint Data Source Service
Connects to SharePoint Online list for property data lookup
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import CamlQuery
from office365.runtime.auth.token_response import TokenResponse

logger = logging.getLogger(__name__)


class SharePointDataSource:
    """Handle SharePoint Online connections and property data queries"""
    
    def __init__(self, access_token: Optional[str] = None, app_only_token: Optional[str] = None):
        """
        Initialize SharePoint data source with dual authentication
        
        Args:
            access_token: User's access token for delegated authentication (reading data)
            app_only_token: Application's token for app-only operations (logging)
        """
        self.site_url = os.environ.get('SHAREPOINT_SITE_URL', '')
        self.list_name = os.environ.get('SHAREPOINT_LIST_NAME', 'Properties_0')
        self.log_list_name = os.environ.get('SHAREPOINT_LOG_LIST_NAME', 'Innovation Use Log')
        self.access_token = access_token
        self.app_only_token = app_only_token
        self._logging_available = None  # Cache whether logging list exists
        
        # Cache for Graph API logging
        self._graph_site_id = None
        self._graph_list_id = None
        
        if not self.site_url:
            raise ValueError("SHAREPOINT_SITE_URL is required")
    
    def _get_context(self) -> ClientContext:
        """
        Create SharePoint client context with user token
        Uses delegated permissions via logged-in user's access token
        
        Returns:
            ClientContext object for SharePoint operations
        """
        try:
            if not self.access_token:
                raise ValueError("Access token required for SharePoint authentication")
            
            # Create client context with access token
            # with_access_token() expects a callable that returns a TokenResponse object
            def token_provider():
                token = TokenResponse()
                token.accessToken = self.access_token
                token.tokenType = "Bearer"
                return token
            
            ctx = ClientContext(self.site_url).with_access_token(token_provider)
            
            logger.debug(f"Connected to SharePoint using user token: {self.site_url}")
            return ctx
        except Exception as e:
            logger.error(f"SharePoint connection error: {str(e)}")
            raise
    
    def _get_app_context(self) -> ClientContext:
        """
        Create SharePoint client context with app-only token
        Uses application permissions - app acts as itself, not as user
        Used for logging operations to prevent users from needing SharePoint permissions
        
        Returns:
            ClientContext object for SharePoint operations
        """
        try:
            if not self.app_only_token:
                raise ValueError("App-only token required for application operations")
            
            # Create client context with app-only token
            def token_provider():
                token = TokenResponse()
                token.accessToken = self.app_only_token
                token.tokenType = "Bearer"
                return token
            
            ctx = ClientContext(self.site_url).with_access_token(token_provider)
            
            logger.debug(f"Connected to SharePoint using app-only token: {self.site_url}")
            return ctx
        except Exception as e:
            logger.error(f"SharePoint app-only connection error: {str(e)}")
            raise
    
    def get_property_info(self, property_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Lookup property details by ENTITY_NUMBER or PROPERTY_NAME
        
        Args:
            property_identifier: ENTITY_NUMBER (preferred) or PROPERTY_NAME
            
        Returns:
            Dictionary with property details or None if not found
        """
        try:
            print(f"=== SHAREPOINT QUERY START ===")
            print(f"Looking for property_identifier: {property_identifier}")
            print(f"Type: {type(property_identifier)}")
            
            ctx = self._get_context()
            
            # Get the list
            sp_list = ctx.web.lists.get_by_title(self.list_name)
            
            # Determine if property_identifier is numeric (entity number) or text (property name)
            is_numeric = property_identifier.isdigit()
            
            # Use filter instead of CAML query for more reliable results
            if is_numeric:
                # Filter by ENTITY_NUMBER
                filter_expr = f"ENTITY_NUMBER eq {property_identifier}"
                print(f"=== USING FILTER: {filter_expr} ===")
                items = sp_list.items.filter(filter_expr).top(1).get().execute_query()
            else:
                # Filter by PROPERTY_NAME
                filter_expr = f"PROPERTY_NAME eq '{property_identifier}'"
                print(f"=== USING FILTER: {filter_expr} ===")
                items = sp_list.items.filter(filter_expr).top(1).get().execute_query()
            
            print(f"=== FILTER RETURNED {len(items)} ITEMS ===")
            
            if len(items) == 0:
                print(f"=== NO ITEMS FOUND FOR: {property_identifier} ===")
                logger.warning(f"Property not found in SharePoint: {property_identifier}")
                return None
            
            if len(items) > 0:
                print(f"First item ENTITY_NUMBER: {items[0].properties.get('ENTITY_NUMBER')}")
                print(f"First item PROPERTY_NAME: {items[0].properties.get('PROPERTY_NAME')}")
                
                # CRITICAL: Verify we got the right record
                entity_match = str(items[0].properties.get('ENTITY_NUMBER')) == str(property_identifier)
                name_match = items[0].properties.get('PROPERTY_NAME') == property_identifier
                
                if not (entity_match or name_match):
                    print(f"=== WARNING: Query returned wrong property! ===")
                    print(f"Requested: {property_identifier}")
                    print(f"Got ENTITY_NUMBER: {items[0].properties.get('ENTITY_NUMBER')}")
                    print(f"Got PROPERTY_NAME: {items[0].properties.get('PROPERTY_NAME')}")
                    logger.error(f"SharePoint query returned wrong property. Requested: {property_identifier}, Got: {items[0].properties.get('ENTITY_NUMBER')}")
                    return None
                item = items[0].properties
                
                # Format the address: ADDRESS_1[, ADDRESS_2], ADDRESS_CITY, ADDRESS_STATE
                address_parts = []
                if item.get('ADDRESS_1'):
                    address_parts.append(item.get('ADDRESS_1').strip())
                if item.get('ADDRESS_2') and item.get('ADDRESS_2').strip():
                    address_parts.append(item.get('ADDRESS_2').strip())
                if item.get('ADDRESS_CITY'):
                    address_parts.append(item.get('ADDRESS_CITY').strip())
                if item.get('ADDRESS_STATE'):
                    address_parts.append(item.get('ADDRESS_STATE').strip())
                
                formatted_address = ', '.join(address_parts)
                
                return {
                    'entity_number': item.get('ENTITY_NUMBER', ''),
                    'property_name': item.get('PROPERTY_NAME', ''),
                    'address': formatted_address,
                    'city': item.get('ADDRESS_CITY', '').strip() if item.get('ADDRESS_CITY') else '',
                    'state': item.get('ADDRESS_STATE', '').strip() if item.get('ADDRESS_STATE') else '',
                    'zip_code': item.get('ADDRESS_ZIP', ''),
                    'university': item.get('SCHOOL_NAME', '')
                }
            else:
                logger.warning(f"Property not found in SharePoint: {property_identifier}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying SharePoint property: {str(e)}")
            raise
    
    def list_all_properties(self) -> List[Dict[str, str]]:
        """
        Get list of all reportable properties for dropdown
        Filters by FLAG_REPORTABLE = 1
        
        Returns:
            List of dictionaries with entity_number and property_name
        """
        try:
            ctx = self._get_context()
            
            # Get the list
            sp_list = ctx.web.lists.get_by_title(self.list_name)
            
            # Query for reportable properties
            caml_query_xml = """
                <View>
                    <Query>
                        <Where>
                            <Eq>
                                <FieldRef Name='FLAG_REPORTABLE'/>
                                <Value Type='Boolean'>1</Value>
                            </Eq>
                        </Where>
                        <OrderBy>
                            <FieldRef Name='PROPERTY_NAME' Ascending='TRUE'/>
                        </OrderBy>
                    </Query>
                </View>
            """
            
            caml_query = CamlQuery.parse(caml_query_xml)
            items = sp_list.get_items(caml_query).execute_query()
            
            properties = [
                {
                    'entity_number': item.properties.get('ENTITY_NUMBER', ''),
                    'property_name': item.properties.get('PROPERTY_NAME', '')
                }
                for item in items
            ]
            
            # Sort by property name (in case CAML OrderBy doesn't work)
            properties.sort(key=lambda x: x['property_name'].upper() if x['property_name'] else '')
            
            logger.info(f"Retrieved {len(properties)} reportable properties from SharePoint")
            return properties
            
        except Exception as e:
            logger.error(f"Error listing SharePoint properties: {str(e)}")
            raise
    
    def _get_graph_site_id(self, graph_token: str) -> Optional[str]:
        """
        Resolve SharePoint site ID via Microsoft Graph API
        Caches the result for subsequent calls
        
        Args:
            graph_token: Microsoft Graph access token
            
        Returns:
            SharePoint site ID or None if resolution fails
        """
        if self._graph_site_id:
            return self._graph_site_id
        
        try:
            # Parse site URL to get host and path
            # e.g., https://peakcampus.sharepoint.com/sites/BaseCampApps
            from urllib.parse import urlparse
            parsed = urlparse(self.site_url)
            host = parsed.netloc  # e.g., peakcampus.sharepoint.com
            path = parsed.path    # e.g., /sites/BaseCampApps
            
            # Query Graph API for site ID
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{host}:{path}"
            headers = {
                'Authorization': f'Bearer {graph_token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()
            
            site_data = response.json()
            self._graph_site_id = site_data.get('id')
            
            logger.info(f"Resolved SharePoint site ID via Graph: {self._graph_site_id}")
            return self._graph_site_id
            
        except Exception as e:
            logger.error(f"Failed to resolve SharePoint site ID: {str(e)}")
            return None
    
    def _get_graph_list_id(self, graph_token: str, site_id: str) -> Optional[str]:
        """
        Resolve SharePoint list ID via Microsoft Graph API
        Caches the result for subsequent calls
        
        Args:
            graph_token: Microsoft Graph access token
            site_id: SharePoint site ID
            
        Returns:
            SharePoint list ID or None if resolution fails
        """
        if self._graph_list_id:
            return self._graph_list_id
        
        try:
            # Query Graph API for list by display name
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
            headers = {
                'Authorization': f'Bearer {graph_token}',
                'Accept': 'application/json'
            }
            params = {
                '$filter': f"displayName eq '{self.log_list_name}'"
            }
            
            response = requests.get(graph_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            lists = data.get('value', [])
            
            if not lists:
                logger.error(f"SharePoint list '{self.log_list_name}' not found")
                return None
            
            self._graph_list_id = lists[0].get('id')
            logger.info(f"Resolved SharePoint list ID via Graph: {self._graph_list_id}")
            return self._graph_list_id
            
        except Exception as e:
            logger.error(f"Failed to resolve SharePoint list ID: {str(e)}")
            return None
    
    def _log_via_graph(self, user_email: str, user_name: str, activity_type: str,
                      property_name: Optional[str], file_names: Optional[str],
                      application: str, environment: str, session_id: Optional[str],
                      status: Optional[str] = None, status_reason: Optional[str] = None) -> bool:
        """
        Log activity to SharePoint via Microsoft Graph API (app-only)
        This is more reliable than SharePoint REST API
        
        Args:
            user_email: User's email address
            user_name: User's display name
            activity_type: Type of activity
            property_name: Optional property name
            file_names: Optional file names
            application: Application name
            environment: Environment name
            session_id: Session ID
            status: Optional recommendation status
            status_reason: Optional recommendation amount
            
        Returns:
            True if logging successful, False otherwise
        """
        if not self.app_only_token:
            logger.warning("No app-only token available for Graph API logging")
            return False
        
        try:
            # Get site ID
            site_id = self._get_graph_site_id(self.app_only_token)
            if not site_id:
                return False
            
            # Get list ID
            list_id = self._get_graph_list_id(self.app_only_token, site_id)
            if not list_id:
                self._logging_available = False
                return False
            
            # Create log entry
            log_entry = {
                'fields': {
                    'Title': user_email,  # SharePoint requires Title field
                    'UserEmail': user_email,
                    'UserName': user_name,
                    'LoginTimestamp': datetime.utcnow().isoformat() + 'Z',
                    'UserRole': 'user',
                    'ActivityType': activity_type,
                    'Application': application,
                    'Env': environment
                }
            }
            
            # Add optional fields
            if session_id:
                log_entry['fields']['SessionID'] = session_id
            if property_name:
                log_entry['fields']['PropertyName'] = property_name
            if file_names:
                log_entry['fields']['FileNames'] = file_names
            if status:
                log_entry['fields']['Status'] = status
            if status_reason:
                log_entry['fields']['StatusReason'] = status_reason
            
            # Post to Graph API
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items"
            headers = {
                'Authorization': f'Bearer {self.app_only_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(graph_url, json=log_entry, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully logged activity via Graph: {activity_type} for {user_email}")
            self._logging_available = True
            return True
            
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_msg = e.response.text if e.response else str(e)
            
            print(f"=== GRAPH API LOGGING ERROR: HTTP {status_code} ===")
            print(f"=== Error: {error_msg} ===")
            
            if status_code == 404:
                logger.error(f"SharePoint list '{self.log_list_name}' not found via Graph API")
                self._logging_available = False
            elif status_code in [401, 403]:
                logger.error(f"Graph API returned {status_code} - check Azure AD app permissions")
                print(f"=== Ensure 'Sites.ReadWrite.All' application permission is granted in Azure AD ===")
            else:
                logger.error(f"Graph API logging failed: {error_msg}")
            
            return False
            
        except Exception as e:
            logger.error(f"Exception during Graph API logging: {str(e)}")
            print(f"=== GRAPH API EXCEPTION: {str(e)} ===")
            import traceback
            traceback.print_exc()
            return False
    
    def log_activity(self, user_email: str, user_name: str, activity_type: str, 
                    property_name: str = None, file_names: str = None, 
                    application: str = 'CashForecastAnalyzer', environment: str = 'Prod',
                    session_id: str = None, status: str = None, status_reason: str = None) -> bool:
        """
        Log user activity to Innovation Use Log SharePoint list
        Uses Microsoft Graph API with app-only token (more reliable than SharePoint REST)
        
        Args:
            user_email: User's email address
            user_name: User's display name
            activity_type: Type of activity (e.g., 'Start Session', 'End Session', 'analysis_successful', 'analysis_failed')
            property_name: Optional property name for analysis activities
            file_names: Optional comma-separated list of uploaded filenames
            application: Application name (default: 'CashForecastAnalyzer')
            environment: Environment name (default: 'Prod', use 'Local' for local development)
            session_id: Session ID for tracking activities within the same session
            status: Optional recommendation status (e.g., 'Distribute', 'Contribute', 'Do Nothing')
            status_reason: Optional recommendation amount (e.g., '$500,000.00' or '$0.00')
            
        Returns:
            True if logging successful, False otherwise
        """
        # Skip if we've already determined logging is unavailable for this instance
        if self._logging_available is False:
            return False
        
        # Use app-only token for logging (app writes as itself, not as user)
        if not self.app_only_token:
            logger.warning("No app-only token available for logging. Skipping activity log.")
            print("=== WARNING: No app-only token for logging ===")
            return False
        
        # Use Graph API for logging (more reliable than SharePoint REST)
        print(f"=== LOGGING ACTIVITY VIA GRAPH API: {activity_type} for {user_email} ===")
        return self._log_via_graph(
            user_email=user_email,
            user_name=user_name,
            activity_type=activity_type,
            property_name=property_name,
            file_names=file_names,
            application=application,
            environment=environment,
            session_id=session_id,
            status=status,
            status_reason=status_reason
        )
    
    def test_connection(self) -> bool:
        """
        Test SharePoint connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            ctx = self._get_context()
            # Try to get the list to verify connection
            ctx.web.lists.get_by_title(self.list_name).get().execute_query()
            logger.info("SharePoint connection test successful")
            return True
        except Exception as e:
            logger.error(f"SharePoint connection test failed: {str(e)}")
            return False
