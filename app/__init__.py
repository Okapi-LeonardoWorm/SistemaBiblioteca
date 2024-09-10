from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



# Inicializando extensões fora do escopo da aplicação
app = Flask(__name__)
bcrypt = Bcrypt()
login_manager = LoginManager()

db = SQLAlchemy()
migrate = Migrate()

def createApp():
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    CORS(app)
    bcrypt = Bcrypt(app)


    with app.app_context():
        from . import forms, models, routes

        # Cria as tabelas no banco de dados se elas não existirem
        db.create_all()


    @app.context_processor
    def inject_globals():
        return dict(
            username=session.get('username'),
            userType=session.get('userType'),
            userId=session.get('userId'))


    @login_manager.user_loader
    def load_user(userId):
        from app.models import User
        
        return User.query.get(int(userId))
    
    
    return app

