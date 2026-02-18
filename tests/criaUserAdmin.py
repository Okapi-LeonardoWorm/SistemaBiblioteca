from time import strftime
from datetime import date, datetime

from app import createApp, db
from app.models import User

# Usa Flask-Bcrypt se disponível; caso contrário, usa a lib bcrypt diretamente
def hash_password(pw: str) -> str:
    """Tenta usar Flask-Bcrypt, depois bcrypt; se indisponíveis, retorna a senha em texto puro."""
    try:
        from flask_bcrypt import Bcrypt  # type: ignore
        return Bcrypt().generate_password_hash(pw).decode('utf-8')
    except Exception:
        try:
            import bcrypt as _bcrypt  # type: ignore
            return _bcrypt.hashpw(pw.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
        except Exception:
            # Fallback: sem hash; compatível com o login do app (compara direto em fallback)
            return pw


def criaAdminUser():
    app = createApp()
    with app.app_context():
        admin = User.query.filter_by(identificationCode='admin').first()
        if admin:
            admin.password = hash_password('badminton')
            admin.userType = 'admin'
            admin.lastUpdate = datetime.now()
            admin.birthDate = date(1998, 7, 6)
            admin.userCompleteName = 'Administrador'
            if admin.updatedBy is None:
                admin.updatedBy = admin.userId
        else:
            admin = User(
                identificationCode='admin',
                password=hash_password('badminton'),
                userType='admin',
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=None,
                updatedBy=None,
                birthDate=date(1998, 7, 6),
                gradeNumber=None,
                userCompleteName='Administrador',
            )
            db.session.add(admin)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Erro ao criar/atualizar admin: {e}")
            db.session.rollback()


if __name__ == "__main__":
    criaAdminUser()