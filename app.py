"""
Cash Forecast Analyzer - Main Flask Application
Analyzes student housing property cash forecasts and validates accountant recommendations
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Debug: Print loaded environment variables
print(f"ENV DEBUG: OPENAI_MODEL={os.environ.get('OPENAI_MODEL')}")
print(f"ENV DEBUG: PROPERTY_DATA_SOURCE={os.environ.get('PROPERTY_DATA_SOURCE')}")
print(f"ENV DEBUG: SECRET_KEY exists={bool(os.environ.get('SECRET_KEY'))}")

# Version checks - CRITICAL for economic analysis with web search
print("\n" + "="*80)
print("FLASK APP INITIALIZATION - VERSION CHECKS")
print("="*80)
try:
    import openai
    print(f"✓ OpenAI Library Version: {openai.__version__}")
    if openai.__version__ >= "2.2.0":
        print("  ✓ Web search capability available (Responses API)")
    else:
        print("  ⚠️  WARNING: OpenAI library too old - web search will NOT work!")
        print("  ⚠️  Run: pip install --upgrade openai==2.2.0")
except Exception as e:
    print(f"✗ Error checking OpenAI version: {e}")

try:
    from services.economic_analysis import EconomicAnalyzer
    test_analyzer = EconomicAnalyzer()
    print(f"✓ IPEDS Client Enabled: {test_analyzer.ipeds.enabled}")
    print(f"✓ OpenAI Model: {test_analyzer.model}")
    if hasattr(test_analyzer.client, 'responses'):
        print(f"✓ Responses API Available: YES (web search enabled)")
    else:
        print(f"⚠️  Responses API Available: NO (upgrade openai library)")
except Exception as e:
    print(f"✗ Error checking economic analyzer: {e}")

college_scorecard_key = os.environ.get('COLLEGE_SCORECARD_API_KEY')
if college_scorecard_key:
    print(f"✓ College Scorecard API Key: Set (...{college_scorecard_key[-10:]})")
else:
    print("⚠️  College Scorecard API Key: Not set (IPEDS data disabled)")
print("="*80 + "\n")


from services.file_processor import FileProcessor
from services.analysis_engine import AnalysisEngine
from services.summary_generator import SummaryGenerator
from services.docx_generator import WordDocumentGenerator
from services.auth import AzureADAuth, login_required, get_user, group_required

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv', 'txt', 'pdf'}

# Configure server-side session storage (avoids cookie size limits)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Azure AD authentication
azure_auth = AzureADAuth(app)

def is_local_environment():
    """Detect if running in local development environment"""
    # Check common local environment indicators
    return (
        os.getenv('FLASK_ENV') == 'development' or
        os.getenv('ENVIRONMENT') == 'local' or
        app.debug or
        request.host.startswith('127.0.0.1') or
        request.host.startswith('localhost')
    )

def get_application_name():
    """Get application name - always returns CashForecastAnalyzer"""
    return 'CashForecastAnalyzer'

def get_environment_name():
    """Get environment name for logging"""
    return 'Local' if is_local_environment() else 'Prod'

def get_session_id():
    """Get or generate logical session ID for activity tracking"""
    import uuid
    if 'logical_session_id' not in session:
        session['logical_session_id'] = str(uuid.uuid4())
        print(f"=== GENERATED NEW SESSION ID: {session['logical_session_id']} ===")
    else:
        print(f"=== USING EXISTING SESSION ID: {session['logical_session_id']} ===")
    return session['logical_session_id']

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Authentication routes
@app.route('/login')
def login():
    """Initiate Azure AD login flow"""
    auth_url = azure_auth.get_auth_url()
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    """Handle Azure AD callback after login"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400
    
    # Check if this is SharePoint consent flow
    is_sharepoint_consent = session.get('sharepoint_consent_flow', False)
    print(f"=== CALLBACK - Is SharePoint consent: {is_sharepoint_consent} ===")
    
    # Exchange code for token
    if is_sharepoint_consent:
        print("=== PROCESSING SHAREPOINT CONSENT CALLBACK ===")
        result = azure_auth.acquire_sharepoint_token_by_code(code)
        print(f"=== SharePoint token result: {bool(result)} ===")
        if result:
            print(f"=== SharePoint token has access_token: {'access_token' in result} ===")
        session.pop('sharepoint_consent_flow', None)
        if result and 'access_token' in result:
            # Store the SharePoint access token directly in session (smaller than full cache)
            session['sharepoint_access_token'] = result['access_token']
            session['sharepoint_consented'] = True
            
            # Debug: print session sizes
            import json
            print(f"=== SESSION SIZE BREAKDOWN ===")
            for key, value in session.items():
                try:
                    size = len(json.dumps(value))
                    print(f"  {key}: {size} bytes")
                except:
                    print(f"  {key}: (cannot serialize)")
            
            print("=== SHAREPOINT TOKEN STORED IN SESSION - REDIRECTING TO INDEX ===")
            return redirect(url_for('index'))
        else:
            print("=== SHAREPOINT CONSENT FAILED ===")
            return jsonify({'error': 'Failed to acquire SharePoint token'}), 401
    else:
        print("=== PROCESSING INITIAL LOGIN CALLBACK ===")
        result = azure_auth.acquire_token_by_auth_code(code)
    
    if not result:
        return jsonify({'error': 'Failed to acquire token'}), 401
    
    # Store minimal user info in session (avoid large cookies)
    id_token_claims = result.get('id_token_claims', {})
    session['user'] = {
        'name': id_token_claims.get('name', 'Unknown'),
        'email': id_token_claims.get('preferred_username', ''),
        'id': id_token_claims.get('oid', '')
    }
    # Store only essential account info for token refresh
    session['account'] = {
        'home_account_id': id_token_claims.get('oid', ''),
        'environment': 'login.microsoftonline.com',
        'realm': id_token_claims.get('tid', '')
    }
    session['refresh_token'] = result.get('refresh_token')
    session['authenticated'] = True
    
    # Fetch and store user's group memberships for authorization
    # Use the access token we just acquired (includes Graph API scopes)
    try:
        # Import the helper function directly
        from services.auth import fetch_user_groups
        
        # Use the access_token from the login result (includes Graph API permissions)
        access_token = result.get('access_token')
        if access_token:
            user_groups = fetch_user_groups(access_token)
            session['user_groups'] = user_groups
            print(f"=== USER GROUPS FETCHED: {len(user_groups)} groups ===")
            
            # Check if user is in authorized group
            authorized_group_id = os.environ.get('AUTHORIZED_GROUP_ID')
            if authorized_group_id:
                is_authorized = authorized_group_id in user_groups
                print(f"=== USER AUTHORIZATION CHECK: {is_authorized} ===")
                if not is_authorized:
                    print(f"=== WARNING: User {session['user']['email']} not in authorized group ===")
            else:
                print("=== INFO: No AUTHORIZED_GROUP_ID configured - group check disabled ===")
        else:
            print("=== WARNING: No access token in result ===")
            session['user_groups'] = []
    except Exception as e:
        print(f"=== WARNING: Could not fetch user groups: {str(e)} ===")
        import traceback
        traceback.print_exc()
        session['user_groups'] = []  # Fail safe with empty list
    
    # Note: Initial login only provides Graph API token (for group membership)
    # SharePoint access requires separate consent via /auth/sharepoint-consent
    # Don't store SharePoint token here - it won't be in the initial login result
    
    # Log session start (initial login)
    try:
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
        app_token = azure_auth.get_app_only_token()
        
        if not app_token:
            print("=== WARNING: App-only token not available - logging disabled ===")
            print("=== See FIX_SHAREPOINT_APP_LOGGING.md for setup instructions ===")
        elif not access_token:
            print("=== WARNING: User token not available - cannot access SharePoint ===")
        else:
            db = get_property_data_source(access_token=access_token, app_only_token=app_token)
            log_result = db.log_activity(
                user_email=session['user']['email'],
                user_name=session['user']['name'],
                activity_type='Start Session',
                application=get_application_name(),
                environment=get_environment_name(),
                session_id=get_session_id()
            )
            if log_result:
                # Set timestamp immediately after logging to prevent duplicate log in index route
                session['last_session_start'] = datetime.now().isoformat()
                print(f"=== SESSION START LOGGED in auth/callback, timestamp set: {session['last_session_start']} ===")
            else:
                print("=== WARNING: Session start logging failed - check SharePoint permissions ===")
                print("=== See FIX_SHAREPOINT_APP_LOGGING.md for troubleshooting ===")
    except Exception as e:
        # Don't break login if logging fails
        print(f"=== WARNING: Failed to log session start: {str(e)} ===")
        print("=== Logging is disabled but authentication continues ===")
    
    # Redirect directly to index - no second consent needed
    return redirect(url_for('index'))

