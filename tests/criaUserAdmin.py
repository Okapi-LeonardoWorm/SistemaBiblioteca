import os
import sqlite3
from time import strftime

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
    # Encontrar o caminho do banco (preferir instance/biblioteca.db, senão biblioteca.db na raiz)
    db_path = 'instance/biblioteca.db'
    if not os.path.exists(db_path):
        db_path = 'biblioteca.db'

    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verifica se o usuário admin (id=1) existe usando identificationCode
    admin_row = cursor.execute(
        'SELECT 1 FROM users WHERE "userId" = 1 AND "identificationCode" = ?',
        ("admin",)
    ).fetchone()
    if admin_row:
        # Atualiza dados essenciais do admin, incluindo senha e userType
        try:
            cursor.execute(
                '''UPDATE users
                   SET password = ?, "userType" = ?, "lastUpdate" = ?, "birthDate" = ?, "userCompleteName" = ?
                 WHERE "userId" = 1''',
                (
                    hash_password("badminton"),
                    "admin",
                    strftime("%Y-%m-%d"),
                    '1998-07-06',
                    'Administrador'
                )
            )
            conn.commit()
        except Exception as e:
            print(f"Erro ao atualizar admin: {e}")
    else:
        # Criar o hash da senha e inserir o admin
        password = "badminton"
        hashed_password = hash_password(password)

        try:
            cursor.execute('''
                INSERT INTO users ("userId", "identificationCode", password, "userType", "creationDate", "lastUpdate", "createdBy", "updatedBy", "birthDate", "gradeNumber", "userCompleteName")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (1, "admin", hashed_password, "admin", strftime("%Y-%m-%d"), strftime("%Y-%m-%d"), None, None, '1998-07-06', None, 'Administrador'))

            conn.commit()
        except Exception as e:
            print(f"Erro: {e}")

    # Fechar a conexão
    conn.close()


if __name__ == "__main__":
    criaAdminUser()