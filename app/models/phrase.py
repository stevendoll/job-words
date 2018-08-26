from app import db, login
from sqlalchemy.sql import func
from app.models.userphrase import UserPhrase
from app.models.finding import Finding
import datetime as dt
import re

class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase_text = db.Column(db.Text(), index=True, unique=True, nullable=False)
    slug = db.Column(db.String(64), index=True, unique=True, nullable=False)
    search_count = db.Column(db.Integer, default=1)
    findings = db.relationship('Finding')
    user_phrases = db.relationship('UserPhrase')
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def serialize(self):
        result = {}
        result['documentTitle'] = None
        result['username'] = None
        result['phraseText'] = self.phrase_text
        result['searchCount'] = self.search_count
        result['createdDate'] = self.created_date.strftime('%Y-%m-%dT%H:%M:%S.000Z') if isinstance(self.created_date, dt.date) else None
        result['updatedDate'] = self.updated_date.strftime('%Y-%m-%dT%H:%M:%S.000Z') if isinstance(self.updated_date, dt.date) else None

        if self.findings:

            finding = self.findings[-1]

            result['meanSalary'] = finding.mean_salary
            result['sigmaSalary'] = finding.sigma_salary
            result['jobsCount'] = finding.jobs_count
            result['jobsOver100kCount'] = finding.jobs_above_50k_count
            result['state'] = 'KS'

        else:

            result['meanSalary'] = None
            result['sigmaSalary'] = None
            result['jobsCount'] = None
            result['jobsOver100kCount'] = None
            result['state'] = None

        return result

    def __repr__(self):
        return '<Phrase {}>'.format(self.phrase_text)

    @staticmethod
    def get_all():
        return Phrase.query.all()

    @staticmethod
    def add(phrase_text, user=None, document=None):

        phrase = None

        if len(phrase_text) > 0:

            phrase_in_db = db.session.query(Phrase).filter_by(phrase_text=phrase_text).first()

            if phrase_in_db:
                phrase = phrase_in_db
                phrase.search_count = phrase.search_count + 1

            else:
                regex = r'[^a-zA-Z\s]'
                slug = re.sub(regex, '', phrase_text.lower().strip()).replace(' ', '-')

                phrase = Phrase(phrase_text=phrase_text, slug=slug)
                db.session.add(phrase)

            if user or document:
                user_phrase = UserPhrase(phrase=phrase, user=user, document=document)
                db.session.add(user_phrase)

            db.session.commit()

        return phrase

    @staticmethod
    def lookup(phrase_text, user=None, document=None):

        phrase = Phrase.add(phrase_text, user=user, document=document)

        # scrape indeed and analyze
        Finding.analyze(phrase)

        return phrase

    @staticmethod
    def get_phrase(phrase_slug):

        this_phrase = None

        if len(phrase_slug) > 0:

            phrase_in_db = db.session.query(Phrase).filter_by(slug=phrase_slug).first()

            if phrase_in_db:
                phrase = phrase_in_db

            else:
                # 404 would be better
                phrase = None

        return phrase
        

