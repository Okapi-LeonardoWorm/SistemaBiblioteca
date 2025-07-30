from app import app, db
from pandas import pandas as pd
from datetime import date
from random import randint

with app.app_context():
    import run
    from app.models import Book
    
    
    description = "Lorem ipsum odor amet, consectetuer adipiscing elit. Potenti tristique nisi dui et pellentesque laoreet condimentum diam. Efficitur porta ridiculus fusce dapibus; pretium sit torquent. Imperdiet sociosqu magna vitae; mattis consectetur nostra.\n Nascetur nec eget leo quis maximus hendrerit? Fames luctus et posuere maecenas velit scelerisque.\n Fringilla malesuada ornare ullamcorper sapien elementum habitasse vivamus massa. Hendrerit aliquet vulputate enim libero fermentum massa."


    books = pd.read_csv('tests/bookNames.csv', sep=';')
    names = books['livro']
    authors = books['autor']

    dates = pd.read_csv('tests/dates.csv', sep=';')
    dates = dates['datas']

    for i, bookYear in enumerate(dates):
        day = randint(1, 28)
        month = randint(1, 12)
        year = bookYear
        dates[i] = date(year, month, day)

    for book in range(0, len(names)):
        bookName = names[book]
        authorName = authors[book]
        amount = randint(1, 100)
        publisherName = f"publisher_{book}"
        publishedDate = dates[book]
        acquisitionDate = date.today()
        description = description

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
        db.session.add(new_book)

    db.session.commit()
