from flask import flash
from textblob import TextBlob, Word
from sqlalchemy import case, desc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import column_property
import re
import uuid
from app import app, db
from app.models import PhraseAssociation, Phrase

PHRASE_MINIMUM_JOBS = 100


class PhraseSet(db.Model):
    __tablename__ = 'phraseset'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(), nullable=False)
    slug = db.Column(db.String(64), index=True, unique=True, nullable=False)
    type = db.Column(db.Text(), nullable=False, default='document')
    body = db.Column(db.Text())
    phrases = db.relationship("PhraseAssociation")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'phraseset'
    }

    @staticmethod
    def get_phrases(phraseset):
        return (
            Phrase.query.join(PhraseAssociation)
            .filter(PhraseAssociation.phraseset == phraseset)
            .filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
            .order_by(desc(Phrase.mean_salary))
            .all()
        )

class Document(PhraseSet):

    __mapper_args__ = {
        'polymorphic_identity':'document'
    }

    def __repr__(self):
        return "<Document {}>".format(self.title)

    @staticmethod
    def get_all():
        return Document.query.all()

    # @staticmethod
    # def get_phrases(document):
    #     return (
    #         Phrase.query.join(PhraseAssociation)
    #         .filter(PhraseAssociation.document == document)
    #         .filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
    #         .order_by(desc(Phrase.mean_salary))
    #         .all()
    #     )

    @staticmethod
    def add_document(title, body, user=None):

        regex = r"[^a-zA-Z\s\.-]"
        title = re.sub(regex, "", title.strip())
        slug = str(uuid.uuid4())[:8]

        document = Document(title=title, body=body, slug=slug, user=user)
        db.session.add(document)

        phrase_texts = TextBlob(body).noun_phrases

        app.logger.info(phrase_texts)

        Phrase.add_multiple(phrase_texts, user, document)

        db.session.commit()

        return document

    @staticmethod
    def get_by_slug(slug):

        this_document = None

        if len(slug) > 0:

            document_in_db = Document.query.filter_by(slug=slug).first()

        return document_in_db

class Cluster(PhraseSet):

    __mapper_args__ = {
        'polymorphic_identity':'cluster'
    }

    def __repr__(self):
        return "<Cluster {}>".format(self.title)

class Comparison(PhraseSet):

    __mapper_args__ = {
        'polymorphic_identity':'comparison'
    }

    def __repr__(self):
        return "<Comparison {}>".format(self.title)