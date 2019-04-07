from flask import flash
from textblob import TextBlob, Word
from sqlalchemy import case, desc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import column_property
import re
import uuid
from app import app, db
from app.models import ClusterPhrase, Phrase

PHRASE_MINIMUM_JOBS = 100


class Cluster(db.Model):
    __tablename__ = "cluster"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(), nullable=False)
    type = db.Column(db.Text(), nullable=False, default="Comparison")
    slug = db.Column(db.String(64), index=True, unique=True, nullable=False)
    body = db.Column(db.Text())
    phrases = db.relationship("ClusterPhrase")
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<Cluster {}>".format(self.title)

    @staticmethod
    def get_phrases(cluster):
        return (
            Phrase.query.join(ClusterPhrase)
            .filter(ClusterPhrase.cluster == cluster)
            .filter(Phrase.jobs_count > PHRASE_MINIMUM_JOBS)
            .order_by(desc(Phrase.mean_salary))
            .all()
        )

    @staticmethod
    def get_all():
        return Cluster.query.all()

    @staticmethod
    def add_cluster(title, body, user=None):

        regex = r"[^a-zA-Z\s\.-]"
        title = re.sub(regex, "", title.strip())
        slug = str(uuid.uuid4())[:8]

        cluster = Cluster(title=title, body=body, slug=slug)
        db.session.add(cluster)

        phrase_texts = TextBlob(body).noun_phrases

        app.logger.info(phrase_texts)

        Phrase.add_multiple(phrase_texts, user, cluster)

        db.session.commit()

        return cluster

    @staticmethod
    def get_by_slug(slug):

        this_cluster = None

        if len(slug) > 0:

            cluster_in_db = Cluster.query.filter_by(slug=slug).first()

        return cluster_in_db
