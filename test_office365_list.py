"""Test script to find CamlQuery in office365"""

try:
    from office365.sharepoint.lists import list as sp_list
    print(f"List module contents: {[m for m in dir(sp_list) if not m.startswith('_')]}")
except Exception as e:
    print(f"Error importing list: {e}")

try:
    from office365.sharepoint.lists.list import List
    print(f"List class methods: {[m for m in dir(List) if 'query' in m.lower() or 'items' in m.lower()]}")
except Exception as e:
    print(f"Error importing List: {e}")

# Check if there's a caml module
try:
    import office365.sharepoint.lists
    print(f"\nLists module contents: {dir(office365.sharepoint.lists)}")
except Exception as e:
    print(f"Error: {e}")
