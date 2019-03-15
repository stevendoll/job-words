from flask import flash
from textblob import TextBlob, Word
from sqlalchemy import case, desc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import column_property
import re
import uuid
from app import app, db
from app.models import UserPhrase, Phrase

PHRASE_MINIMUM_JOBS = 100


class PhraseGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(), nullable=False)
    type = db.Column(db.String(64), index=True, nullable=False, default='Document')
    slug = db.Column(db.String(64), index=True, unique=True, nullable=False)
    body = db.Column(db.Text())
    phrases = db.relationship("UserPhrase")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def analyze(self):

        for phrase in self.phrase_group_phrases:
            Phrase.lookup(phrase.phrase, user=self.user)

    def __repr__(self):
        return "<PhraseGroup {}>".format(self.title)

    @staticmethod
    def get_all():
        return PhraseGroup.query.all()

    @staticmethod
    def get_phrases(phrase_group):
        return (
            Phrase.query.join(UserPhrase)
            .filter(UserPhrase.phrase_group == phrase_group)
            .filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
            .order_by(desc(Phrase.mean_salary))
            .all()
        )

    @staticmethod
    def add_document(title, body, user=None):

        regex = r"[^a-zA-Z\s\.-]"
        title = re.sub(regex, "", title.strip())
        slug = str(uuid.uuid4())[:8]

        phrase_group = PhraseGroup(title=title, body=body, slug=slug, user=user, type='Document')
        db.session.add(phrase_group)

        phrase_texts = TextBlob(body).noun_phrases

        app.logger.info(phrase_texts)

        Phrase.add_multiple(phrase_texts, user, phrase_group)

        db.session.commit()

        return phrase_group

    @staticmethod
    def get_by_slug(slug):

        this_phrase_group = None

        if len(slug) > 0:

            phrase_group_in_db = PhraseGroup.query.filter_by(slug=slug).first()

        return phrase_group_in_db
