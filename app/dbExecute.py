from . import db
from sqlalchemy import text


def executeQuery(query, params=None):
    try:
        db.session.execute(text(query), params or {})
        db.session.commit()
    except Exception as e:
        print(f"\n{e}\n")
        db.session.rollback()
        return False
    return True
    

def addFromForm(newObj):
    try:
        db.session.add(newObj)
        db.session.commit()
        return newObj
    except Exception as e:
        print(f"\n{e}\n")
        db.session.rollback()
        return None

    """
        if type(newObj)==list:
            try:
                for obj in newObj:
                    db.session.add(obj)
            except Exception as e:
                print(f"\n{e}\n")
                db.session.rollback()
                return None
        db.session.commit()
        return True
    """