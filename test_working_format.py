"""
Test using the EXACT working connection code format
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# Use the SAME environment variable names as our app
server = os.getenv('DATABASE_SERVER')
database = os.getenv('DATABASE_NAME')
username = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')

print(f"Server: {server}")
print(f"Database: {database}")
print(f"Username: {username}")
print(f"Password: {'*' * len(password)}")
print("-" * 60)

# Use the EXACT connection string format from the working code
driver = 'SQL Server'
conn_str = f"DRIVER={{{driver}}};SERVER={server},1433;DATABASE={database};UID={username};PWD={password};Encrypt=no;TrustServerCertificate=yes;"

print(f"Connection string: {conn_str.replace(password, '***')}")
print("Connecting...")

try:
    conn = pyodbc.connect(conn_str, timeout=10)
    print("✓ Connected successfully!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM PROPERTY_0")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} properties")
    
    cursor.close()
    conn.close()
    print("✓✓✓ SUCCESS! ✓✓✓")
    
except Exception as e:
    print(f"✗ Error: {e}")
