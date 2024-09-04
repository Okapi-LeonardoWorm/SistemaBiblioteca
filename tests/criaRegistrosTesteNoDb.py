from multiprocessing import Pool
from time import strftime
from random import randint
from datetime import date
from flask_bcrypt import Bcrypt
from app import app, db
from app.models import User, Book, KeyWord
from .criaUserAdmin import criaAdminUser
from time import sleep

# run me with -> python -m tests.criaRegistrosTesteNoDb

bcrypt = Bcrypt()

def insert_users(start, end):
    with app.app_context():
        users = []
        for i in range(start, end):
            username = f"user_{i}"
            password = f"passWord_{i}"
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            new_user = User(
                username=username,
                password=hashed_password,
                userType="regular",
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=1,
                updatedBy=1,
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
    with app.app_context():
        words = []
        for i in range(start, end):
            word = f"word_{i}"

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
    user_batches = [(i, i + 10) for i in range(1, 100, 10)]
    book_batches = [(i, i + 10) for i in range(1, 100, 10)]
    keyWord_batches = [(i, i + 10) for i in range(1, 100, 10)]

    with Pool(num_processes) as pool:
        try:
            pool.starmap(insert_users, user_batches)
        except:
            pass
        try:
            pool.starmap(insert_books, book_batches)
        except:
            pass
        try:
            pool.starmap(insert_keyWord, keyWord_batches)
        except:
            pass

    print("Done!")

# run me with -> python -m tests.criaRegistrosTesteNoDb
