"""
Smoke tests - Basic sanity checks that the application can start and core functionality works.
These tests should run quickly and catch fundamental issues like import errors, 
missing dependencies, or configuration problems.
"""
import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestApplicationStartup:
    """Test that the application can start without errors"""
    
    def test_app_imports_without_error(self):
        """Test that app.py can be imported without exceptions"""
        try:
            import app
            assert app is not None
        except Exception as e:
            pytest.fail(f"Failed to import app: {str(e)}")
    
    def test_flask_app_exists(self):
        """Test that Flask app object is created"""
        import app
        assert hasattr(app, 'app')
        assert app.app is not None
        from flask import Flask
        assert isinstance(app.app, Flask)
    
    def test_required_config_exists(self):
        """Test that required configuration values are present"""
        import app
        required_configs = ['SECRET_KEY', 'UPLOAD_FOLDER']
        for config in required_configs:
            assert config in app.app.config, f"Missing required config: {config}"
            assert app.app.config[config] is not None, f"Config {config} is None"


class TestCoreModules:
    """Test that core modules can be imported"""
    
    def test_services_import(self):
        """Test that services module exists and imports"""
        try:
            from services import auth
            from services import database
            from services import data_source_factory
            from services import file_processor
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import services: {str(e)}")
    
    @pytest.mark.skip(reason="AzureAuth class not currently in use")
    def test_azure_auth_import(self):
        """Test that Azure auth utilities can be imported"""
        try:
            from services.auth import AzureAuth
            assert AzureAuth is not None
        except Exception as e:
            pytest.fail(f"Failed to import AzureAuth: {str(e)}")


class TestEnvironmentConfiguration:
    """Test environment configuration and dependencies"""
    
    def test_required_packages_installed(self):
        """Test that critical packages are available"""
        required_packages = [
            'flask',
            'pandas',
            'openpyxl',
            'pypdf',
            'openai',
            'requests',
            'msal'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        assert len(missing_packages) == 0, f"Missing required packages: {', '.join(missing_packages)}"
    
    def test_upload_folder_exists(self):
        """Test that upload folder exists or can be created"""
        import app
        upload_folder = app.app.config.get('UPLOAD_FOLDER')
        assert upload_folder is not None
        
        # Check if it exists or create it
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
            except Exception as e:
                pytest.fail(f"Cannot create upload folder: {str(e)}")
        
        assert os.path.exists(upload_folder)
        assert os.path.isdir(upload_folder)


class TestRouteRegistration:
    """Test that routes are properly registered"""
    
    def test_main_routes_exist(self):
        """Test that expected routes are registered"""
        import app
        
        # Get all registered routes
        routes = [str(rule) for rule in app.app.url_map.iter_rules()]
        
        expected_routes = [
            '/',
            '/login',
            '/auth/callback',
            '/logout',
            '/session/start',
            '/api/properties',
            '/api/analyze'
        ]
        
        missing_routes = []
        for route in expected_routes:
            if route not in routes:
                missing_routes.append(route)
        
        assert len(missing_routes) == 0, f"Missing expected routes: {', '.join(missing_routes)}"
    
    def test_static_files_configured(self):
        """Test that static files are configured"""
        import app
        assert app.app.static_folder is not None
        assert os.path.exists(app.app.static_folder)


class TestUtilityFunctions:
    """Test utility functions work correctly"""
    
    def test_environment_detection(self):
        """Test that environment detection works"""
        import app
        result = app.is_local_environment()
        assert isinstance(result, bool)
    
    def test_application_name_generation(self):
        """Test that application name is generated correctly"""
        import app
        name = app.get_application_name()
        assert isinstance(name, str)
        assert len(name) > 0
        assert name == 'CashForecastAnalyzer'
    
    def test_allowed_file_validation(self):
        """Test file extension validation"""
        import app
        
        # Test valid extensions (xlsx, xls, csv, txt, pdf)
        assert app.allowed_file('test.xlsx') == True
        assert app.allowed_file('test.xls') == True
        assert app.allowed_file('test.pdf') == True
        assert app.allowed_file('test.csv') == True
        assert app.allowed_file('test.txt') == True
        
        # Test invalid extensions
        assert app.allowed_file('test.docx') == False
        assert app.allowed_file('test.pptx') == False
        assert app.allowed_file('test.exe') == False
        assert app.allowed_file('test') == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
