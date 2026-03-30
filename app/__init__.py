import warnings

from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import generate_csrf
from markupsafe import Markup, escape
from config import Config, TestingConfig
from flask_session import Session

try:
    from sqlalchemy.exc import LegacyAPIWarning
except Exception:
    LegacyAPIWarning = Warning


# Silence known third-party warnings to keep runtime/test output focused.
warnings.filterwarnings('ignore', message=r'.*datetime\.datetime\.utcnow\(\) is deprecated.*')
warnings.filterwarnings('ignore', category=LegacyAPIWarning, message=r'.*Query\.get\(\) method is considered legacy.*')
warnings.simplefilter('ignore', DeprecationWarning)
warnings.simplefilter('ignore', LegacyAPIWarning)



# Inicializando extensões fora do escopo da aplicação
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap5()
sess = Session()


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
    
    # Configurar Sessão do Servidor
    app.config['SESSION_SQLALCHEMY'] = db
    sess.init_app(app)

    login_manager.login_view = 'auth.login'
    
    
    # Importa as rotas
    @login_manager.user_loader
    def load_user(userId):
        from app.models import User
        return db.session.get(User, int(userId))


    @app.context_processor
    def inject_globals():
        def _render_user_identifier(user):
            if user is None:
                return ''
            identification = getattr(user, 'identificationCode', None) or getattr(user, 'username', '')
            identification_safe = escape(identification)
            if not bool(getattr(user, 'pcd', False)):
                return identification_safe

            return Markup(
                '<i class="fas fa-wheelchair me-1 text-primary" aria-label="Usuario PCD" title="Usuario PCD"></i>'
                f'{identification_safe}'
            )

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
            csrf_token=_csrf_token,
            render_user_identifier=_render_user_identifier)
    
    
    with app.app_context():
        from . import forms, models
        from . import audit
        from .routes import register_blueprints

        audit.register_listeners(app)
        register_blueprints(app)
    return app

# Alias comum para compatibilidade com ferramentas/CLIs
create_app = createApp

