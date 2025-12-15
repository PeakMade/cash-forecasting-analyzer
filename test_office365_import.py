"""Test script to find correct office365 imports"""

try:
    from office365.sharepoint.caml.caml_query import CamlQuery
    print("SUCCESS: from office365.sharepoint.caml.caml_query import CamlQuery")
except ImportError as e:
    print(f"FAILED caml.caml_query: {e}")

try:
    from office365.sharepoint.caml_query import CamlQuery
    print("SUCCESS: from office365.sharepoint.caml_query import CamlQuery")
except ImportError as e:
    print(f"FAILED caml_query: {e}")

try:
    # Try getting items without CamlQuery
    from office365.sharepoint.client_context import ClientContext
    print("ClientContext imported successfully")
    print(f"ClientContext methods: {[m for m in dir(ClientContext) if not m.startswith('_')][:10]}")
except ImportError as e:
    print(f"FAILED ClientContext: {e}")

# Check what's in the office365 package
import office365.sharepoint as sp
print(f"\nAvailable in office365.sharepoint: {[m for m in dir(sp) if not m.startswith('_')]}")
