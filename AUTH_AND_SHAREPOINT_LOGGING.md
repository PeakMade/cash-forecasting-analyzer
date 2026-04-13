# Authentication & SharePoint Logging — Integration Reference

This document describes how the Associate Relations app handles user authentication (Azure AD via MSAL) and SharePoint activity logging.  It is written to be consumed by another Flask app that wants to adopt the same patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
   - [Libraries Used](#libraries-used)
   - [Step-by-Step Flow](#step-by-step-flow)
   - [Session Contents After Login](#session-contents-after-login)
   - [Token Refresh Strategy](#token-refresh-strategy)
   - [Logout](#logout)
3. [Admin Authorization](#admin-authorization)
   - [How Roles Are Determined](#how-roles-are-determined)
   - [Role Values](#role-values)
   - [Authorization Payload Shape](#authorization-payload-shape)
4. [SharePoint Logging](#sharepoint-logging)
   - [What Is Logged](#what-is-logged)
   - [Write Modes](#write-modes)
   - [Token Strategy for Logging](#token-strategy-for-logging)
   - [Log Item Shape](#log-item-shape)
   - [Available Log Methods](#available-log-methods)
5. [Required Configuration](#required-configuration)
6. [Azure App Registration Requirements](#azure-app-registration-requirements)
7. [Reusable Auth Blueprint](#reusable-auth-blueprint)

---

## Overview

Authentication is handled with **OAuth 2.0 Authorization Code Flow** (confidential client) against Azure AD using the `msal` library.  After login, the user's role/admin status is looked up from a **SharePoint admin list**.  All meaningful user activity is written to a **SharePoint "Innovation Use Log" list** — either via Graph API (app-only) or SharePoint REST (delegated).

---

## Authentication Flow

### Libraries Used

| Library | Purpose |
|---|---|
| `msal` | Token acquisition and refresh |
| `flask` | Framework; session storage |
| `flask-session` | Server-side filesystem session backend |
| `requests` | Microsoft Graph API calls |

### Step-by-Step Flow

```
User visits protected route
        │
        ▼
GET /auth/login
  └─ AzureADAuth.get_auth_url()
       └─ msal.ConfidentialClientApplication
            .get_authorization_request_url(scopes, redirect_uri)
        │
        ▼  (browser redirects to Microsoft login page)
        │
        ▼
GET /auth/callback?code=<auth_code>
  └─ AzureADAuth.get_token_from_code(code)
       └─ msal.acquire_token_by_authorization_code(code, scopes, redirect_uri)
       └─ Tokens + id_token_claims stored in Flask session
       └─ (Optional) acquire delegated SharePoint token via silent / refresh-token exchange
       └─ Graph /me call to enrich employee_id
        │
        ▼
Authorization check
  └─ AzureADAuth.get_authorization(user_email)
       └─ SharePoint admin list lookup → role / admin flag
        │
        ▼
Redirect to admin endpoint or user endpoint
```

### Session Contents After Login

After `get_token_from_code()` succeeds, the following keys are populated in the Flask server-side session:

| Key | Type | Description |
|---|---|---|
| `authenticated` | `bool` | Always `True` after login |
| `user` | `dict` | `{ name, email, id (OID), employee_id }` |
| `account` | `dict` | MSAL account stub for silent refresh |
| `access_token` | `str` | Microsoft Graph access token |
| `ms_access_token` | `str` | Alias of `access_token` (Teams service) |
| `jwt` | `str` | Alias of `access_token` (legacy) |
| `refresh_token` | `str` | OAuth refresh token |
| `token_cache` | `str` | Serialized MSAL token cache |
| `sp_access_token` | `str` | SharePoint delegated token (only when delegated mode enabled) |
| `session_id` | `str` | 8-char UUID fragment, used in log entries |
| `is_admin` | `bool` | Whether the user has an admin role |
| `admin_type` | `str\|None` | `"pops_admin"` or `"tech_user"` or `None` |

### Token Refresh Strategy

Silent token refresh from the MSAL token cache is used throughout the app.  The token cache is serialized into `session['token_cache']` and deserialized on every `get_msal_app()` call.

For SharePoint delegated tokens specifically:

1. Try `msal.acquire_token_silent()` using the cached account.
2. If that fails, call `msal.acquire_token_by_refresh_token()` using `session['refresh_token']`.
3. Store the result in `session['sp_access_token']`.

This only runs when `SHAREPOINT_LOG_WRITE_MODE` (or `SHAREPOINT_DATA_MODE`) is set to `delegated` or `auto`.

### Logout

`GET /auth/logout` calls:

1. `AzureADAuth.get_logout_url()` → constructs `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout?post_logout_redirect_uri=...`
2. `session.clear()` to destroy all server-side session data.
3. Redirects the browser to the Microsoft logout URL so the SSO session is also ended.

---

## Admin Authorization

### How Roles Are Determined

After a successful login, `get_authorization(user_email)` is called.  It:

1. Queries a **SharePoint list** (configured via `SHAREPOINT_LIST_NAME` / `SHAREPOINT_SITE_HOST` / `SHAREPOINT_SITE_PATH`) via SharePoint REST using an **app-only** token.
2. Iterates list items looking for a row where the identity field (default: `Email`) matches the logged-in user's email.
3. Optionally filters by an `App` / `Application` column matching the configured `ADMIN_APP_NAME`.
4. Reads the `Admin Value` (or `AdminType`, `Role`) column and normalizes it to a known role.
5. If the SharePoint lookup fails or returns nothing, falls back to `DEFAULT_LOCAL_ADMIN` config flag (dev/local only).

### Role Values

| Raw value in SharePoint | Normalized role | `admin` flag |
|---|---|---|
| `admin`, `pops_admin`, `pops` | `pops_admin` | `True` |
| `tech_user`, `tech`, `tech-user` | `tech_user` | `True` |
| anything else / empty | `""` | `False` |

### Authorization Payload Shape

```python
{
    "email":      "user@example.com",   # lowercased
    "role":       "pops_admin",         # normalized role string
    "admin":      True,                 # bool
    "admin_type": "pops_admin",         # same as role, or None
    "active":     True,                 # from Active column
    "app":        "Associate Relations" # app name from list or config
}
```

---

## SharePoint Logging

### What Is Logged

Every meaningful user action writes a row to a SharePoint list (`Innovation Use Log` by default).

### Write Modes

Controlled by `SHAREPOINT_LOG_WRITE_MODE`:

| Mode | Behavior |
|---|---|
| `app_only` (default) | Uses Graph API with an **app-only** client-credentials token.  No delegated token needed. |
| `delegated` | Uses SharePoint REST API with the user's delegated `sp_access_token`. |
| `auto` | Tries app-only first; falls back to delegated if that fails. |

**For most deployments, `app_only` is the recommended mode.**  It requires no user interaction and the Azure app registration simply needs `Sites.ReadWrite.All` (application permission) granted.

### Token Strategy for Logging

**App-only (Graph):**

1. `msal.ConfidentialClientApplication.acquire_token_for_client(["https://graph.microsoft.com/.default"])`
2. Resolves the SharePoint site ID via `GET https://graph.microsoft.com/v1.0/sites/{host}:{path}`
3. Resolves the list ID via `GET https://graph.microsoft.com/v1.0/sites/{siteId}/lists?$filter=displayName eq 'Innovation Use Log'`
4. Creates list items via `POST https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/items`

Site ID and list ID are cached in memory on the logger instance for the lifetime of the request.

**Delegated (SharePoint REST):**

1. Uses `session['sp_access_token']` (audience must be `*.sharepoint.com`).
2. Token audience is validated by decoding the JWT payload and checking the `aud` claim before use.
3. Falls back to an app-only **SharePoint REST** token (client-credentials to `{SHAREPOINT_RESOURCE}/.default`) if `SHAREPOINT_LOG_ALLOW_APP_ONLY=true`.

### Log Item Shape

Every log write sends these fields to SharePoint:

| SharePoint Column | Source |
|---|---|
| `Title` | User's email |
| `UserEmail` | User's email |
| `UserName` | User's display name |
| `LoginTimestamp` | ISO 8601, Eastern Time |
| `UserRole` | Normalized role string |
| `ActivityType` | See activity types below |
| `Application` | `"Associate Relations"` (hardcoded) |
| `SessionID` | `session['session_id']` (8-char UUID) |
| `Env` | `ENVIRONMENT` config value (`Local`, `Production`, etc.) |

### Available Log Methods

```python
logger = SharePointUsageLogger()

logger.log_session_start(user_email, user_name, user_role)   # ActivityType = "Start Session"
logger.log_session_end(user_email, user_name, user_role)     # ActivityType = "End Session"
logger.log_successful_case(user_email, user_name, user_role) # ActivityType = "Successful Case"
logger.log_case_closed(user_email, user_name, user_role)     # ActivityType = "Closed"
logger.log_case_closed_legal(user_email, user_name, user_role) # ActivityType = "Closed-Legal"

# Legacy aliases
logger.log_login(user_email, user_name, user_role)   # → log_session_start
logger.log_logout(user_email, user_name, user_role)  # → log_session_end

# Generic
logger.log_activity(user_email, user_name, user_role, activity_type)
```

All methods accept an optional `user_token` parameter that is checked as a delegated SharePoint token before falling back.

Factory helper (handles initialization failure gracefully):

```python
from app.sharepoint_logger import get_sharepoint_logger
logger = get_sharepoint_logger()  # returns None if initialization fails
if logger:
    logger.log_session_start(...)
```

---

## Required Configuration

Set these in your `.env` file or environment.

### Azure AD (required)

| Variable | Description |
|---|---|
| `AZURE_AD_CLIENT_ID` | App registration client ID |
| `AZURE_AD_CLIENT_SECRET` | Client secret |
| `AZURE_AD_TENANT_ID` | Azure AD tenant ID |
| `AZURE_AD_REDIRECT_URI` | Full callback URL, e.g. `https://yourapp.azurewebsites.net/auth/callback` |

### SharePoint Logging

| Variable | Default | Description |
|---|---|---|
| `SHAREPOINT_LOG_SITE_URL` | `https://<tenant>.sharepoint.com/sites/BaseCampApps` | SharePoint site root URL (not a list view URL) |
| `SHAREPOINT_LOG_LIST_NAME` | `Innovation Use Log` | Display name of the target list |
| `SHAREPOINT_LOG_WRITE_MODE` | `app_only` | `app_only` \| `delegated` \| `auto` |
| `SHAREPOINT_LOG_ALLOW_APP_ONLY` | `False` | Allow app-only REST fallback in delegated mode |
| `SHAREPOINT_RESOURCE` | `https://<tenant>.sharepoint.com` | SharePoint tenant root for delegated token scope |

### Admin Authorization (SharePoint list)

| Variable | Default | Description |
|---|---|---|
| `SHAREPOINT_SITE_HOST` | — | Hostname, e.g. `peakcampus.sharepoint.com` |
| `SHAREPOINT_SITE_PATH` | — | Site path, e.g. `/sites/BaseCampApps` |
| `SHAREPOINT_LIST_NAME` | — | Admin list name |
| `ADMIN_IDENTITY_FIELD` | `Email` | Column that holds the user's email |
| `SHAREPOINT_ACTIVE_FIELD` | `Active` | Column for active/inactive flag |
| `ADMIN_APP_NAME` | `Associate Relations` | Value in the App column to match |
| `ADMIN_CACHE_SECONDS` | `300` | How long to cache authorization lookups |

### Session

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Flask secret key (change in production) |
| `SESSION_FILE_DIR` | `./flask_session` (local) or `/home/flask_session` (Azure) | Server-side session directory |
| `ENVIRONMENT` | `Local` | Written to every log entry |

### Optional / Dev

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_LOCAL_ADMIN` | `True` | Grant admin role when SharePoint lookup unavailable (dev only) |

---

## Azure App Registration Requirements

### Delegated permissions (for user login)

| Permission | Reason |
|---|---|
| `User.Read` | Read signed-in user's profile |
| `offline_access` | Needed for refresh token |
| `https://<tenant>.sharepoint.com/AllSites.Manage` | Delegated SharePoint access (only when using delegated write mode) |

### Application permissions (for app-only operations)

| Permission | Reason |
|---|---|
| `Sites.ReadWrite.All` (Graph) | Write log items via Graph app-only |
| `Sites.Read.All` (Graph) | Read admin list via Graph app-only |

All application permissions require **admin consent** in the Azure portal.

### Redirect URIs

Register the `/auth/callback` path of your app as an allowed redirect URI under **Authentication → Web**.

---

## Reusable Auth Blueprint

The `shared_auth.py` module provides `create_auth_blueprint()` — a factory that returns a Flask `Blueprint` you can register on any app.  Wire it up by passing callables for the operations that differ per app:

```python
from app.shared_auth import create_auth_blueprint
from app.auth_helper import AzureADAuth

auth_bp = create_auth_blueprint(
    get_auth_helper=lambda: AzureADAuth(),
    get_cached_authorization=lambda email: AzureADAuth().get_authorization(email),
    clear_cached_authorization=lambda: cache.clear(),
    clear_admin_cache=lambda email: admin_cache.pop(email, None),
    user_is_admin=lambda email: session.get('is_admin', False),
    admin_endpoint='admin.dashboard',
    user_endpoint='main.index',
    home_endpoint='main.index',
    name='auth',
    url_prefix='/auth',
    on_login_success=lambda email, name, role: logger.log_session_start(email, name, role),
    on_logout=lambda email, name, role: logger.log_session_end(email, name, role),
)

app.register_blueprint(auth_bp)
```

This blueprint exposes:

| Route | Description |
|---|---|
| `GET /auth/login` | Redirects to Microsoft login |
| `GET /auth/callback` | Handles the OAuth callback, sets session, redirects |
| `GET /auth/logout` | Clears session, redirects to Microsoft logout |
