# Azure Database Connectivity Solutions

## Problem
Azure App Service cannot connect to on-premises SQL Server (`Atlsql03.corp.placeproperties.biz`) due to network isolation.

**Error**: `Login timeout expired (0) (SQLDriverConnect)`

## Root Cause
Azure App Service runs in Microsoft's cloud infrastructure and cannot directly access corporate network resources without additional configuration.

## Solutions

### Option 1: Use SharePoint Data Source (Recommended - Quickest)

**Pros**:
- No infrastructure changes needed
- Works immediately once app registration is complete
- Data already synchronized via Power Automate

**Steps**:
1. Complete SharePoint app registration (see `SHAREPOINT_INTEGRATION.md`)
2. In Azure Portal → Your App Service → Configuration → Application settings
3. Add/Update:
   ```
   PROPERTY_DATA_SOURCE = sharepoint
   SHAREPOINT_SITE_URL = https://peakcampus.sharepoint.com/sites/BaseCampApps
   SHAREPOINT_LIST_NAME = Properties_0
   SHAREPOINT_CLIENT_ID = <your-app-client-id>
   SHAREPOINT_CLIENT_SECRET = <your-app-client-secret>
   ```
4. Click "Save" and restart the app

---

### Option 2: Azure Hybrid Connection

**Pros**:
- Connects Azure App Service to on-premises resources
- No code changes needed
- SQL Server stays on-premises

**Cons**:
- Requires installing Hybrid Connection Manager on a server in your network
- Additional Azure configuration

**Steps**:
1. In Azure Portal → Your App Service → Networking → Hybrid connections
2. Add hybrid connection → Create new
3. Name: `sql-atlsql03-connection`
4. Endpoint Host: `Atlsql03.corp.placeproperties.biz`
5. Endpoint Port: `1433`
6. Download and install Hybrid Connection Manager on a Windows server in your network
7. Configure the connection in the HCM

**Documentation**: https://learn.microsoft.com/en-us/azure/app-service/app-service-hybrid-connections

---

### Option 3: Azure SQL Database

**Pros**:
- Native Azure connectivity (no timeouts)
- Better performance from Azure App Service
- Fully managed service

**Cons**:
- Requires database migration
- Ongoing Azure SQL Database costs
- Need to maintain data sync with on-premises

**Steps**:
1. Create Azure SQL Database
2. Migrate schema and data using Azure Data Migration Service
3. Set up data sync if needed (Azure SQL Data Sync)
4. Update connection string in App Service configuration

---

### Option 4: Point-to-Site VPN

**Pros**:
- Full network connectivity to corporate resources
- Can access multiple resources

**Cons**:
- More complex setup
- Requires Azure VNet integration
- Higher cost

**Steps**:
1. Create Azure Virtual Network
2. Configure VNet integration for App Service
3. Set up Point-to-Site VPN from VNet to corporate network
4. Configure DNS for name resolution

---

## Temporary Workaround

While setting up one of the above solutions, you can:

1. Keep local development using `PROPERTY_DATA_SOURCE=database`
2. Use SharePoint in production once app registration is complete
3. Properties data stays synchronized via Power Automate flow

## Current Status

- **Local Development**: Uses SQL Server (working ✓)
- **Production (Azure)**: Connection timeout - needs one of the solutions above

## Recommendation

**For immediate production fix**: Use SharePoint (Option 1)
- Fastest to implement
- No infrastructure changes
- Already have the code ready

**For long-term**: Consider Azure Hybrid Connection (Option 2) or Azure SQL Database (Option 3) depending on:
- Security requirements
- Performance needs
- Budget constraints
- IT infrastructure strategy
