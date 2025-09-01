from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5



# Inicializando extensões fora do escopo da aplicação
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap5()


def createApp():
    # Cria o app
    app = Flask(__name__)
    app.config.from_object('config.Config')

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
        return dict(
            username=session.get('username'),
            userType=session.get('userType'),
            userId=session.get('userId'))
    
    
    with app.app_context():
        from . import forms, models, routes
        from .routes import bp as main_bp
        app.register_blueprint(main_bp)
        # Cria as tabelas no banco de dados se elas não existirem
        db.create_all()
    return app

