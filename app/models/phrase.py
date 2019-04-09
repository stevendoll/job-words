from app import app, db
from sqlalchemy import case, desc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import column_property, joinedload
from sqlalchemy.ext.hybrid import hybrid_property
import datetime as dt
import re
import math

from app.models import DocumentPhrase, ClusterPhrase, UserPhrase, Finding

from app.models.utils.schemas import PhraseSchema

PHRASE_MINIMUM_JOBS = 100


class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase_text = db.Column(db.Text(), nullable=False)
    slug = db.Column(db.String(256), index=True, unique=True, nullable=False)
    search_count = db.Column(db.Integer, default=1)
    findings = db.relationship("Finding", order_by="Finding.created_date")
    document_phrases = db.relationship("DocumentPhrase")
    cluster_phrases = db.relationship("ClusterPhrase")
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
        return (
            select([Finding.mean_salary])
            .where(Finding.phrase_id == cls.id)
            .order_by(desc(Finding.created_date))
            .limit(1)
            .as_scalar()
        )

    @hybrid_property
    def jobs_count(self):

        if self.findings:
            self._jobs_count = self.findings[-1].jobs_count
        else:
            self._jobs_count = None

        return self._jobs_count

    @jobs_count.expression
    def jobs_count(cls):
        return (
            select([Finding.jobs_count])
            .where(Finding.phrase_id == cls.id)
            .order_by(desc(Finding.created_date))
            .limit(1)
            .as_scalar()
        )

    @hybrid_property
    def jobs_above_100k_count(self):

        if self.findings:
            self._jobs_above_100k_count = self.findings[-1].jobs_above_100k_count
        else:
            self._jobs_above_100k_count = None

        return self._jobs_above_100k_count

    @jobs_above_100k_count.expression
    def jobs_above_100k_count(cls):
        return (
            select([Finding.jobs_above_100k_count])
            .where(Finding.phrase_id == cls.id)
            .order_by(desc(Finding.created_date))
            .limit(1)
            .as_scalar()
        )

    def serialize(self):

        return PhraseSchema().dump(self).data

    def __repr__(self):
        return "<Phrase {}>".format(self.phrase_text)

    @staticmethod
    def get_all(limit=100):

        return Phrase.query.options(joinedload(Phrase.findings)).filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(
            desc(Phrase.mean_salary)
        ).limit(limit=limit)

    @staticmethod
    def get_featured():

        q1 = Phrase.query.options(joinedload(Phrase.findings)).filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(
            desc(Phrase.mean_salary)
        ).limit(80)

        q2 = Phrase.query.options(joinedload(Phrase.findings)).filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS).order_by(
            desc(Phrase.updated_date)
        ).limit(20)

        return q1.union(q2)


    @staticmethod
    def get_serialized(phrases=[]):
        return PhraseSchema(many=True).dump(phrases).data

    @staticmethod
    def get_by_user(user):
        return (
            Phrase.query.join(UserPhrase)
            .filter(UserPhrase.user == user)
            .filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
            .order_by(desc(Phrase.mean_salary))
        )

    @staticmethod
    def get_last():
        return (
            Phrase.query.options(joinedload(Phrase.findings)).filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
            .order_by(Phrase.updated_date.desc())
            .first()
        )

    @staticmethod
    def add(phrase_text, user=None, document=None, comparison=None):

        regex_remove_special = (
            r"[^\w\.\s\-]"
        )  # only letters, numbers, dash, period, whitespace
        regex_extra_period = (
            r"(\.+)(\s|$)|(\s|$)(\.+)"
        )  # remove periods at beginning and end, and adjacent to whitespace
        regex_multiple_space = r"[\s]+"  # trim multiple space
        regex_multiple_dash = r"[-]+"  # trim multiple dash
        regex_multiple_space_or_dash = r"[-\s]+"  # trim multiple space or dash

        phrase_text = re.sub(
            regex_multiple_dash,
            "-",
            re.sub(
                regex_multiple_space,
                " ",
                re.sub(
                    regex_extra_period,
                    " ",
                    re.sub(regex_remove_special, "", phrase_text.lower()),
                ),
            ),
        ).strip()

        phrase = None

        if len(phrase_text) > 0:

            phrase_in_db = Phrase.query.filter_by(phrase_text=phrase_text).first()

            if phrase_in_db:
                phrase = phrase_in_db
                phrase.search_count = phrase.search_count + 1

            else:

                slug = re.sub(
                    regex_multiple_space_or_dash,
                    "-",
                    re.sub(
                        regex_extra_period,
                        " ",
                        re.sub(regex_remove_special, "", phrase_text.lower()).strip(),
                    ),
                )

                phrase = Phrase(phrase_text=phrase_text, slug=slug)
                db.session.add(phrase)

            if document:
                document_phrase = DocumentPhrase(phrase=phrase, document=document)
                db.session.add(document_phrase)

            elif user:
                user_phrase = UserPhrase(phrase=phrase, user=user)
                db.session.add(user_phrase)

            db.session.commit()

        return phrase

    @staticmethod
    def add_multiple(phrase_texts, user=None, document=None, comparison=None):

        for phrase_text in phrase_texts:

            flash_message = "Analyzing " + phrase_text
            app.logger.info(flash_message)

            # add phrase
            phrase = Phrase.add(phrase_text, user, document, comparison)

            # analyze
            Finding.analyze(phrase)

    @staticmethod
    def lookup(phrase_text, user=None, document=None, comparison=None):

        phrase = Phrase.add(
            phrase_text, user=user, document=document, comparison=comparison
        )

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
