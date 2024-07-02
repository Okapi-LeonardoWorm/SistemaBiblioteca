import os

class Config:
    # Configuração para o caminho dos arquivos estáticos
    # STATIC_FOLDER = 'app/static'
    # STATIC_URL_PATH = 'app/static'

    # Configuração para o caminho dos templates
    # TEMPLATE_FOLDER = 'app/templates

    # Configuração para a chave secreta
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///biblioteca.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False