from flask import flash
from textblob import TextBlob, Word
from sqlalchemy.sql import func
import re
import uuid

from app import app, db, login
from app.models.userdocument import UserDocument
from app.models.finding import Finding
from app.models.phrase import Phrase

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(), nullable=False)
    slug = db.Column(db.String(64), index=True, unique=True, nullable=False)
    body = db.Column(db.Text())
    document_phrases = db.relationship('UserPhrase')
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    
    def analyze(self):
        
        user_document = db.session.query(UserDocument).filter_by(document=self).first()

        if user_document:
            user = user_document.user
        else:
            user = None

        for phrase in self.document_phrases:
            Phrase.lookup(phrase.phrase, user=user)
        

    def __repr__(self):
        return '<Document {}>'.format(self.title)

    @staticmethod
    def get_all():
        return Document.query.all()

    @staticmethod
    def add_document(title, body, user=None):
        
        regex = r'[^a-zA-Z\s\.-]'
        title = re.sub(regex, '', title.strip())
        slug = str(uuid.uuid4())[:8]

        document = Document(title=title, body=body, slug=slug)
        db.session.add(document)

        if user is not None:
            user_document = UserDocument(user=user, document=document)
            db.session.add(user_document)

        phrase_texts = TextBlob(body).noun_phrases

        app.logger.info(phrase_texts)

        for phrase_text in phrase_texts:

            flash_message = 'Analyzing ' + phrase_text
            app.logger.info(flash_message)

            # add phrase
            phrase = Phrase.add(phrase_text, user, document)

            # analyze
            Finding.analyze(phrase)


        db.session.commit()

        return document

    @staticmethod
    def get_by_slug(slug):

        this_document = None

        if len(slug) > 0:

            document_in_db = Document.query.filter_by(slug=slug).first()

        return document_in_db

    # @staticmethod
    # def get_document(search_document):

    #     this_document = None

    #     if len(search_document) > 0:

    #         document_in_db = db.session.query(Document).filter_by(document=search_document).first()

    #         if document_in_db:
    #             this_document = document_in_db

    #         else:
    #             # 404 would be better
    #             this_document = None

    #     return this_document
        

