from multiprocessing import Pool
from time import strftime
from random import randint
from datetime import date, timedelta
import unicodedata
from app import createApp, db
from app.models import User, Book, KeyWord
from .criaUserAdmin import criaAdminUser

"""
Execute com: python -m tests.criaRegistrosTesteNoDb
"""

def hash_password(pw: str) -> str:
    try:
        from flask_bcrypt import Bcrypt  # type: ignore
        return Bcrypt().generate_password_hash(pw).decode('utf-8')
    except Exception:
        try:
            import bcrypt as _bcrypt  # type: ignore
            return _bcrypt.hashpw(pw.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
        except Exception:
            return pw  # fallback: texto puro

def _normalize_tag(token: str) -> str:
    if not token:
        return ''
    token = token.strip()
    nfkd = unicodedata.normalize('NFKD', token)
    ascii_only = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    up = ascii_only.upper()
    return ' '.join(up.split())

def insert_users(start, end):
    app = createApp()
    with app.app_context():
        users = []
        for i in range(start, end):
            username = f"user_{i}"
            password = f"passWord_{i}"
            hashed_password = hash_password(password)

            # birthDate obrigatório no modelo
            birth = date(2000, 1, 1) + timedelta(days=i % 365)

            # pular se já existe
            if db.session.query(User.userId).filter_by(identificationCode=username).first():
                continue

            new_user = User(
                username=username,  # synonym para identificationCode
                password=hashed_password,
                userType="visitor",
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=1,
                updatedBy=1,
                birthDate=birth,
                userCompleteName=f"User {i}",
            )
            users.append(new_user)

            if len(users) % 1000 == 0:
                db.session.bulk_save_objects(users)
                print(f"Users - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                users = []

        if users:
            db.session.bulk_save_objects(users)
            print(f"Users - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


def insert_books(start, end):
    app = createApp()
    with app.app_context():
        books = []
        for i in range(start, end):
            bookName = f"book_{i}"
            amount = randint(1, 100)
            authorName = f"author_{i}"
            publisherName = f"publisher_{i}"
            publishedDate = date.today()
            acquisitionDate = date.today()
            description = f"description_{i}"

            new_book = Book(
                bookName=bookName,
                amount=amount,
                authorName=authorName,
                publisherName=publisherName,
                publishedDate=publishedDate,
                acquisitionDate=acquisitionDate,
                description=description,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=1,
                updatedBy=1,
            )
            books.append(new_book)

            if len(books) % 100 == 0:
                db.session.bulk_save_objects(books)
                print(f"Books - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                books = []

        if books:
            db.session.bulk_save_objects(books)
            print(f"Books - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


def insert_keyWord(start, end):
    app = createApp()
    with app.app_context():
        words = []
        for i in range(start, end):
            word = _normalize_tag(f"word_{i}")

            # pular se já existe
            if db.session.query(KeyWord.wordId).filter_by(word=word).first():
                continue

            new_keyWord = KeyWord(
                word=word,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=1,
                updatedBy=1,
            )
            words.append(new_keyWord)

            if len(words) % 1000 == 0:
                db.session.bulk_save_objects(words)
                print(f"KeyWords - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                words = []

        if words:
            db.session.bulk_save_objects(words)
            print(f"KeyWords - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


if __name__ == "__main__":
    # Cria um usuário admin para poder inserir registros no banco de dados
    a = criaAdminUser()
    
    num_processes = 4  # Number of parallel processes
    BATCH_SIZE = 10
    TOTAL_USERS = 20
    TOTAL_KEYWORDS = 20
    TOTAL_BOOKS = 20

    def build_batches(total):
        batches = []
        start = 1
        while start <= total:
            end = min(start + BATCH_SIZE, total + 1)
            batches.append((start, end))
            start = end
        return batches

    user_batches = build_batches(TOTAL_USERS)
    book_batches = build_batches(TOTAL_BOOKS)
    keyWord_batches = build_batches(TOTAL_KEYWORDS)

    with Pool(num_processes) as pool:
        try:
            pool.starmap(insert_users, user_batches)
        except Exception as e:
            print(f"Erro ao inserir usuários: {e}")
        try:
            pool.starmap(insert_books, book_batches)
        except:
            pass
        try:
            pool.starmap(insert_keyWord, keyWord_batches)
        except Exception as e:
            print(f"Erro ao inserir keywords: {e}")

    print("Done!")

# run me with -> python -m tests.criaRegistrosTesteNoDb
