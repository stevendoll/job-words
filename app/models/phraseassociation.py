from app import app, db
from sqlalchemy.sql import func
import datetime as dt


class PhraseAssociation(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    phrase_id = db.Column(db.Integer, db.ForeignKey("phrase.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    phraseset_id = db.Column(db.Integer, db.ForeignKey("phraseset.id"))
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    phrase = db.relationship("Phrase")
    user = db.relationship("User")
    phraseset = db.relationship("PhraseSet")
    document = db.relationship("Document")
    cluster = db.relationship("Cluster")
    comparison = db.relationship("Comparison")

    def serialize(self):
        result = {}
        result["documentTitle"] = self.document.title if self.document else None
        result["username"] = self.user.username if self.user else None
        result["phraseText"] = self.phrase.phrase_text
        result["searchCount"] = self.phrase.search_count
        result["createdDate"] = (
            self.phrase.created_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            if isinstance(self.phrase.created_date, dt.date)
            else None
        )
        result["updatedDate"] = (
            self.phrase.updated_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            if isinstance(self.phrase.updated_date, dt.date)
            else None
        )

        if self.phrase.findings:

            finding = self.phrase.findings[-1]

            result["meanSalary"] = finding.mean_salary
            result["sigmaSalary"] = finding.sigma_salary
            result["jobsCount"] = finding.jobs_count
            result["jobsOver100kCount"] = finding.jobs_above_50k_count

        else:

            result["meanSalary"] = None
            result["sigmaSalary"] = None
            result["jobsCount"] = None
            result["jobsOver100kCount"] = None

        return result

    def __repr__(self):
        return "<PhraseAssociation {}>".format(self.phrase)

    @staticmethod
    def get_all():
        return PhraseAssociation.query.all()