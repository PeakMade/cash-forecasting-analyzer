"""
Test Windows Authentication (Trusted Connection)
"""
import pyodbc

server = "Atlsql03.corp.placeproperties.biz"
database = "DW_APP_SUPPORT"

print(f"Testing Windows Authentication (Trusted Connection)...")
print(f"Server: {server}")
print(f"Database: {database}")
print("-" * 60)

try:
    # Try Windows Authentication / Trusted Connection
    conn_str = f"DRIVER=SQL Server;SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    
    print(f"Connection string: {conn_str}")
    print("Connecting with Windows Authentication...")
    
    conn = pyodbc.connect(conn_str, timeout=10)
    print("✓ Connected successfully!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE(), SYSTEM_USER")
    result = cursor.fetchone()
    print(f"✓ Query executed: Current datetime = {result[0]}")
    print(f"✓ Connected as: {result[1]}")
    
    cursor.execute("SELECT COUNT(*) FROM PROPERTY_0")
    count = cursor.fetchone()[0]
    print(f"✓ PROPERTY_0 table access: {count} rows found")
    
    cursor.close()
    conn.close()
    print("\n✓✓✓ WINDOWS AUTHENTICATION WORKS! ✓✓✓")
    print("\nWe should use Windows Authentication (Trusted_Connection) instead of SQL Auth!")
    
except Exception as e:
    print(f"\n✗ Windows Authentication failed: {e}")
    print("\nTrying with Integrated Security parameter...")
    
    try:
        conn_str = f"DRIVER=SQL Server;SERVER={server};DATABASE={database};Integrated Security=SSPI;"
        conn = pyodbc.connect(conn_str, timeout=10)
        print("✓ Connected with Integrated Security!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT SYSTEM_USER")
        user = cursor.fetchone()[0]
        print(f"✓ Connected as: {user}")
        
        cursor.close()
        conn.close()
        print("\n✓✓✓ INTEGRATED SECURITY WORKS! ✓✓✓")
        
    except Exception as e2:
        print(f"\n✗ Integrated Security also failed: {e2}")
        print("\nThis suggests the SQL authentication credentials may need to be verified with your DBA.")
