from app import db, login
from sqlalchemy.sql import func

class UserDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    document = db.relationship('Document')
    user = db.relationship('User')

    def __repr__(self):
        return '<UserDocument {}>'.format(self.document.title)

    @staticmethod
    def get_all():
        return UserDocument.query.all()
