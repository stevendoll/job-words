from app import app, db
from app.models import User, Document, Phrase, PhraseAssociation, Finding

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Document': Document, 'Phrase': Phrase, 'PhraseAssociation': PhraseAssociation, 'Finding': Finding}

