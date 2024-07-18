from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate.init_app(app, db)


with app.app_context():
    from . import models
    from . import routes
    from . import forms
    
    # Cria as tabelas no banco de dados se elas não existirem ainda
    db.create_all()
