from app import db, login
from sqlalchemy.sql import func

class UserPhrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'))
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    phrase = db.relationship('Phrase')
    user = db.relationship('User')

    def __repr__(self):
        return '<UserPhrase {}>'.format(self.phrase)

    @staticmethod
    def get_all():
        return UserPhrase.query.all()
