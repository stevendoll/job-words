from app import db, login
from sqlalchemy.sql import func
from app.models.userdocument import UserDocument

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text())
    body = db.Column(db.Text())
    document_phrases = db.relationship('UserPhrase')
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return '<Document {}>'.format(self.document)

    @staticmethod
    def get_all():
        return Document.query.all()

    # @staticmethod
    # def lookup(search_document, user=None):

    #     this_document = None

    #     if len(search_document) > 0:

    #         document_in_db = db.session.query(Document).filter_by(document=search_document).first()

    #         if document_in_db:
    #             this_document = document_in_db
    #             this_document.search_count = this_document.search_count + 1

    #         else:
    #             this_document = Document(document=search_document)
    #             db.session.add(this_document)

    #         if user:
    #             this_user_document = UserDocument(document=this_document, user=user)
    #             db.session.add(this_user_document)

    #         # if not this_document.findings or this_document.findings.created_date.max() > '2018-01-01':
    #             # print('no findings')
    #         Finding.analyze(this_document)

    #         # if this_document.findings:
    #             # print('has findings')

    #         db.session.commit()


    #     return this_document

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
        

