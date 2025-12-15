"""
Check available ODBC drivers on this system
"""
import pyodbc

print("Available ODBC Drivers:")
print("-" * 50)
drivers = pyodbc.drivers()
if drivers:
    for driver in drivers:
        print(f"  - {driver}")
else:
    print("  No ODBC drivers found!")

print("\n" + "=" * 50)
print("SQL Server drivers needed:")
print("  - ODBC Driver 17 for SQL Server (recommended)")
print("  - ODBC Driver 18 for SQL Server (newest)")
print("\nDownload from:")
print("  https://go.microsoft.com/fwlink/?linkid=2249004")
print("=" * 50)
