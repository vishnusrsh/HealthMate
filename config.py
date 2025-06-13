import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Add other configuration variables here
    APP_NAME = "HealthMate AI"
    APP_DESCRIPTION = "Your AI-powered health assistant" 