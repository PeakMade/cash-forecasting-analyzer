# Azure AD User Authentication Setup

## Overview
The application now uses Azure AD user authentication instead of app-only authentication. Users sign in with their PeakMade Microsoft accounts, and the app accesses SharePoint on their behalf using delegated permissions.

## Benefits
- ✓ Works with Conditional Access policies (no tenant admin bypass needed)
- ✓ Only authenticated PeakMade users can access the app
- ✓ No tenant admin consent required for SharePoint access
- ✓ Better audit trail (actions tied to specific users)
- ✓ More secure - follows Microsoft security best practices

## Azure AD App Registration Configuration

### 1. Update App Registration

Go to Azure Portal → Azure Active Directory → App registrations → Your app

#### A. Add Redirect URI
- Click "Authentication" → "Add a platform" → "Web"
- Add redirect URI:
  - Local: `http://localhost:5000/auth/callback`
  - Production: `https://cashforecastanalyzer.azurewebsites.net/auth/callback`
- Save

#### B. Configure API Permissions
Click "API permissions" → "Add a permission"

**Microsoft Graph** (Delegated permissions):
- `User.Read` - Read user profile

**SharePoint** (Delegated permissions):
- Click "SharePoint" → "Delegated permissions"
- Add: `AllSites.Read` or `Sites.Read.All`

**No admin consent required!** Users consent for themselves when they first login.

#### C. Update Client Secret (if needed)
- Go to "Certificates & secrets"
- Create new client secret if the old one expired
- Copy the **Value** (not the Secret ID)

### 2. Environment Variables

Update your `.env` file (local) and Azure App Service environment variables (production):

```bash
# Azure AD Authentication
AZURE_AD_CLIENT_ID=2460e3dd-93a2-439c-8254-c8caf20b7d93
AZURE_AD_CLIENT_SECRET=<your-client-secret-value>
AZURE_AD_TENANT_ID=<your-tenant-id>  # Find in Azure AD overview
AZURE_AD_REDIRECT_URI=http://localhost:5000/auth/callback  # Change for production

# Property Data Source
PROPERTY_DATA_SOURCE=sharepoint  # or 'database'

# SharePoint Configuration
SHAREPOINT_SITE_URL=https://peakcampus.sharepoint.com/sites/BaseCampApps
SHAREPOINT_LIST_NAME=Properties_0

# Remove these (no longer needed):
# SHAREPOINT_CLIENT_ID  # Not needed for user auth
# SHAREPOINT_CLIENT_SECRET  # Not needed for user auth
```

### 3. Production Deployment

In Azure Portal → CashForecastAnalyzer → Environment variables:

1. Update/Add:
   - `AZURE_AD_CLIENT_ID` = `2460e3dd-93a2-439c-8254-c8caf20b7d93`
   - `AZURE_AD_CLIENT_SECRET` = `<your-new-client-secret-value>`
   - `AZURE_AD_TENANT_ID` = `<your-tenant-id-guid>`
   - `AZURE_AD_REDIRECT_URI` = `https://cashforecastanalyzer.azurewebsites.net/auth/callback`
   
2. Keep existing:
   - `PROPERTY_DATA_SOURCE` = `sharepoint`
   - `SHAREPOINT_SITE_URL` = `https://peakcampus.sharepoint.com/sites/BaseCampApps`
   - `SHAREPOINT_LIST_NAME` = `Properties_0`

3. Remove (no longer used):
   - `SHAREPOINT_CLIENT_ID`
   - `SHAREPOINT_CLIENT_SECRET`

4. Save and restart the app

## How It Works

### User Flow
1. User visits app → redirected to Microsoft login page
2. User signs in with their `@peakmade.com` account
3. User consents to app accessing their profile and SharePoint (first time only)
4. App receives access token scoped to the user
5. App uses user's token to read SharePoint list
6. User's name and logout button shown in header

### Technical Flow
- Uses MSAL (Microsoft Authentication Library) for OAuth 2.0 flow
- Stores access token and user info in Flask session
- SharePoint access uses user's delegated permissions
- Token automatically refreshed when expired
- All routes except `/login`, `/auth/callback`, `/logout`, and `/health` require authentication

## Testing

### Local Testing
1. Update `.env` with Azure AD variables
2. Run `python app.py`
3. Visit `http://localhost:5000`
4. You'll be redirected to Microsoft login
5. Sign in with your PeakMade account
6. After login, you'll return to the app

### Production Testing
1. Update Azure environment variables
2. Deploy code to Azure (via git push)
3. Visit your Azure app URL
4. Sign in with PeakMade account
5. Verify SharePoint data loads correctly

## Troubleshooting

### "AADSTS50011: The redirect URI does not match"
- Make sure redirect URI is added in App Registration → Authentication
- Check it matches exactly (including http/https, trailing slashes)

### "Consent Required"
- User needs to consent to permissions on first login
- This is normal and expected behavior

### "Access Token Error"
- Check that delegated SharePoint permissions are added
- Verify user has access to the SharePoint site

### "Session Expired"
- User needs to log in again
- Tokens expire after a period of inactivity

## Security Notes

- Users must have `@peakmade.com` email addresses
- Only users with access to the SharePoint site can retrieve property data
- Sessions stored server-side with secure session keys
- Access tokens never exposed to client browser
- Logout clears all session data

## Files Modified

- `services/auth.py` - New Azure AD authentication module
- `services/sharepoint_data_source.py` - Updated to use user tokens
- `services/data_source_factory.py` - Pass access token to SharePoint
- `app.py` - Added login/logout routes, @login_required decorators
- `templates/base.html` - Added user info and logout button
- `requirements.txt` - Added msal==1.26.0

##Next Steps

1. Update Azure AD app registration with redirect URI and delegated permissions
2. Update environment variables (local and Azure)
3. Test locally with your PeakMade account
4. Deploy to Azure and test production
5. Confirm SharePoint data loads correctly for authenticated users
