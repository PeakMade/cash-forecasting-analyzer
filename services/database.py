"""
Database Service
SQL Server connection for property data lookup
"""

import os
import logging
import pyodbc
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class PropertyDatabase:
    """Handle SQL Server connections and property data queries"""
    
    def __init__(self):
        self.server = os.environ.get('DATABASE_SERVER', 'Atlsql03.corp.placeproperties.biz')
        self.database = os.environ.get('DATABASE_NAME', 'DW_APP_SUPPORT')
        self.username = os.environ.get('DATABASE_USER', '')
        self.password = os.environ.get('DATABASE_PASSWORD', '')
        
    def _get_connection(self):
        """
        Create a new database connection for each request
        This prevents stale connection issues
        """
        try:
            # Try multiple ODBC driver versions in order of preference
            drivers = [
                'ODBC Driver 18 for SQL Server',
                'ODBC Driver 17 for SQL Server',
                'ODBC Driver 13 for SQL Server',
                'SQL Server Native Client 11.0',
                'SQL Server'
            ]
            
            # Find available driver
            available_drivers = [d for d in pyodbc.drivers() if any(driver in d for driver in drivers)]
            
            if not available_drivers:
                raise Exception(
                    "No SQL Server ODBC driver found. "
                    "Please install 'ODBC Driver 17 for SQL Server' or newer. "
                    f"Available drivers: {pyodbc.drivers()}"
                )
            
            driver = available_drivers[0]
            
            # Build connection string - compatible with older drivers
            # Using semicolon-separated format that works with SQL Server authentication
            connection_params = {
                'DRIVER': driver,
                'SERVER': self.server,
                'DATABASE': self.database,
                'UID': self.username,
                'PWD': self.password,
            }
            
            # Build connection string manually to ensure proper formatting
            connection_string = ';'.join([f'{k}={v}' for k, v in connection_params.items()]) + ';'
            
            connection = pyodbc.connect(connection_string, timeout=30)
            logger.debug(f"Connected to SQL Server: {self.server}/{self.database}")
            return connection
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    def get_property_info(self, property_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Lookup property details by ENTITY_NUMBER, PROPERTY_NAME, or other identifier
        
        Args:
            property_identifier: ENTITY_NUMBER (preferred), PROPERTY_NAME, or other identifier
            
        Returns:
            Dictionary with property details or None if not found
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ENTITY_NUMBER,
                    PROPERTY_NAME,
                    ADDRESS_1,
                    ADDRESS_2,
                    ADDRESS_CITY,
                    ADDRESS_STATE,
                    ADDRESS_ZIP,
                    SCHOOL_NAME
                FROM PROPERTY_0
                WHERE ENTITY_NUMBER = ?
                   OR PROPERTY_NAME = ?
            """
            
            cursor.execute(query, (property_identifier, property_identifier))
            row = cursor.fetchone()
            
            if row:
                # Format the address: ADDRESS_1[, ADDRESS_2], ADDRESS_CITY, ADDRESS_STATE
                address_parts = []
                if row[2]:  # ADDRESS_1
                    address_parts.append(row[2].strip())
                if row[3] and row[3].strip():  # ADDRESS_2 (only if populated)
                    address_parts.append(row[3].strip())
                if row[4]:  # ADDRESS_CITY
                    address_parts.append(row[4].strip())
                if row[5]:  # ADDRESS_STATE
                    address_parts.append(row[5].strip())
                
                formatted_address = ', '.join(address_parts)
                
                return {
                    'entity_number': row[0],
                    'property_name': row[1],
                    'address': formatted_address,
                    'city': row[4].strip() if row[4] else '',
                    'state': row[5].strip() if row[5] else '',
                    'zip_code': row[6],
                    'university': row[7]
                }
            else:
                logger.warning(f"Property not found: {property_identifier}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying property: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def list_all_properties(self) -> List[Dict[str, str]]:
        """
        Get list of all reportable properties for dropdown
        Filters by FLAG_REPORTABLE = 1
        
        Returns:
            List of dictionaries with entity_number and property_name
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ENTITY_NUMBER,
                    PROPERTY_NAME
                FROM PROPERTY_0
                WHERE FLAG_REPORTABLE = 1
                ORDER BY PROPERTY_NAME
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            properties = [
                {'entity_number': row[0], 'property_name': row[1]}
                for row in rows
            ]
            
            logger.info(f"Retrieved {len(properties)} reportable properties from database")
            return properties
            
        except Exception as e:
            logger.error(f"Error listing properties: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