@app.route('/auth/sharepoint-consent')
@group_required
def sharepoint_consent():
    """Initiate SharePoint consent flow"""
    print("=== INITIATING SHAREPOINT CONSENT FLOW ===")
    session['sharepoint_consent_flow'] = True
    session['sharepoint_consented'] = False  # Clear any existing consent flag
    auth_url = azure_auth.get_sharepoint_consent_url()
    print(f"=== CONSENT URL: {auth_url} ===")
    return redirect(auth_url)

@app.route('/logout')
def logout():
    """End user session (without revoking MS tokens)"""
    # Capture session ID BEFORE any session operations
    current_session_id = session.get('logical_session_id', 'unknown')
    print(f"=== LOGOUT: Captured existing session ID: {current_session_id} ===")
    
    # Log user logout activity before clearing session
    try:
        from services.data_source_factory import get_property_data_source
        user_email = session.get('user', {}).get('email', 'unknown')
        user_name = session.get('user', {}).get('name', 'unknown')
        access_token = azure_auth.get_sharepoint_token()
        app_token = azure_auth.get_app_only_token()
        
        if not app_token:
            print(f"=== WARNING: App-only token not available - cannot log session end for {user_name} ===")
        elif not access_token:
            print(f"=== WARNING: User token not available - cannot access SharePoint for {user_name} ===")
        else:
            db = get_property_data_source(access_token=access_token, app_only_token=app_token)
            log_result = db.log_activity(
                user_email=user_email,
                user_name=user_name,
                activity_type='End Session',
                application=get_application_name(),
                environment=get_environment_name(),
                session_id=current_session_id
            )
            if log_result:
                print(f"=== SESSION END LOGGED for {user_name} with SessionID: {current_session_id} ===")
            else:
                print(f"=== WARNING: Session end logging failed for {user_name} ===")
    except Exception as e:
        # Don't break logout if logging fails
        print(f"=== WARNING: Failed to log session end activity: {str(e)} ===")
    
    # Preserve MS tokens, cache, and user info before clearing session
    token_cache = session.get('token_cache')
    sharepoint_access_token = session.get('sharepoint_access_token')
    refresh_token = session.get('refresh_token')
    account = session.get('account')
    user_info = session.get('user')  # Preserve user name/email
    
    # Clear all session data (including session start timestamp)
    session.clear()
    
    # Restore MS authentication data (keep tokens valid)
    if token_cache:
        session['token_cache'] = token_cache
    if sharepoint_access_token:
        session['sharepoint_access_token'] = sharepoint_access_token
    if refresh_token:
        session['refresh_token'] = refresh_token
    if account:
        session['account'] = account
    if user_info:
        session['user_info_preserved'] = user_info  # Store for session restart
    
    # Mark that tokens exist but session ended
    session['session_ended'] = True
    # Note: last_session_start is cleared, so next access will log new session_start
    
    # Redirect to session ended page
    return redirect(url_for('session_ended'))

