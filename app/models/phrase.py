from app import db, login
from sqlalchemy.sql import func
from app.models.userphrase import UserPhrase

class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.Text(), index=True, unique=True)
    search_count = db.Column(db.Integer, default=1)
    # phrase_users = db.relationship('UserPhrase', backref='phrase', lazy='dynamic')
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return '<Phrase {}>'.format(self.phrase)

    @staticmethod
    def get_all():
        return Phrase.query.all()

    @staticmethod
    def lookup(search_phrase, user):

        this_phrase = None

        if len(search_phrase) > 0:

            phrase_in_db = db.session.query(Phrase).filter_by(phrase=search_phrase).first()

            if phrase_in_db:
                this_phrase = phrase_in_db
                this_phrase.search_count = this_phrase.search_count + 1

            else:
                this_phrase = Phrase(phrase=search_phrase)
                db.session.add(this_phrase)

            if user:
                this_user_phrase = UserPhrase(phrase=this_phrase, user=user)
                db.session.add(this_user_phrase)

            db.session.commit()


        return this_phrase

