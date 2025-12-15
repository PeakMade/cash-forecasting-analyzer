"""
Test SQL Server connection with different username formats
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
print("-" * 60)

# Try different connection approaches
attempts = [
    {
        'name': 'Original username with @domain',
        'user': username,
    },
    {
        'name': 'Username without @domain',
        'user': username.split('@')[0] if '@' in username else username,
    },
    {
        'name': 'DOMAIN\\Username format',
        'user': username.replace('@', '\\').replace('.com', '') if '@' in username else username,
    },
]

for attempt in attempts:
    print(f"\nTrying: {attempt['name']}")
    print(f"  Username: {attempt['user']}")
    
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={attempt['user']};"
            f"PWD={password};"
        )
        
        conn = pyodbc.connect(conn_str, timeout=5)
        print("  ✓ SUCCESS! Connection established.")
        
        # Try a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"  SQL Server Version: {version[:80]}...")
        
        cursor.close()
        conn.close()
        print("\n" + "=" * 60)
        print("WORKING CONNECTION FOUND!")
        print(f"Use username: {attempt['user']}")
        print("=" * 60)
        break
        
    except Exception as e:
        print(f"  ✗ Failed: {str(e)[:100]}")

print("\nDone.")
