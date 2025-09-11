import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///biblioteca.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'DELETE']

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF forms protection in tests for simplicity
