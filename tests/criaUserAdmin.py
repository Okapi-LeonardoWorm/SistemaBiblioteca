import sqlite3
from flask_bcrypt import Bcrypt
from time import strftime

bcrypt = Bcrypt()

# Conectar ao banco de dados
conn = sqlite3.connect('instance/biblioteca.db')
cursor = conn.cursor()

# Desativar temporariamente as restrições de chave estrangeira
cursor.execute('PRAGMA foreign_keys = OFF')

# Criar o hash da senha
password = "badminton"
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

# Inserir o usuário admin
try:
    cursor.execute('''
        INSERT INTO users (id, username, password, usertype, creationdate, lastUpdateDt, createdBy, updatedBy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, "admin", hashed_password, "admin", strftime("%Y-%m-%d"), strftime("%Y-%m-%d"), 1, 1))

    conn.commit()
except Exception as e:
    print(f"Erro: {e}")

# Ativar novamente as restrições de chave estrangeira
cursor.execute('PRAGMA foreign_keys = ON')

# Fechar a conexão
conn.close()
