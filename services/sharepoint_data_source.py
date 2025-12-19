"""
SharePoint Data Source Service
Connects to SharePoint Online list for property data lookup
"""

import os
import logging
from typing import Dict, Any, Optional, List
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import CamlQuery
from office365.runtime.auth.token_response import TokenResponse

logger = logging.getLogger(__name__)


class SharePointDataSource:
    """Handle SharePoint Online connections and property data queries"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize SharePoint data source
        
        Args:
            access_token: User's access token for delegated authentication
        """
        self.site_url = os.environ.get('SHAREPOINT_SITE_URL', '')
        self.list_name = os.environ.get('SHAREPOINT_LIST_NAME', 'Properties_0')
        self.access_token = access_token
        
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
            
            print(f"=== CREATING SHAREPOINT CONTEXT ===")
            print(f"Site URL: {self.site_url}")
            print(f"Access token length: {len(self.access_token)}")
            print(f"Access token starts with: {self.access_token[:50]}...")
            
            # Create client context with access token
            # with_access_token() expects a callable that returns a TokenResponse object
            def token_provider():
                token = TokenResponse()
                token.accessToken = self.access_token
                token.tokenType = "Bearer"
                return token
            
            ctx = ClientContext(self.site_url).with_access_token(token_provider)
            
            print(f"=== CONTEXT CREATED SUCCESSFULLY ===")
            
            logger.debug(f"Connected to SharePoint using user token: {self.site_url}")
            return ctx
        except Exception as e:
            logger.error(f"SharePoint connection error: {str(e)}")
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
            ctx = self._get_context()
            
            # Get the list
            sp_list = ctx.web.lists.get_by_title(self.list_name)
            
            # Query for the property - try both ENTITY_NUMBER and PROPERTY_NAME
            caml_query_xml = f"""
                <View>
                    <Query>
                        <Where>
                            <Or>
                                <Eq>
                                    <FieldRef Name='ENTITY_NUMBER'/>
                                    <Value Type='Text'>{property_identifier}</Value>
                                </Eq>
                                <Eq>
                                    <FieldRef Name='PROPERTY_NAME'/>
                                    <Value Type='Text'>{property_identifier}</Value>
                                </Eq>
                            </Or>
                        </Where>
                    </Query>
                    <RowLimit>1</RowLimit>
                </View>
            """
            
            caml_query = CamlQuery.parse(caml_query_xml)
            items = sp_list.get_items(caml_query).execute_query()
            
            if len(items) > 0:
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
