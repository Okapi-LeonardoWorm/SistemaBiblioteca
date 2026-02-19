import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    # Essa configuração só deve ser usada quando o servidor for par nuvem e o app tenha um certificado SSL válido. Para desenvolvimento local, deixe como False.
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Server-Side Session Config
    SESSION_TYPE = 'sqlalchemy'
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'sess_'
    
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('SQLALCHEMY_DATABASE_URI')
        or 'postgresql+psycopg2://biblioteca:biblioteca@localhost:5439/sistema_biblioteca'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'DELETE']

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('TEST_DATABASE_URL')
        or 'postgresql+psycopg2://biblioteca:biblioteca@localhost:5439/sistema_biblioteca_test'
    )
    WTF_CSRF_ENABLED = False  # Disable CSRF forms protection in tests for simplicity
    SERVER_NAME = 'localhost'
    PREFERRED_URL_SCHEME = 'http'
