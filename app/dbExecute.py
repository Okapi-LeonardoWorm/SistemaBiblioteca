from . import db


def executeQuery(query, params=None):
    try:
        cursor = db.connection.cursor()
        cursor.execute(query, params)
        db.connection.commit()
        cursor.close()
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