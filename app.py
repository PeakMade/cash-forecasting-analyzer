"""
Cash Forecast Analyzer - Main Flask Application
Analyzes student housing property cash forecasts and validates accountant recommendations
"""

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

from services.file_processor import FileProcessor
from services.analysis_engine import AnalysisEngine
from services.summary_generator import SummaryGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv', 'txt'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main page with file upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
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
def view_analysis(analysis_id):
    """View detailed analysis results"""
    # TODO: Retrieve stored analysis results
    return render_template('analysis.html', analysis_id=analysis_id)

@app.route('/api/drill-down/<analysis_id>/<bullet_id>')
def get_drill_down(analysis_id, bullet_id):
    """Get detailed information for a specific bullet point"""
    # TODO: Retrieve detailed drill-down data
    return jsonify({
        'bullet_id': bullet_id,
        'details': 'Detailed analysis will appear here'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Azure"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
