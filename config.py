import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta'
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('SQLALCHEMY_DATABASE_URI')
        or 'postgresql+psycopg2://biblioteca:biblioteca@localhost:5433/sistema_biblioteca'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'DELETE']

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('TEST_DATABASE_URL')
        or 'postgresql+psycopg2://biblioteca:biblioteca@localhost:5433/sistema_biblioteca_test'
    )
    WTF_CSRF_ENABLED = False  # Disable CSRF forms protection in tests for simplicity
    SERVER_NAME = 'localhost'
    PREFERRED_URL_SCHEME = 'http'