@app.route('/session/ended')
def session_ended():
    """Display session ended page"""
    return render_template('session_ended.html')

@app.route('/session/check')
def session_check():
    """Check if Microsoft tokens are still valid"""
    try:
        # Check if we have token data
        if not session.get('token_cache') and not session.get('sharepoint_access_token'):
            return jsonify({'valid': False, 'reason': 'no_tokens'})
        
        # Try to get a fresh token (will use refresh token if access token expired)
        token = azure_auth.get_sharepoint_token()
        
        if token:
            return jsonify({'valid': True})
        else:
            return jsonify({'valid': False, 'reason': 'token_refresh_failed'})
    except Exception as e:
        print(f"=== Session check error: {str(e)} ===")
        return jsonify({'valid': False, 'reason': 'error', 'message': str(e)})

@app.route('/session/start', methods=['POST'])
def session_start():
    """Start a new session (requires valid MS tokens)"""
    try:
        # Verify tokens are still valid
        token = azure_auth.get_sharepoint_token()
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get preserved user info
        user_info = session.get('user_info_preserved')
        if not user_info:
            return jsonify({'error': 'No user information available'}), 401
        
        # Re-establish session with user info
        session['authenticated'] = True
        session['user'] = user_info
        
        # Clean up preserved user info (moved to active session)
        session.pop('user_info_preserved', None)
        
        # Remove session_ended flag
        session.pop('session_ended', None)
        
        # Generate new logical session ID for the restarted session
        import uuid
        session['logical_session_id'] = str(uuid.uuid4())
        print(f"=== SESSION RESTART: Generated new session ID: {session['logical_session_id']} ===")
        
        # Log session restart
        from services.data_source_factory import get_property_data_source
        app_token = azure_auth.get_app_only_token()
        db = get_property_data_source(access_token=token, app_only_token=app_token)
        db.log_activity(
            user_email=session['user']['email'],
            user_name=session['user']['name'],
            activity_type='Start Session',
            application=get_application_name(),
            environment=get_environment_name(),
            session_id=session['logical_session_id']
        )
        # Set timestamp to prevent duplicate logging when navigating to index
        session['last_session_start'] = datetime.now().isoformat()
        print(f"=== SESSION RESTART LOGGED for {session['user']['name']} ===")
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"=== Session start error: {str(e)} ===")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """
    Health check endpoint - shows system configuration and versions
    Access at: http://localhost:5000/health
    """
    import openai
    from services.economic_analysis import EconomicAnalyzer
    
    # Gather version and configuration info
    health_info = {
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'openai_version': openai.__version__,
        'openai_version_ok': openai.__version__ >= "2.2.0",
        'web_search_capable': hasattr(openai.OpenAI(api_key='test'), 'responses'),
        'environment': {
            'openai_model': os.environ.get('OPENAI_MODEL', 'not set'),
            'property_data_source': os.environ.get('PROPERTY_DATA_SOURCE', 'not set'),
            'college_scorecard_api_key': 'set' if os.environ.get('COLLEGE_SCORECARD_API_KEY') else 'NOT SET',
            'bls_api_key': 'set' if os.environ.get('BLS_API_KEY') else 'NOT SET',
        }
    }
    
    # Test economic analyzer
    try:
        test_analyzer = EconomicAnalyzer()
        health_info['economic_analyzer'] = {
            'initialized': True,
            'model': test_analyzer.model,
            'ipeds_enabled': test_analyzer.ipeds.enabled,
            'bls_enabled': test_analyzer.bls.enabled,
            'responses_api_available': hasattr(test_analyzer.client, 'responses')
        }
    except Exception as e:
        health_info['economic_analyzer'] = {
            'initialized': False,
            'error': str(e)
        }
    
    # Generate HTML response
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cash Forecast Analyzer - Health Check</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c5282; border-bottom: 3px solid #4299e1; padding-bottom: 10px; }}
            h2 {{ color: #2d3748; margin-top: 30px; }}
            .status-ok {{ color: #38a169; font-weight: bold; }}
            .status-warning {{ color: #d69e2e; font-weight: bold; }}
            .status-error {{ color: #e53e3e; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #edf2f7; font-weight: 600; color: #2d3748; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
            .badge-success {{ background: #c6f6d5; color: #22543d; }}
            .badge-warning {{ background: #feebc8; color: #744210; }}
            .badge-error {{ background: #fed7d7; color: #742a2a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Cash Forecast Analyzer - Health Check</h1>
            <p><strong>Status:</strong> <span class="status-ok">✓ RUNNING</span></p>
            <p><strong>Timestamp:</strong> {health_info['timestamp']}</p>
            
            <h2>📦 OpenAI Library</h2>
            <table>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Version</td>
                    <td>{health_info['openai_version']}</td>
                    <td>{'<span class="badge badge-success">✓ OK (≥2.2.0)</span>' if health_info['openai_version_ok'] else '<span class="badge badge-error">✗ TOO OLD</span>'}</td>
                </tr>
                <tr>
                    <td>Responses API (Web Search)</td>
                    <td>{'Available' if health_info['web_search_capable'] else 'Not Available'}</td>
                    <td>{'<span class="badge badge-success">✓ ENABLED</span>' if health_info['web_search_capable'] else '<span class="badge badge-error">✗ DISABLED</span>'}</td>
                </tr>
            </table>
            
            <h2>🎓 Economic Analysis Configuration</h2>
            <table>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Economic Analyzer</td>
                    <td>{'Initialized' if health_info['economic_analyzer']['initialized'] else 'Error'}</td>
                    <td>{'<span class="badge badge-success">✓ OK</span>' if health_info['economic_analyzer']['initialized'] else '<span class="badge badge-error">✗ ERROR</span>'}</td>
                </tr>
                <tr>
                    <td>OpenAI Model</td>
                    <td>{health_info['economic_analyzer'].get('model', 'N/A')}</td>
                    <td><span class="badge badge-success">✓ OK</span></td>
                </tr>
                <tr>
                    <td>IPEDS Data (Historical Enrollment)</td>
                    <td>{'Enabled' if health_info['economic_analyzer'].get('ipeds_enabled') else 'Disabled'}</td>
                    <td>{'<span class="badge badge-success">✓ ENABLED</span>' if health_info['economic_analyzer'].get('ipeds_enabled') else '<span class="badge badge-warning">⚠ DISABLED</span>'}</td>
                </tr>
                <tr>
                    <td>BLS Data (Official Unemployment)</td>
                    <td>{'Enabled' if health_info['economic_analyzer'].get('bls_enabled') else 'Disabled'}</td>
                    <td>{'<span class="badge badge-success">✓ ENABLED</span>' if health_info['economic_analyzer'].get('bls_enabled') else '<span class="badge badge-warning">⚠ DISABLED</span>'}</td>
                </tr>
                <tr>
                    <td>Web Search (Current Data)</td>
                    <td>{'Available' if health_info['economic_analyzer'].get('responses_api_available') else 'Not Available'}</td>
                    <td>{'<span class="badge badge-success">✓ ENABLED</span>' if health_info['economic_analyzer'].get('responses_api_available') else '<span class="badge badge-error">✗ DISABLED</span>'}</td>
                </tr>
            </table>
            
            <h2>🔧 Environment Variables</h2>
            <table>
                <tr>
                    <th>Variable</th>
                    <th>Value</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>OPENAI_MODEL</td>
                    <td>{health_info['environment']['openai_model']}</td>
                    <td><span class="badge badge-success">✓ SET</span></td>
                </tr>
                <tr>
                    <td>PROPERTY_DATA_SOURCE</td>
                    <td>{health_info['environment']['property_data_source']}</td>
                    <td><span class="badge badge-success">✓ SET</span></td>
                </tr>
                <tr>
                    <td>COLLEGE_SCORECARD_API_KEY</td>
                    <td>{health_info['environment']['college_scorecard_api_key']}</td>
                    <td>{'<span class="badge badge-success">✓ SET</span>' if health_info['environment']['college_scorecard_api_key'] == 'set' else '<span class="badge badge-warning">⚠ NOT SET</span>'}</td>
                </tr>
                <tr>
                    <td>BLS_API_KEY</td>
                    <td>{health_info['environment']['bls_api_key']}</td>
                    <td>{'<span class="badge badge-success">✓ SET</span>' if health_info['environment']['bls_api_key'] == 'set' else '<span class="badge badge-warning">⚠ NOT SET</span>'}</td>
                </tr>
            </table>
            
            <h2>✅ Expected Behavior</h2>
            <ul>
                <li><strong>OpenAI Version ≥ 2.2.0:</strong> Required for web search capability</li>
                <li><strong>Responses API Available:</strong> Enables real-time web search for current enrollment data</li>
                <li><strong>IPEDS Enabled:</strong> Provides official historical enrollment baseline (2018-2022)</li>
                <li><strong>BLS Enabled:</strong> Provides official unemployment rates from Bureau of Labor Statistics</li>
                <li><strong>Web Search Enabled:</strong> Provides current enrollment estimates (2025-2026) and employment context</li>
            </ul>
            
            <p style="margin-top: 30px; padding: 20px; background: #edf2f7; border-left: 4px solid #4299e1; border-radius: 4px;">
                <strong>💡 Tip:</strong> If web search is disabled, run: <code>pip install --upgrade openai==2.2.0</code> and restart Flask.
            </p>
            
            <p style="text-align: center; margin-top: 30px; color: #718096;">
                <a href="/" style="color: #4299e1; text-decoration: none;">← Back to Main App</a>
            </p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/')
@group_required
def index():
    """Main page with file upload form"""
    print("=== INDEX ROUTE V4 - LOGIN NOW LOGS SESSION_START ===")
    # Validate that user info exists in session (for old sessions, force re-auth)
    user_info = session.get('user')
    if not user_info or not user_info.get('name') or not user_info.get('email') or \
       user_info.get('name') == 'Unknown' or user_info.get('name') == 'Unknown User':
        print(f"=== WARNING: Session has invalid user info ({user_info}), forcing re-authentication ===")
        session.clear()
        return redirect(url_for('login'))
    
    # Log session start on first access (whether from fresh login or existing auth)
    # Use timestamp to determine if this is a new session (handles browser close without explicit logout)
    SESSION_TIMEOUT_MINUTES = 30
    last_session_start = session.get('last_session_start')
    current_time = datetime.now()
    
    should_log_session_start = False
    if not last_session_start:
        print("=== NO PREVIOUS SESSION START TIMESTAMP - LOGGING NEW SESSION ===")
        should_log_session_start = True
    else:
        # Parse the timestamp and check if it's been more than SESSION_TIMEOUT_MINUTES
        try:
            last_start_time = datetime.fromisoformat(last_session_start)
            time_since_last_start = current_time - last_start_time
            print(f"=== LAST SESSION START: {last_start_time}, TIME ELAPSED: {time_since_last_start} ===")
            
            if time_since_last_start > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                print(f"=== SESSION TIMEOUT ({SESSION_TIMEOUT_MINUTES} min) EXCEEDED - LOGGING NEW SESSION ===")
                should_log_session_start = True
            else:
                print(f"=== WITHIN SESSION WINDOW ({SESSION_TIMEOUT_MINUTES} min) - SKIPPING SESSION START LOG ===")
        except (ValueError, TypeError) as e:
            print(f"=== ERROR PARSING SESSION TIMESTAMP: {e} - LOGGING NEW SESSION ===")
            should_log_session_start = True
    
    if should_log_session_start:
        print("=== ATTEMPTING TO LOG SESSION START ===")
        try:
            from services.data_source_factory import get_property_data_source
            access_token = azure_auth.get_sharepoint_token()
            app_token = azure_auth.get_app_only_token()
            print(f"=== ACCESS TOKEN ACQUIRED: {access_token is not None} ===")
            print(f"=== APP TOKEN ACQUIRED: {app_token is not None} ===")
            if access_token and app_token:
                db = get_property_data_source(access_token=access_token, app_only_token=app_token)
                # Generate new logical session ID for new session (timeout or first access)
                import uuid
                session['logical_session_id'] = str(uuid.uuid4())
                print(f"=== NEW SESSION (timeout/first access): Generated session ID: {session['logical_session_id']} ===")
                
                db.log_activity(
                    user_email=user_info.get('email'),
                    user_name=user_info.get('name'),
                    activity_type='Start Session',
                    application=get_application_name(),
                    environment=get_environment_name(),
                    session_id=session['logical_session_id']
                )
                session['last_session_start'] = current_time.isoformat()
                print(f"=== SESSION START LOGGED for {user_info.get('name')} at {current_time} ===")
            else:
                print("=== WARNING: No access/app token, cannot log session start ===")
        except Exception as e:
            print(f"=== ERROR: Failed to log session start: {str(e)} ===")
            import traceback
            traceback.print_exc()
    
    model_name = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    data_source = os.environ.get('PROPERTY_DATA_SOURCE', 'database')
    print(f"DEBUG: model_name={model_name}, data_source={data_source}")
    
    # Only restore saved form data if coming from "Analyze Another Property" button
    # This prevents auto-filling on fresh page loads/new sessions
    restore_data = request.args.get('restore') == '1'
    saved_data = None
    
    if restore_data:
        saved_data = session.get('last_analysis_data')
        if saved_data:
            print(f"=== RESTORING SAVED ANALYSIS DATA: Property {saved_data.get('property_name')} ===")
        else:
            print("=== RESTORE REQUESTED BUT NO SAVED DATA FOUND ===")
    else:
        # Clear saved data on fresh page load to avoid stale data
        if 'last_analysis_data' in session:
            print("=== CLEARING SAVED ANALYSIS DATA (fresh page load) ===")
            session.pop('last_analysis_data', None)
    
    return render_template('index.html', 
                         model_name=model_name, 
                         data_source=data_source,
                         saved_data=saved_data)

@app.route('/upload', methods=['POST'])
@group_required
def upload_files():
    """Handle file uploads and property information"""
    try:
        # Validate files
        if 'cash_forecast' not in request.files or \
           'gl_export' not in request.files or \
           'analysis_file' not in request.files:
            return jsonify({'error': 'All three files are required'}), 400
        
        cash_forecast = request.files['cash_forecast']
        gl_export = request.files['gl_export']
        analysis_file = request.files['analysis_file']
        
        # Validate property information
        property_name = request.form.get('property_name', '').strip()
        property_address = request.form.get('property_address', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        university = request.form.get('university', '').strip()
        
        if not all([property_name, property_address, zip_code, university]):
            return jsonify({'error': 'All property information fields are required'}), 400
        
        # Validate file selections
        if cash_forecast.filename == '' or gl_export.filename == '' or analysis_file.filename == '':
            return jsonify({'error': 'Please select all three files'}), 400
        
        # Validate file types
        if not all([allowed_file(cash_forecast.filename),
                   allowed_file(gl_export.filename),
                   allowed_file(analysis_file.filename)]):
            return jsonify({'error': 'Invalid file type. Allowed: xlsx, xls, csv, txt'}), 400
        
        # Create unique session ID for this analysis
        analysis_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], analysis_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # Save files
        cash_forecast_path = os.path.join(session_folder, secure_filename(cash_forecast.filename))
        gl_export_path = os.path.join(session_folder, secure_filename(gl_export.filename))
        analysis_file_path = os.path.join(session_folder, secure_filename(analysis_file.filename))
        
        cash_forecast.save(cash_forecast_path)
        gl_export.save(gl_export_path)
        analysis_file.save(analysis_file_path)
        
        # Store property info
        property_info = {
            'name': property_name,
            'address': property_address,
            'zip_code': zip_code,
            'university': university,
            'analysis_date': datetime.now().isoformat()
        }
        
        # Process files (placeholder for now)
        file_processor = FileProcessor()
        parsed_data = file_processor.process_files(
            cash_forecast_path,
            gl_export_path,
            analysis_file_path,
            property_info
        )
        
        # Run analysis (placeholder for now)
        analysis_engine = AnalysisEngine()
        analysis_results = analysis_engine.analyze(parsed_data, property_info)
        
        # Generate executive summary
        summary_generator = SummaryGenerator()
        executive_summary = summary_generator.generate_summary(
            analysis_results,
            property_info
        )
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'property': property_info,
            'summary': executive_summary
        })
        
    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/analysis/<analysis_id>')
@group_required
def view_analysis(analysis_id):
    """View detailed analysis results"""
    # TODO: Retrieve stored analysis results
    return render_template('analysis.html', analysis_id=analysis_id)

@app.route('/api/drill-down/<analysis_id>/<bullet_id>')
@group_required
def get_drill_down(analysis_id, bullet_id):
    """Get detailed information for a specific bullet point"""
    # TODO: Retrieve detailed drill-down data
    return jsonify({
        'bullet_id': bullet_id,
        'details': 'Detailed analysis will appear here'
    })

@app.route('/api/analyze', methods=['POST'])
@group_required
def analyze_files():
    """
    Process uploaded files and generate comprehensive recommendation
    Requires: cash_forecast (Excel), income_statement (PDF), balance_sheet (PDF)
    """
    try:
        # Check if we have saved files from a previous analysis
        saved_analysis = session.get('last_analysis_data')
        use_saved_files = request.form.get('use_saved_files') == 'true'
        
        print(f"=== ANALYZE FILES CALLED ===")
        print(f"=== use_saved_files flag: {use_saved_files} ===")
        print(f"=== saved_analysis exists: {saved_analysis is not None} ===")
        if saved_analysis:
            print(f"=== saved files: {saved_analysis.get('cash_forecast_filename')}, {saved_analysis.get('income_statement_filename')}, {saved_analysis.get('balance_sheet_filename')} ===")
        
        # Validate files - either new uploads or use saved files
        required_files = ['cash_forecast', 'income_statement', 'balance_sheet']
        
        # Check if user uploaded new files or if we should use saved ones
        files_uploaded = all(
            file_key in request.files and request.files[file_key].filename != '' and request.files[file_key].filename != 'dummy.txt'
            for file_key in required_files
        )
        
        print(f"=== files_uploaded: {files_uploaded} ===")
        print(f"=== File names in request: {[request.files[k].filename if k in request.files else 'N/A' for k in required_files]} ===")
        
        if not files_uploaded and not (use_saved_files and saved_analysis):
            print("=== ERROR: No files uploaded and no saved files available ===")
            return jsonify({'error': 'All three files are required'}), 400
        
        # Determine which files to use
        if files_uploaded and not use_saved_files:
            # New files uploaded
            print("=== USING NEW FILES ===")
            cash_forecast = request.files['cash_forecast']
            income_statement = request.files['income_statement']
            balance_sheet = request.files['balance_sheet']
            using_saved_files = False
        else:
            # Use saved files from previous analysis
            print("=== USING SAVED FILES FROM PREVIOUS ANALYSIS ===")
            if not saved_analysis:
                print("=== ERROR: No saved analysis data found ===")
                return jsonify({'error': 'No saved files available. Please upload files.'}), 400
            
            # Create dummy file objects with saved filenames for logging
            class SavedFile:
                def __init__(self, filename):
                    self.filename = filename
            
            cash_forecast = SavedFile(saved_analysis['cash_forecast_filename'])
            income_statement = SavedFile(saved_analysis['income_statement_filename'])
            balance_sheet = SavedFile(saved_analysis['balance_sheet_filename'])
            using_saved_files = True
        
        # Validate property information
        property_entity = request.form.get('property_name', '').strip()
        property_address = request.form.get('property_address', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        university = request.form.get('university', '').strip()
        client_risk = request.form.get('client_risk', '').strip()
        show_parameters = request.form.get('show_parameters', '0') == '1'  # Checkbox value
        
        if not all([property_entity, property_address, zip_code, university, client_risk]):
            return jsonify({'error': 'All property information fields are required'}), 400
        
        # Map client risk to reserve months (configurable via environment variables)
        risk_to_months = {
            'low': int(os.getenv('RISK_LOW_MONTHS', '2')),
            'medium': int(os.getenv('RISK_MEDIUM_MONTHS', '6')),
            'high': int(os.getenv('RISK_HIGH_MONTHS', '6'))
        }
        reserve_months = risk_to_months.get(client_risk.lower())
        if reserve_months is None:
            return jsonify({'error': 'Invalid client risk selection'}), 400
        
        # Map client risk to working capital target ratio (configurable via environment variables)
        risk_to_wc_target = {
            'low': float(os.getenv('RISK_LOW_WC_TARGET', '0.5')),
            'medium': float(os.getenv('RISK_MEDIUM_WC_TARGET', '0.75')),
            'high': float(os.getenv('RISK_HIGH_WC_TARGET', '1.0'))
        }
        wc_target_ratio = risk_to_wc_target.get(client_risk.lower(), 1.0)
        
        # Log risk selection (using both print and logger to ensure visibility)
        risk_log_msg = f"=== CLIENT RISK SELECTION: {client_risk.upper()} → Reserve Months: {reserve_months}, WC Target Ratio: {wc_target_ratio} ==="
        print(risk_log_msg)
        app.logger.info(risk_log_msg)
        
        # Capture filenames for logging
        uploaded_filenames = ', '.join([
            cash_forecast.filename,
            income_statement.filename,
            balance_sheet.filename
        ])
        
        # Validate file types (only if new files uploaded)
        if not using_saved_files:
            if not cash_forecast.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Cash forecast must be an Excel file (.xlsx or .xls)'}), 400
            
            if not income_statement.filename.endswith('.pdf') or not balance_sheet.filename.endswith('.pdf'):
                return jsonify({'error': 'Income statement and balance sheet must be PDF files'}), 400
        
        # Handle file paths
        if using_saved_files:
            # Use saved file paths from previous analysis
            cash_forecast_path = saved_analysis['cash_forecast_path']
            income_statement_path = saved_analysis['income_statement_path']
            balance_sheet_path = saved_analysis['balance_sheet_path']
            session_folder = saved_analysis['session_folder']
            print(f"=== REUSING FILES FROM SESSION FOLDER: {session_folder} ===")
        else:
            # Create unique session folder and save new files
            analysis_id = str(uuid.uuid4())
            session_folder = os.path.join(app.config['UPLOAD_FOLDER'], analysis_id)
            os.makedirs(session_folder, exist_ok=True)
            
            # Save files
            cash_forecast_path = os.path.join(session_folder, secure_filename(cash_forecast.filename))
            income_statement_path = os.path.join(session_folder, secure_filename(income_statement.filename))
            balance_sheet_path = os.path.join(session_folder, secure_filename(balance_sheet.filename))
            
            cash_forecast.save(cash_forecast_path)
            income_statement.save(income_statement_path)
            balance_sheet.save(balance_sheet_path)
        
        # Get property details from SharePoint
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
        db = get_property_data_source(access_token=access_token)
        db_property = db.get_property_info(property_entity)
        
        property_info = {
            'entity_number': property_entity,
            'name': db_property.get('property_name', property_entity),
            'address': db_property.get('address', property_address),
            'city': db_property.get('city', 'Unknown'),
            'state': db_property.get('state', 'Unknown'),
            'zip': db_property.get('zip_code', zip_code),
            'university': db_property.get('university', university),
            'analysis_date': datetime.now().isoformat(),
            'client_risk': client_risk,
            'reserve_months': reserve_months
        }
        
        # Process files and generate recommendation
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        file_processor = FileProcessor(openai_api_key=openai_api_key)
        result = file_processor.process_and_analyze(
            cash_forecast_path=cash_forecast_path,
            income_statement_path=income_statement_path,
            balance_sheet_path=balance_sheet_path,
            property_info=property_info,
            reserve_months=reserve_months,
            wc_target_ratio=wc_target_ratio,
            show_parameters=show_parameters
        )
        
        # Check if analysis failed due to data validation issues
        if not result.get('success'):
            error_msg = result.get('error', 'Analysis failed')
            validation_issues = result.get('validation_issues', [])
            
            # Log failed analysis with specific details
            try:
                user = get_user()
                app_token = azure_auth.get_app_only_token()
                db_log = get_property_data_source(access_token=access_token, app_only_token=app_token)
                db_log.log_activity(
                    user_email=user.get('email', 'unknown'),
                    user_name=user.get('name', 'Unknown User'),
                    activity_type='Failed Analysis',
                    property_name=property_info.get('name', property_entity),
                    file_names=uploaded_filenames,
                    application=get_application_name(),
                    environment=get_environment_name(),
                    session_id=get_session_id()
                )
                app.logger.info(f"✓ Logged failed analysis for {property_info.get('name', property_entity)}")
            except Exception as log_error:
                app.logger.error(f"Failed to log validation failure: {str(log_error)}")
            
            # Return detailed error information
            return jsonify({
                'error': error_msg,
                'validation_issues': validation_issues,
                'details': 'Failed to extract valid data from input files. Check that files are correct format and contain data.'
            }), 400
        
        # Generate Word document
        docx_filename = f"{property_entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        docx_path = os.path.join(session_folder, docx_filename)
        docx_available = False
        
        try:
            docx_generator = WordDocumentGenerator()
            docx_generator.generate_document(result['recommendation'], docx_path)
            # Store docx path in session for download
            session['last_docx_path'] = docx_path
            session['last_docx_filename'] = docx_filename
            docx_available = True
        except Exception as docx_error:
            app.logger.error(f"Word document generation failed: {str(docx_error)}")
            # Continue even if Word document fails
        
        # Log successful analysis
        try:
            user = get_user()
            app_token = azure_auth.get_app_only_token()
            db_log = get_property_data_source(access_token=access_token, app_only_token=app_token)
            
            # Extract recommendation details for Status columns
            recommendation = result.get('recommendation', {})
            decision = recommendation.get('decision', 'UNKNOWN')
            amount = recommendation.get('amount', 0)
            
            # Format decision for display (capitalize first letter of each word)
            status_display = decision.replace('_', ' ').title()
            
            # Format amount as currency with risk level
            risk_display = client_risk.title() if client_risk else 'Unknown'
            amount_display = f"${amount:,.2f}" if amount else "$0.00"
            status_reason_display = f"{risk_display} Risk Chosen - {amount_display}"
            
            db_log.log_activity(
                user_email=user.get('email', 'unknown'),
                user_name=user.get('name', 'Unknown User'),
                activity_type='Successful Analysis',
                property_name=property_info.get('name', property_entity),
                file_names=uploaded_filenames,
                application=get_application_name(),
                environment=get_environment_name(),
                session_id=get_session_id(),
                status=status_display,
                status_reason=status_reason_display
            )
        except Exception as log_error:
            app.logger.error(f"Failed to log successful analysis: {str(log_error)}")
        
        # Store form data in session for re-use when "Analyze Another Property" is clicked
        session['last_analysis_data'] = {
            'property_name': property_entity,
            'property_address': property_address,
            'zip_code': zip_code,
            'university': university,
            'client_risk': client_risk,
            'show_parameters': show_parameters,
            'cash_forecast_filename': cash_forecast.filename,
            'income_statement_filename': income_statement.filename,
            'balance_sheet_filename': balance_sheet.filename,
            'cash_forecast_path': cash_forecast_path,
            'income_statement_path': income_statement_path,
            'balance_sheet_path': balance_sheet_path,
            'session_folder': session_folder
        }
        
        # Render results page
        return render_template('results.html', 
                             recommendation=result['recommendation'],
                             docx_available=docx_available)
        
    except Exception as e:
        app.logger.error(f"Error in analysis: {str(e)}")
        
        # Log failed analysis (capture what we can)
        try:
            user = get_user()
            property_name = request.form.get('property_name', 'Unknown') if request.form else 'Unknown'
            
            # Try to get filenames if available
            file_names = 'Unknown'
            if 'cash_forecast' in request.files and 'income_statement' in request.files and 'balance_sheet' in request.files:
                file_names = ', '.join([
                    request.files['cash_forecast'].filename if request.files['cash_forecast'].filename else 'unknown',
                    request.files['income_statement'].filename if request.files['income_statement'].filename else 'unknown',
                    request.files['balance_sheet'].filename if request.files['balance_sheet'].filename else 'unknown'
                ])
            
            # Get access token and log activity
            access_token = azure_auth.get_sharepoint_token()
            app_token = azure_auth.get_app_only_token()
            from services.data_source_factory import get_property_data_source
            db = get_property_data_source(access_token=access_token, app_only_token=app_token)
            
            db.log_activity(
                user_email=user.get('email', 'unknown'),
                user_name=user.get('name', 'Unknown User'),
                activity_type='Failed Analysis',
                property_name=property_name,
                file_names=file_names,
                application=get_application_name(),
                environment=get_environment_name(),
                session_id=get_session_id()
            )
        except Exception as log_error:
            app.logger.error(f"Failed to log analysis failure: {str(log_error)}")
        
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/download-docx')
@group_required
def download_docx():
    """Download the generated Word document"""
    try:
        docx_path = session.get('last_docx_path')
        docx_filename = session.get('last_docx_filename', 'analysis.docx')
        
        if not docx_path or not os.path.exists(docx_path):
            return jsonify({'error': 'Word document file not found'}), 404
        
        return send_file(
            docx_path,
            as_attachment=True,
            download_name=docx_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        app.logger.error(f"Error downloading Word document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-db')
@group_required
def test_database():
    """Test database connection and query"""
    try:
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
        db = get_property_data_source(access_token=access_token)
        
        # Test connection
        if not db.test_connection():
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Try to list properties (will show first 5)
        properties = db.list_all_properties()[:5]
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'total_properties': len(properties),
            'sample_properties': properties
        })
        
    except Exception as e:
        app.logger.error(f"Database test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties')
@group_required
def get_properties():
    """Get list of all reportable properties for dropdown"""
    try:
        from services.data_source_factory import get_property_data_source
        print("=== ATTEMPTING TO GET SHAREPOINT TOKEN ===")
        access_token = azure_auth.get_sharepoint_token()
        print(f"=== SHAREPOINT TOKEN ACQUIRED: {bool(access_token)} ===")
        
        if not access_token:
            print("=== ERROR: NO SHAREPOINT TOKEN - USER NEEDS TO CONSENT ===")
            print(f"=== User: {session.get('user', {}).get('email')} ===")
            print(f"=== SharePoint consented: {session.get('sharepoint_consented', False)} ===")
            return jsonify({
                'error': 'SharePoint access not granted',
                'message': 'Please complete SharePoint authorization',
                'needs_consent': True,
                'consent_url': url_for('sharepoint_consent')
            }), 401
        
        # For reading properties, we only need user token (no app token needed)
        db = get_property_data_source(access_token=access_token)
        print("=== FETCHING PROPERTIES FROM SHAREPOINT ===")
        properties = db.list_all_properties()
        print(f"=== SUCCESSFULLY FETCHED {len(properties)} PROPERTIES ===")
        return jsonify(properties)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"=== ERROR FETCHING PROPERTIES: {str(e)} ===")
        print(f"=== TRACEBACK: {error_trace} ===")
        print(f"=== User: {session.get('user', {}).get('email')} ===")
        
        # Check if it's a permission error
        if 'Access denied' in str(e) or 'Forbidden' in str(e) or '403' in str(e):
            return jsonify({
                'error': 'SharePoint access denied',
                'message': 'You do not have permission to access the SharePoint list',
                'details': str(e)
            }), 403
            
        return jsonify({
            'error': 'Failed to load properties',
            'message': str(e),
            'trace': error_trace if app.debug else None
        }), 500

@app.route('/api/property/<entity_number>')
@group_required
def get_property_details(entity_number):
    """Get detailed property information by entity number"""
    try:
        print(f"=== FETCHING PROPERTY DETAILS FOR: {entity_number} ===")
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
        # For reading properties, we only need user token (no app token needed)
        db = get_property_data_source(access_token=access_token)
        property_info = db.get_property_info(str(entity_number))
        if property_info:
            print(f"=== PROPERTY INFO FOUND: {property_info} ===")
            return jsonify(property_info)
        else:
            print(f"=== PROPERTY NOT FOUND: {entity_number} ===")
            return jsonify({'error': 'Property not found'}), 404
    except Exception as e:
        print(f"=== ERROR FETCHING PROPERTY: {str(e)} ===")
        app.logger.error(f"Error fetching property details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug/auth')
@login_required
def debug_auth():
    """Debug route to check authentication and group membership"""
    from services.auth import check_group_membership
    
    authorized_group_id = os.environ.get('AUTHORIZED_GROUP_ID')
    user_groups = session.get('user_groups', [])
    is_authorized = check_group_membership()
    
    return jsonify({
        'user': session.get('user', {}),
        'authenticated': session.get('authenticated', False),
        'user_groups': user_groups,
        'user_groups_count': len(user_groups),
        'configured_group_id': authorized_group_id,
        'is_in_authorized_group': authorized_group_id in user_groups if authorized_group_id else None,
        'check_group_membership_result': is_authorized,
        'account': session.get('account', {})
    })

if __name__ == '__main__':
    # Use use_reloader=False to avoid file watcher issues on Windows
    # Or manually restart the app when making changes
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
