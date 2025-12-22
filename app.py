"""
Cash Forecast Analyzer - Main Flask Application
Analyzes student housing property cash forecasts and validates accountant recommendations
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
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

from services.file_processor import FileProcessor
from services.analysis_engine import AnalysisEngine
from services.summary_generator import SummaryGenerator
from services.docx_generator import WordDocumentGenerator
from services.auth import AzureADAuth, login_required, get_user

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
    
    # Store SharePoint token from initial login (both scopes requested at once)
    if 'access_token' in result:
        session['sharepoint_access_token'] = result['access_token']
        print(f"### SharePoint token stored from initial login (length: {len(result['access_token'])})")
    
    # Log user login activity
    try:
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
        if access_token:
            db = get_property_data_source(access_token=access_token)
            db.log_activity(
                user_email=session['user']['email'],
                user_name=session['user']['name'],
                activity_type='login'
            )
    except Exception as e:
        # Don't break login if logging fails
        print(f"=== WARNING: Failed to log login activity: {str(e)} ===")
    
    # Redirect directly to index - no second consent needed
    return redirect(url_for('index'))

@app.route('/auth/sharepoint-consent')
@login_required
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
    """Log out user and clear session"""
    # Log user logout activity before clearing session
    try:
        from services.data_source_factory import get_property_data_source
        user_email = session.get('user', {}).get('email', 'unknown')
        user_name = session.get('user', {}).get('name', 'unknown')
        access_token = azure_auth.get_sharepoint_token()
        if access_token:
            db = get_property_data_source(access_token=access_token)
            db.log_activity(
                user_email=user_email,
                user_name=user_name,
                activity_type='logout'
            )
    except Exception as e:
        # Don't break logout if logging fails
        print(f"=== WARNING: Failed to log logout activity: {str(e)} ===")
    
    session.clear()
    
    # Redirect to Azure AD logout to clear SSO session
    tenant_id = os.environ.get('AZURE_AD_TENANT_ID')
    logout_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout"
    
    # Add post_logout_redirect_uri to return to our app
    post_logout_redirect = request.host_url
    logout_url += f"?post_logout_redirect_uri={post_logout_redirect}"
    
    return redirect(logout_url)

@app.route('/')
@login_required
def index():
    """Main page with file upload form"""
    model_name = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    data_source = os.environ.get('PROPERTY_DATA_SOURCE', 'database')
    print(f"DEBUG: model_name={model_name}, data_source={data_source}")
    return render_template('index.html', model_name=model_name, data_source=data_source)

@app.route('/upload', methods=['POST'])
@login_required
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
@login_required
def view_analysis(analysis_id):
    """View detailed analysis results"""
    # TODO: Retrieve stored analysis results
    return render_template('analysis.html', analysis_id=analysis_id)

@app.route('/api/drill-down/<analysis_id>/<bullet_id>')
@login_required
def get_drill_down(analysis_id, bullet_id):
    """Get detailed information for a specific bullet point"""
    # TODO: Retrieve detailed drill-down data
    return jsonify({
        'bullet_id': bullet_id,
        'details': 'Detailed analysis will appear here'
    })

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze_files():
    """
    Process uploaded files and generate comprehensive recommendation
    Requires: cash_forecast (Excel), income_statement (PDF), balance_sheet (PDF)
    """
    try:
        # Validate files
        required_files = ['cash_forecast', 'income_statement', 'balance_sheet']
        for file_key in required_files:
            if file_key not in request.files:
                return jsonify({'error': f'{file_key} file is required'}), 400
            if request.files[file_key].filename == '':
                return jsonify({'error': f'Please select a {file_key} file'}), 400
        
        # Get files
        cash_forecast = request.files['cash_forecast']
        income_statement = request.files['income_statement']
        balance_sheet = request.files['balance_sheet']
        
        # Validate property information
        property_entity = request.form.get('property_name', '').strip()
        property_address = request.form.get('property_address', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        university = request.form.get('university', '').strip()
        
        if not all([property_entity, property_address, zip_code, university]):
            return jsonify({'error': 'All property information fields are required'}), 400
        
        # Validate file types
        if not cash_forecast.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Cash forecast must be an Excel file (.xlsx or .xls)'}), 400
        
        if not income_statement.filename.endswith('.pdf') or not balance_sheet.filename.endswith('.pdf'):
            return jsonify({'error': 'Income statement and balance sheet must be PDF files'}), 400
        
        # Create unique session folder
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
            'analysis_date': datetime.now().isoformat()
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
            property_info=property_info
        )
        
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Analysis failed')}), 500
        
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
        
        # Render results page
        return render_template('results.html', 
                             recommendation=result['recommendation'],
                             docx_available=docx_available)
        
    except Exception as e:
        app.logger.error(f"Error in analysis: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/download-docx')
@login_required
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

@app.route('/health')
def health_check():
    """Health check endpoint for Azure"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test-db')
@login_required
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
@login_required
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
@login_required
def get_property_details(entity_number):
    """Get detailed property information by entity number"""
    try:
        print(f"=== FETCHING PROPERTY DETAILS FOR: {entity_number} ===")
        from services.data_source_factory import get_property_data_source
        access_token = azure_auth.get_sharepoint_token()
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

if __name__ == '__main__':
    # Use use_reloader=False to avoid file watcher issues on Windows
    # Or manually restart the app when making changes
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
