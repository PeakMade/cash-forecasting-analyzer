---
title: Group-Based Access Control Setup Guide
description: Restrict app access to specific Entra ID (Azure AD) security groups
tags: [security, authorization, entra-id, azure-ad, groups, rbac]
category: Security
audience: administrators, developers
last_updated: 2026-05-06
---

# Group-Based Access Control Setup Guide

## Overview

This guide explains how to restrict access to the Cash Forecast Analyzer application using Entra ID (Azure AD) security groups. Only users who are members of designated groups will be able to access the application.

## Quick Reference

### New Decorator
```python
from services.auth import group_required

@app.route('/analyze')
@group_required  # Replaces @login_required for restricted access
def analyze():
    # Only authorized group members can access this
    return render_template('analyze.html')
```

### Key Features
- ✅ **Group-based authorization** - Only specific groups can access
- ✅ **Flexible configuration** - Control via environment variable
- ✅ **Graceful error pages** - Users see friendly "Access Denied" message
- ✅ **Backward compatible** - `@login_required` still works for basic auth
- ✅ **Caching** - Group memberships cached in session for performance

---

## Implementation Steps

### Step 1: Create Security Group in Entra ID

1. **Navigate to Azure Portal**
   - Go to: https://portal.azure.com
   - Select: **Azure Active Directory** → **Groups**

2. **Create New Group**
   - Click: **New group**
   - Settings:
     - **Group type**: Security
     - **Group name**: `CashForecastAnalyzer-Users`
     - **Group description**: "Users authorized to access Cash Forecast Analyzer"
     - **Membership type**: Assigned (or Dynamic if you have Azure AD Premium)
   - Click: **Create**

