# SharePoint Integration Summary

## Overview
Successfully implemented SharePoint Online as an alternate data source for property information, with environment variable control to switch between SQL Server and SharePoint.

## Implementation Details

### 1. **Data Source Class** (`services/sharepoint_data_source.py`)
- **Purpose**: Access SharePoint Properties_0 list using Office365-REST-Python-Client
- **Authentication**: App-only authentication via ClientCredential (bypasses Conditional Access policies)
- **Methods Implemented**:
  - `get_property_info(property_identifier)`: Lookup property by ENTITY_NUMBER or PROPERTY_NAME
  - `list_all_properties()`: Get all reportable properties (FLAG_REPORTABLE = 1)
  - `test_connection()`: Validate SharePoint connectivity
- **Address Formatting**: Combines ADDRESS_1, ADDRESS_2 (if present), ADDRESS_CITY, ADDRESS_STATE with comma separation
- **Returns**: Same data structure as PropertyDatabase for seamless interoperability

### 2. **Factory Pattern** (`services/data_source_factory.py`)
- **Purpose**: Return appropriate data source based on configuration
- **Environment Variable**: `PROPERTY_DATA_SOURCE`
  - `"database"` (default): Returns PropertyDatabase (SQL Server)
  - `"sharepoint"`: Returns SharePointDataSource
- **Error Handling**: Raises ValueError for invalid configuration values

### 3. **Application Updates** (`app.py`)
- **Changed**: All 4 locations that instantiate PropertyDatabase
- **Routes Updated**:
  - `/upload` (line 190-191): Property lookup during file upload
  - `/test-db` (line 276-277): Database connection test
  - `/api/properties` (line 301-302): Property dropdown list
  - `/api/property/<entity_number>` (line 313-314): Property details API
- **Import Changed**: From `services.database import PropertyDatabase` → `services.data_source_factory import get_property_data_source`

### 4. **Dependencies**
- **Added to requirements.txt**: `Office365-REST-Python-Client==2.5.3`
- **Installed Locally**: Successfully installed in venv

### 5. **Environment Configuration** (`.env`)
New variables added:
```bash
# Property Data Source Configuration
PROPERTY_DATA_SOURCE=database  # or 'sharepoint'

# SharePoint Configuration (required if PROPERTY_DATA_SOURCE=sharepoint)
SHAREPOINT_SITE_URL=https://peakcampus.sharepoint.com/sites/BaseCampApps
SHAREPOINT_LIST_NAME=Properties_0
SHAREPOINT_CLIENT_ID=your-app-client-id
SHAREPOINT_CLIENT_SECRET=your-app-client-secret
```

### 6. **Setting Up SharePoint App Registration** (Required for Authentication)

To use SharePoint with Conditional Access policies, you need to register an Azure AD application:

1. **Register a new app in Azure AD**:
   - Go to Azure Portal → Azure Active Directory → App registrations → New registration
   - Name: "Cash Forecast Analyzer SharePoint Access"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Leave blank
   - Click "Register"

2. **Configure API Permissions**:
   - In your app, go to "API permissions" → Add a permission
   - Select "SharePoint" → Application permissions
   - Add: `Sites.Read.All` or `Sites.ReadWrite.All` (depending on needs)
   - Click "Grant admin consent" (requires admin)

3. **Create Client Secret**:
   - Go to "Certificates & secrets" → New client secret
   - Description: "Cash Forecast Analyzer"
   - Expires: Choose appropriate duration (recommend 12-24 months)
   - Copy the **Value** immediately (you won't see it again)

4. **Grant SharePoint Permissions**:
   - Copy your **Application (client) ID** from the Overview page
   - In SharePoint, an admin needs to grant the app access to the site:
     ```
     https://peakcampus.sharepoint.com/sites/BaseCampApps/_layouts/15/appinv.aspx
     ```
   - Enter the Client ID and click "Lookup"
   - In the Permission Request XML field, paste:
     ```xml
     <AppPermissionRequests AllowAppOnlyPolicy="true">
       <AppPermissionRequest Scope="http://sharepoint/content/sitecollection" Right="Read" />
     </AppPermissionRequests>
     ```
   - Click "Create" and then "Trust It"

5. **Update .env file**:
   - `SHAREPOINT_CLIENT_ID`: The Application (client) ID from step 3
   - `SHAREPOINT_CLIENT_SECRET`: The secret value from step 3

## Data Synchronization
- **Power Automate Flow**: Keeps SharePoint Properties_0 list synchronized with SQL Server PROPERTY_0 table
- **Column Structure**: Identical between SharePoint list and SQL Server table
- **Key Columns**: ENTITY_NUMBER, PROPERTY_NAME, ADDRESS_1, ADDRESS_2, ADDRESS_CITY, ADDRESS_STATE, ADDRESS_ZIP, SCHOOL_NAME, FLAG_REPORTABLE

## Testing Steps

### Local Testing
1. **Configure SharePoint App Credentials**:
   - Complete the App Registration steps above
   - Update `.env` with your `SHAREPOINT_CLIENT_ID` and `SHAREPOINT_CLIENT_SECRET`
   - Set `PROPERTY_DATA_SOURCE=sharepoint`

2. **Test SharePoint Connection**:
   - Start Flask app: `.\start.ps1`
   - Navigate to: `http://localhost:5000/test-db`
   - Should show SharePoint connection test results

3. **Test Property Dropdown**:
   - Open: `http://localhost:5000`
   - Check that property dropdown loads from SharePoint

4. **Compare Results**:
   - Test with `PROPERTY_DATA_SOURCE=database`
   - Test with `PROPERTY_DATA_SOURCE=sharepoint`
   - Verify identical property lists and details

### Azure Deployment
1. **Add Environment Variables** in Azure Portal:
   - Configuration → Application settings → New application setting
   - Add all SharePoint variables listed above
   - Set `PROPERTY_DATA_SOURCE=sharepoint` (or leave as `database` by default)

2. **Deploy Code**:
   ```powershell
   git add services/sharepoint_data_source.py services/data_source_factory.py app.py requirements.txt
   git commit -m "Add SharePoint as alternate property data source"
   git push
   ```

3. **Verify Deployment**:
   - Azure auto-deploys from GitHub
   - Check Azure Log stream for any errors
   - Test `/test-db` endpoint on Azure URL
   - Test property dropdown functionality

## Benefits
1. **Flexibility**: Easy switching between SQL Server and SharePoint via environment variable
2. **No Code Changes**: Toggle data sources without redeployment
3. **Same Interface**: Both data sources implement identical methods
4. **Future-Proof**: Easy to add additional data sources (e.g., Azure Cosmos DB, REST API)
5. **Power Automate Integration**: SharePoint list stays synchronized with SQL Server

## Next Steps
1. Fill in your SharePoint credentials in `.env`
2. Test locally with SharePoint data source
3. Deploy to Azure and configure environment variables
4. Consider implementing centralized authentication module (replacing username/password)
5. Monitor performance and add caching if needed

## Files Modified
- `requirements.txt`: Added Office365-REST-Python-Client==2.5.3
- `app.py`: Updated to use factory pattern (4 locations)
- `.env`: Added SharePoint configuration variables

## Files Created
- `services/sharepoint_data_source.py`: SharePoint data access class
- `services/data_source_factory.py`: Factory function for data source selection
- `SHAREPOINT_INTEGRATION.md`: This documentation file
