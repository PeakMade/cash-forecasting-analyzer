"""
Test SQL Server connection with different parameters
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

server = os.environ.get('DATABASE_SERVER')
database = os.environ.get('DATABASE_NAME')
username = os.environ.get('DATABASE_USER')
password = os.environ.get('DATABASE_PASSWORD')

print(f"Testing connection to: {server}/{database}")
print(f"Username: {username}")
print(f"Available drivers: {pyodbc.drivers()}")
print("-" * 60)

# Try different connection string variations
connection_strings = [
    {
        'name': 'Basic SQL Server driver',
        'conn_str': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
    },
    {
        'name': 'SQL Server with Network Library',
        'conn_str': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Network Library=DBMSSOCN;"
    },
    {
        'name': 'SQL Server with Port 1433',
        'conn_str': f"DRIVER={{SQL Server}};SERVER={server},1433;DATABASE={database};UID={username};PWD={password};"
    },
    {
        'name': 'SQL Server with Encrypt=no',
        'conn_str': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;"
    },
    {
        'name': 'SQL Server with TrustServerCertificate',
        'conn_str': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    },
]

for test in connection_strings:
    print(f"\nTrying: {test['name']}")
    
    try:
        conn = pyodbc.connect(test['conn_str'], timeout=10)
        print("  ✓ SUCCESS! Connection established.")
        
        # Try a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PROPERTY_0")
        count = cursor.fetchone()[0]
        print(f"  Properties in database: {count}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("WORKING CONNECTION FOUND!")
        print(f"Connection string: {test['conn_str']}")
        print("=" * 60)
        break
        
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 150:
            error_msg = error_msg[:150] + "..."
        print(f"  ✗ Failed: {error_msg}")

print("\nDone.")
