from app import db, login
from sqlalchemy import case, desc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import column_property
from sqlalchemy.ext.hybrid import hybrid_property
import datetime as dt
import re

from app.models.userphrase import UserPhrase
from app.models.finding import Finding

PHRASE_MINIMUM_JOBS = 100

class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase_text = db.Column(db.Text(), unique=True, nullable=False)
    slug = db.Column(db.String(256), index=True, unique=True, nullable=False)
    search_count = db.Column(db.Integer, default=1)
    findings = db.relationship('Finding')
    user_phrases = db.relationship('UserPhrase')
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    @hybrid_property
    def mean_salary(self):

        if self.findings:
            self._mean_salary = self.findings[-1].mean_salary
        else:
            self._mean_salary = None

        return self._mean_salary

    @mean_salary.expression
    def mean_salary(cls):
        return select([
                    func.sum(Finding.mean_salary)
                ]).where(Finding.phrase_id==cls.id).as_scalar()

    @hybrid_property
    def jobs_count(self):

        if self.findings:
            self._jobs_count = self.findings[-1].jobs_count
        else:
            self._jobs_count = None

        return self._jobs_count

    @jobs_count.expression
    def jobs_count(cls):
        return select([
                    func.sum(Finding.jobs_count)
                ]).where(Finding.phrase_id==cls.id).as_scalar()

    @hybrid_property
    def jobs_above_100k_count(self):

        if self.findings:
            self._jobs_above_100k_count = self.findings[-1].jobs_above_100k_count
        else:
            self._jobs_above_100k_count = None

        return self._jobs_above_100k_count

    @jobs_above_100k_count.expression
    def jobs_above_100k_count(cls):
        return select([
                    func.sum(Finding.jobs_above_100k_count)
                ]).where(Finding.phrase_id==cls.id).as_scalar()


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
        return Phrase.query.filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(desc(Phrase.mean_salary)) 

    @staticmethod
    def get_by_user(user):
        return Phrase.query.join(UserPhrase).filter(UserPhrase.user == user).filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(desc(Phrase.mean_salary)) 

    @staticmethod
    def get_last():
        return Phrase.query.filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(Phrase.updated_date.desc()).first()

    @staticmethod
    def add(phrase_text, user=None, document=None):

        regex_remove_special = r'[^\w\.\s\-]' # only letters, numbers, dash, period, whitespace
        regex_extra_period = r'(\.+)(\s|$)|(\s|$)(\.+)' # remove periods at beginning and end, and adjacent to whitespace
        regex_multiple_space = r'[\s]+' # trim multiple space
        regex_multiple_dash = r'[-]+' # trim multiple dash
        regex_multiple_space_or_dash = r'[-\s]+' # trim multiple space or dash
        
        phrase_text = re.sub(regex_multiple_dash, '-', re.sub(regex_multiple_space, ' ', re.sub(regex_extra_period, ' ', re.sub(regex_remove_special, '', phrase_text.lower())))).strip()

        phrase = None

        if len(phrase_text) > 0:

            phrase_in_db = Phrase.query.filter_by(phrase_text=phrase_text).first()

            if phrase_in_db:
                phrase = phrase_in_db
                phrase.search_count = phrase.search_count + 1

            else:

                slug = re.sub(regex_multiple_space_or_dash, '-', re.sub(regex_extra_period, ' ', re.sub(regex_remove_special, '', phrase_text.lower()).strip()))

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

            phrase_in_db = Phrase.query.filter_by(slug=phrase_slug).first()

            if phrase_in_db:
                phrase = phrase_in_db

            else:
                # 404 would be better
                phrase = None

        return phrase
        

