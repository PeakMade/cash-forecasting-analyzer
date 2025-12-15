"""
Minimal connection test
"""
import pyodbc

# Direct values for testing
server = "Atlsql03.corp.placeproperties.biz"
database = "DW_APP_SUPPORT"
username = "boadmin"
password = "Boad00!!"

print(f"Testing connection...")
print(f"Server: {server}")
print(f"Database: {database}")
print(f"Username: {username}")
print("-" * 60)

try:
    # Simplest possible connection string
    conn_str = f"DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password};"
    
    print(f"Connection string: {conn_str.replace(password, '***')}")
    print("Connecting...")
    
    conn = pyodbc.connect(conn_str, timeout=10)
    print("✓ Connected successfully!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE()")
    result = cursor.fetchone()
    print(f"✓ Query executed: Current datetime = {result[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM PROPERTY_0")
    count = cursor.fetchone()[0]
    print(f"✓ PROPERTY_0 table access: {count} rows found")
    
    cursor.close()
    conn.close()
    print("\n✓✓✓ ALL TESTS PASSED! ✓✓✓")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nPossible issues:")
    print("  1. Wrong password")
    print("  2. User doesn't have access to this database")
    print("  3. Network/firewall blocking connection")
    print("  4. Server name incorrect")
