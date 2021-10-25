from src import db

class BaseModel(db.Model):
    __abstract__ = True

    inserted_date = db.Column(
        db.DateTime,
        default=db.func.now()
    )
    updated_date = db.Column(
        db.DateTime,
        onupdate=db.func.now()
    )