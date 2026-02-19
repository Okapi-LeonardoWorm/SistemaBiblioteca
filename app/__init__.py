from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import generate_csrf
from config import Config, TestingConfig



# Inicializando extensões fora do escopo da aplicação
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap5()


def createApp(config_name: str | None = None):
    # Cria o app
    app = Flask(__name__)
    # Carrega configuração conforme ambiente
    if config_name and config_name.lower() == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    CORS(app)
    
    login_manager.login_view = 'main.login'
    
    # Importa as rotas
    @login_manager.user_loader
    def load_user(userId):
        from app.models import User
        return User.query.get(int(userId))


    @app.context_processor
    def inject_globals():
        def _csrf_token():
            # In tests (or when CSRF is disabled), return empty string to avoid template errors
            if not app.config.get('WTF_CSRF_ENABLED', True):
                return ''
            try:
                return generate_csrf()
            except Exception:
                # Fallback: avoid breaking templates if CSRF generation fails
                return ''

        return dict(
            username=session.get('username'),
            userType=session.get('userType'),
            userId=session.get('userId'),
            csrf_token=_csrf_token)
    
    
    with app.app_context():
        from . import forms, models, routes
        from . import audit
        audit.register_listeners(app)
        from .routes import bp as main_bp
        app.register_blueprint(main_bp)
    return app

# Alias comum para compatibilidade com ferramentas/CLIs
create_app = createApp

