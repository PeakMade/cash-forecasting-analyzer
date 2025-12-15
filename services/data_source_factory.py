"""
Data Source Factory
Returns appropriate property data source based on environment configuration
"""

import os
from services.database import PropertyDatabase
from services.sharepoint_data_source import SharePointDataSource


def get_property_data_source():
    """
    Factory function to get the configured property data source
    
    Returns:
        PropertyDatabase or SharePointDataSource instance based on PROPERTY_DATA_SOURCE env var
        
    Raises:
        ValueError: If PROPERTY_DATA_SOURCE has an invalid value
    """
    source_type = os.environ.get('PROPERTY_DATA_SOURCE', 'database').lower()
    
    if source_type == 'sharepoint':
        return SharePointDataSource()
    elif source_type == 'database':
        return PropertyDatabase()
    else:
        raise ValueError(
            f"Invalid PROPERTY_DATA_SOURCE: '{source_type}'. "
            "Valid values: 'database', 'sharepoint'"
        )