3. **Note the Object ID**
   - Open the newly created group
   - Copy the **Object ID** (GUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - You'll need this for the environment variable

4. **Add Members**
   - In the group, go to: **Members** → **Add members**
   - Add:
     - Accounting VP's team members
     - IT/Tech team members
     - Any other authorized users
   - Click: **Select**

### Step 2: Configure Azure AD App Registration

1. **Navigate to App Registration**
   - Azure Portal → **Azure Active Directory** → **App registrations**
   - Select your app: **Cash Forecast Analyzer** (Client ID: `2460e3dd-93a2-439c-8254-c8caf20b7d93`)

2. **Add API Permissions**
   - Click: **API permissions** → **Add a permission**
   - Select: **Microsoft Graph**
   - Choose: **Delegated permissions**
   - Search and select: `GroupMember.Read.All`
     - *Alternative*: `User.Read.All` (includes group membership)
   - Click: **Add permissions**

3. **Grant Admin Consent**
   - Click: **Grant admin consent for [Your Tenant]**
   - Confirm: **Yes**
   - ⚠️ **Note**: Tenant admin privileges required for this step

4. **Verify Permissions**
   - You should see:
     - ✅ `User.Read` (Delegated)
     - ✅ `GroupMember.Read.All` (Delegated)
     - ✅ `Sites.Read.All` or `AllSites.Read` (Delegated) - for SharePoint
     - ✅ `Sites.ReadWrite.All` (Application) - for logging

### Step 3: Update Environment Variables

#### Local Development (`.env` file)

Add this line to your `.env` file:
```bash
# Group-Based Access Control
AUTHORIZED_GROUP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Replace with your group Object ID
```

Full example:
```bash
# Azure AD Authentication
AZURE_AD_CLIENT_ID=2460e3dd-93a2-439c-8254-c8caf20b7d93
AZURE_AD_CLIENT_SECRET=<your-client-secret>
AZURE_AD_TENANT_ID=<your-tenant-id>
AZURE_AD_REDIRECT_URI=http://localhost:5000/auth/callback

# Group-Based Access Control
AUTHORIZED_GROUP_ID=<your-group-object-id>

# Property Data Source
PROPERTY_DATA_SOURCE=sharepoint

# SharePoint Configuration
SHAREPOINT_SITE_URL=https://peakcampus.sharepoint.com/sites/BaseCampApps
SHAREPOINT_LIST_NAME=Properties_0
```

#### Production (Azure App Service)

1. Go to: **Azure Portal** → **App Services** → **CashForecastAnalyzer**
2. Select: **Environment variables** (or **Configuration** → **Application settings**)
3. Click: **New application setting**
4. Add:
   - **Name**: `AUTHORIZED_GROUP_ID`
   - **Value**: `<your-group-object-id>`
5. Click: **OK** → **Save**
6. Restart the app

### Step 4: Apply Group Protection to Routes

#### Option A: Protect All Main Routes (Recommended)

Replace `@login_required` with `@group_required` on your main application routes:

```python
# In app.py

@app.route('/')
@group_required  # Changed from @login_required
def index():
    """Main page - now restricted to group members"""
    return render_template('index.html')

@app.route('/analyze')
@group_required  # Changed from @login_required
def analyze():
    """Analysis page - restricted"""
    return render_template('analyze.html')
```

#### Option B: Mixed Protection (Advanced)

Keep some routes with `@login_required` (any tenant user) and others with `@group_required`:

```python
# Anyone in tenant can access
@app.route('/about')
@login_required
def about():
    return render_template('about.html')

# Only group members can access
@app.route('/analyze')
@group_required
def analyze():
    return render_template('analyze.html')
```

#### Routes to Update

Current routes using `@login_required` (found at these lines in app.py):
- Line 249: `/auth/sharepoint-consent`
- Line 574: `/` (index)
- Line 671: Another route
- Line 759: Another route
- Line 766: Another route
- Line 776: Another route
- Line 1083: Another route
- Line 1104: Another route
- Line 1131: Another route
- Line 1179: Another route

**Recommendation**: Replace all `@login_required` with `@group_required` for full restriction.

### Step 5: Test the Implementation

#### Test 1: Authorized User Access
1. Add your own account to the `CashForecastAnalyzer-Users` group
2. Navigate to: http://localhost:5000 (or your prod URL)
3. Sign in with your credentials
4. Expected: You should see the main application page

#### Test 2: Unauthorized User Access
1. Sign in with an account NOT in the group
2. Expected: You should see an "Access Denied" page with:
   - 🔒 Header
   - Your email address displayed
   - Message about contacting IT/Accounting VP
   - Options to sign out or return home

#### Test 3: Group Membership Logging
Check the console logs for:
```
=== USER GROUPS FETCHED: X groups ===
=== USER AUTHORIZATION CHECK: True/False ===
```

#### Test 4: No Configuration (Fail-Safe)
If `AUTHORIZED_GROUP_ID` is not set, the system logs a warning but allows access (fail-open):
```
=== INFO: No AUTHORIZED_GROUP_ID configured - group check disabled ===
```

## How It Works

### Authentication Flow

```
User visits app
    ↓
Redirected to Microsoft login
    ↓
User signs in
    ↓
Azure AD returns token + user info
    ↓
App fetches user's group memberships
    ↓
Groups stored in session cache
    ↓
User redirected to app
    ↓
Route decorated with @group_required
    ↓
Check: Is user in authorized group?
    ├─ Yes → Allow access
    └─ No → Show "Access Denied" (403)
```

### Session Storage

After successful login, session contains:
```python
session = {
    'user': {
        'name': 'John Doe',
        'email': 'john.doe@peakmade.com',
        'id': 'user-object-id'
    },
    'user_groups': [
        'group-id-1',
        'group-id-2',
        'authorized-group-id',  # This one grants access
        'group-id-3'
    ],
    'authenticated': True,
    # ... other session data
}
```

### Access Check

```python
def check_group_membership(group_id=None):
    """Check if user is in authorized group"""
    if not group_id:
        group_id = os.environ.get('AUTHORIZED_GROUP_ID')
    
    if not group_id:
        return True  # Fail open if not configured
    
    user_groups = session.get('user_groups', [])
    return group_id in user_groups
```

## Decorators Reference

### `@login_required`
- **Purpose**: Basic authentication check
- **Checks**: Is user signed in?
- **Use for**: Public tenant-wide routes

```python
@app.route('/about')
@login_required
def about():
    # Any authenticated user can access
    return render_template('about.html')
```

### `@group_required`
- **Purpose**: Group-based authorization
- **Checks**: Is user signed in AND in authorized group?
- **Use for**: Restricted application routes

```python
@app.route('/analyze')
@group_required
def analyze():
    # Only group members can access
    return render_template('analyze.html')
```

## Managing Access

### Adding Users

1. **Via Azure Portal**
   - Go to: **Azure AD** → **Groups** → **CashForecastAnalyzer-Users**
   - Click: **Members** → **Add members**
   - Search and select users
   - Click: **Select**

2. **Via PowerShell** (Bulk Operations)
   ```powershell
   # Connect to Azure AD
   Connect-AzureAD
   
   # Get group
   $group = Get-AzureADGroup -Filter "DisplayName eq 'CashForecastAnalyzer-Users'"
   
   # Add user by email
   $user = Get-AzureADUser -Filter "userPrincipalName eq 'user@peakmade.com'"
   Add-AzureADGroupMember -ObjectId $group.ObjectId -RefObjectId $user.ObjectId
   
   # Bulk add from CSV
   Import-Csv users.csv | ForEach-Object {
       $user = Get-AzureADUser -Filter "userPrincipalName eq '$($_.Email)'"
       Add-AzureADGroupMember -ObjectId $group.ObjectId -RefObjectId $user.ObjectId
   }
   ```

### Removing Users

1. **Via Azure Portal**
   - Go to group → **Members**
   - Select user → **Remove**

2. **Via PowerShell**
   ```powershell
   $group = Get-AzureADGroup -Filter "DisplayName eq 'CashForecastAnalyzer-Users'"
   $user = Get-AzureADUser -Filter "userPrincipalName eq 'user@peakmade.com'"
   Remove-AzureADGroupMember -ObjectId $group.ObjectId -MemberId $user.ObjectId
   ```

### Verifying User's Groups

```powershell
# Get user's groups
$user = Get-AzureADUser -Filter "userPrincipalName eq 'user@peakmade.com'"
Get-AzureADUserMembership -ObjectId $user.ObjectId | Select DisplayName, ObjectId
```

## Troubleshooting

### Issue: "Access Denied" for Authorized User

**Possible Causes:**
1. User not actually in the group
2. Group membership not synced yet (wait 5-10 minutes)
3. User session cached before being added to group

**Solutions:**
```python
# Have user sign out and sign in again to refresh groups
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
```

### Issue: "Could not fetch user groups"

**Possible Causes:**
1. API permission not granted
2. Admin consent not provided
3. Token doesn't include necessary scopes

**Check:**
- Azure Portal → App Registration → API permissions
- Ensure `GroupMember.Read.All` has green checkmark (admin consented)

**Fix:**
```bash
# Re-consent by signing out and back in
# Or grant admin consent in Azure Portal
```

### Issue: All Users Blocked (Even Group Members)

**Possible Cause:** Wrong group Object ID in environment variable

**Check:**
```python
# Add debug route (temporary)
@app.route('/debug/groups')
@login_required
def debug_groups():
    return jsonify({
        'user_groups': session.get('user_groups', []),
        'configured_group': os.environ.get('AUTHORIZED_GROUP_ID'),
        'is_authorized': check_group_membership()
    })
```

**Verify:** Navigate to `/debug/groups` and check:
- Does `configured_group` match your actual group ID?
- Is that ID in the `user_groups` list?

### Issue: Group Check Not Working (Always Allows)

**Cause:** `AUTHORIZED_GROUP_ID` environment variable not set

**Check logs for:**
```
=== INFO: No AUTHORIZED_GROUP_ID configured - group check disabled ===
```

**Fix:** Set the environment variable and restart the app

## Security Considerations

### Best Practices

✅ **Use security groups, not distribution lists**
- Security groups integrate with Azure AD authentication
- Distribution lists are for email only

✅ **Keep group membership up to date**
- Remove users when they leave or change roles
- Regular audits of group membership

✅ **Use meaningful group names**
- Format: `AppName-RoleName` (e.g., `CashForecastAnalyzer-Users`)
- Makes it easy to identify in Azure Portal

✅ **Document who manages the group**
- Assign owners in Azure AD
- Clear process for requesting access

✅ **Test with real user accounts**
- Don't just test with admin accounts
- Verify the "Access Denied" flow works

### What This Protects

- ✅ Prevents unauthorized tenant users from accessing the app
- ✅ Provides audit trail of who accessed the system
- ✅ Centralizes access control in Azure AD
- ✅ Allows for easy user onboarding/offboarding

### What This Doesn't Protect

- ❌ Does not protect against compromised credentials (use MFA for that)
- ❌ Does not provide row-level security in data sources
- ❌ Does not prevent network-level attacks

## Advanced: Multiple Groups

To support multiple authorized groups (e.g., Accounting + Tech teams in separate groups):

```python
# In .env
AUTHORIZED_GROUPS=group-id-1,group-id-2,group-id-3

# In auth.py, update check_group_membership:
def check_group_membership(group_ids=None):
    """Check if user is in any of the specified groups"""
    if not group_ids:
        group_ids_str = os.environ.get('AUTHORIZED_GROUPS', os.environ.get('AUTHORIZED_GROUP_ID', ''))
        group_ids = [g.strip() for g in group_ids_str.split(',') if g.strip()]
    
    if not group_ids:
        logger.warning("No authorized groups configured")
        return True  # Fail open
    
    user_groups = session.get('user_groups', [])
    return any(gid in user_groups for gid in group_ids)
```

## Advanced: Custom Error Page

To customize the "Access Denied" page, create a template:

```python
# In templates/access_denied.html
@group_required
def decorated_function(*args, **kwargs):
    if not check_group_membership():
        return render_template('access_denied.html', 
                             user=session.get('user', {})), 403
    return f(*args, **kwargs)
```

## Migration Path

If you want to gradually roll out group-based access:

### Phase 1: Monitoring Only
```python
# Log group check results but don't enforce
user_groups = session.get('user_groups', [])
is_authorized = authorized_group_id in user_groups
logger.info(f"User {user_email} authorization: {is_authorized}")
# Continue regardless
```

### Phase 2: Soft Launch
- Keep `@login_required` on most routes
- Add `@group_required` only to new/sensitive features

### Phase 3: Full Rollout
- Replace all `@login_required` with `@group_required`
- Announce change to all users
- Support team ready for access requests

## Summary

**What You've Gained:**
- ✅ Fine-grained access control
- ✅ Easy user management via Azure AD groups
- ✅ Clear audit trail
- ✅ Professional "Access Denied" experience
- ✅ Centralized authorization policy

**Next Steps:**
1. Create the security group in Azure AD
2. Configure API permissions and grant consent
3. Set `AUTHORIZED_GROUP_ID` environment variable
4. Replace `@login_required` with `@group_required`
5. Test with authorized and unauthorized users
6. Train support team on access management

## Related Documentation

- [SESSION_MANAGEMENT_GUIDE.md](SESSION_MANAGEMENT_GUIDE.md) - Session tracking
- [AZURE_AD_AUTHENTICATION.md](AZURE_AD_AUTHENTICATION.md) - Basic auth setup
- [AUTHENTICATION_CONTEXT.md](AUTHENTICATION_CONTEXT.md) - Auth architecture

## For Copilot Agents

**Keywords**: group-based access control, RBAC, Entra ID groups, Azure AD security groups, authorization, access restriction, GroupMember.Read.All, group membership, user authorization, security group, group_required decorator

**Related Concepts**: role-based access control, authorization vs authentication, Azure AD groups, security groups, delegated permissions, group membership API, Microsoft Graph groups
